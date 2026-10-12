"""批次编排器（R01/R02 修正）：端到端调用链。

链路：Candidate → DecisionEngine(evaluate) → 触发确认 → Order →
撮合(fill_models) → AccountLedger → 连续 NAV → DailyPlan 报告。

设计约束（复审 R01 修复要求）：
- 候选身份/时间/新鲜度校验（异票、未到期候选不得进入评估）；
- regime 真正作为资格门（downtrend 不放行 H2 多头）；
- 引擎确定性决策与事件写入分离（setup_id 内容寻址幂等承载，
  重复 evaluate 不重复发单）；
- TRIGGERED 与成交严格分开（fill 走撮合模型，触价≠成交）；
- 回放只按时钟投递数据，共用决策/价格/风险/撮合/账本（R02）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Tuple

from pal.context.regime import RegimeKind
from pal.data.bars import Bar
from pal.domain.decision import DecisionSnapshot
from pal.domain.models import DomainValidationError, SignalState
from pal.execution.fill_models import match_buy_limit, match_stop_loss_long
from pal.execution.market_rules import (
    MAIN_BOARD,
    MarketRuleSet,
    Order,
    OrderState,
)
from pal.ledger.positions import AccountLedger
from pal.portfolio.risk import PaperDefaults, PortfolioConstraints
from pal.pricing.structure_prices import price_h2_long
from pal.selection.merge import CandidateLifecycle
from pal.selection.providers import Candidate
from pal.signals.engine import DecisionEngine, EngineConfig
from pal.signals.lifecycle import SetupBook


@dataclass
class OrchestratorConfig:
    engine: EngineConfig
    paper: PaperDefaults = field(default_factory=PaperDefaults)
    rules: MarketRuleSet = MAIN_BOARD
    trigger_expiry_bars: int = 8       # armed 后未触发过期窗口


@dataclass
class ArmedSetup:
    """引擎产出、等待触发的结构计划（R01：TRIGGERED≠成交）。"""
    setup_id: str
    instrument_id: str
    family: str
    entry: float          # 触发价（buy-stop 语义：升破成交）
    stop: float
    target: float
    armed_at: datetime
    bars_since_armed: int = 0
    order: Optional[Order] = None


class SessionOrchestrator:
    """单票会话编排（批次 D 最小实现，多票组合由 PortfolioAllocator 承载）。"""

    def __init__(self, config: OrchestratorConfig,
                 ledger: AccountLedger,
                 engine: Optional[DecisionEngine] = None):
        self.cfg = config
        self.ledger = ledger
        self.engine = engine or DecisionEngine(config.engine, SetupBook())
        self.constraints = PortfolioConstraints(config.paper)
        self.armed: Dict[str, ArmedSetup] = {}
        self.decisions_log: List[DecisionSnapshot] = []
        self.nav_series: List[Tuple[datetime, float]] = []   # R02：连续净值
        self.rejected_candidates: List[Tuple[str, str]] = []

    # ── R01：候选门（身份/时间/新鲜度） ──
    def admit_candidate(self, cand: Candidate, instrument_id: str,
                        asof: datetime) -> bool:
        if cand.instrument_id != instrument_id:
            self.rejected_candidates.append(
                (cand.candidate_id, "INSTRUMENT_MISMATCH"))
            return False
        ok, why = CandidateLifecycle().validate_for_session(
            cand, session_open=asof, now=asof)
        if not ok:
            self.rejected_candidates.append((cand.candidate_id, why))
            return False
        return True

    # ── R01：regime 资格门 ──
    @staticmethod
    def regime_allows_long_h2(kind: RegimeKind) -> bool:
        return kind in (RegimeKind.UPTREND, RegimeKind.RANGE)

    # ── 主推进：一根新 bar 到达 ──
    def on_bar(self, instrument_id: str, bar: Bar,
               bars_30m: Sequence[Bar], daily_bars: Sequence[Bar],
               candidate: Optional[Candidate],
               regime_kind: Optional[RegimeKind] = None) -> List[str]:
        """处理一根完成bar：先管持仓退出，再评估新信号。

        返回本bar产生的事件描述（审计用）。
        events: ["EXIT:...", "ARMED:...", "TRIGGER:...", "FILL:...", ...]
        """
        events: List[str] = []
        asof = bar.available_at

        # 1) 持仓退出（退出优先于新信号）
        if self.ledger.positions.total_qty(instrument_id) > 0:
            events += self._manage_exit(instrument_id, bar)

        # 2) armed setup 的触发检查（R01：条件触发处理）
        for sid in list(self.armed):
            setup = self.armed[sid]
            setup.bars_since_armed += 1
            # 触发：升破 entry（buy-stop 语义）
            if bar.high >= setup.entry:
                events += self._try_fill(setup, bar)
            elif setup.bars_since_armed >= self.cfg.trigger_expiry_bars:
                del self.armed[sid]
                events.append(f"EXPIRED:{sid}")
            elif setup.stop and bar.close < setup.stop:
                # 结构失效先于触发
                del self.armed[sid]
                events.append(f"SETUP_INVALID:{sid}")

        # 3) 新信号评估（引擎确定性；setup 幂等防重复发单）
        if candidate is not None and self.admit_candidate(
                candidate, instrument_id, asof):
            if regime_kind is None or self.regime_allows_long_h2(regime_kind):
                res = self.engine.evaluate(
                    asof, list(bars_30m) + [bar], list(daily_bars),
                    candidate=candidate, instrument_id=instrument_id)
                self.decisions_log.extend(res.decisions)
                for sid in res.setups_armed:
                    if sid not in self.armed:      # 幂等：不重复武装
                        det = next(
                            (d for d in res.decisions
                             if sid in d.evidence_ids and d.outcome == "wait"),
                            None)
                        if det:
                            self.armed[sid] = ArmedSetup(
                                setup_id=sid, instrument_id=instrument_id,
                                family="H2",
                                entry=float(det.detail.get("entry", 0)),
                                stop=float(det.detail.get("stop", 0)),
                                target=float(det.detail.get("target", 0)),
                                armed_at=asof)
                            events.append(f"ARMED:{sid}")
            else:
                self.rejected_candidates.append(
                    (candidate.candidate_id, f"REJ_REGIME_{regime_kind.value}"))
                events.append(f"REGIME_BLOCK:{regime_kind.value}")

        # 4) NAV 记录（R02：连续净值）
        self.nav_series.append(
            (asof, self.ledger.nav({instrument_id: bar.close})))
        return events

    # ── 撮合与账本（R02：共用 fill models + ledger） ──
    def _try_fill(self, setup: ArmedSetup, bar: Bar) -> List[str]:
        events: List[str] = []
        iid = setup.instrument_id
        # 风险定仓（R07 修正后的约束器）
        positions_value = self.ledger.positions.mark_value({iid: bar.close})
        instrument_value = positions_value
        rd = self.constraints.size_position(
            entry=setup.entry, stop=setup.stop,
            cash=self.ledger.cash,
            nav=self.ledger.nav({iid: bar.close}),
            positions_value=positions_value,
            instrument_value=instrument_value,
            industry_value=positions_value)
        if not rd.allow or rd.max_qty <= 0:
            events.append(f"NO_CAPACITY:{setup.setup_id}:{rd.reason_codes}")
            return events
        # 订单 + 限价撮合（触价≠成交：一字板/流动性由 fill model 判）
        o = Order(order_id=f"ord_{setup.setup_id}",
                  plan_id=setup.setup_id, side="buy", order_type="limit",
                  qty=rd.max_qty, limit_price=setup.entry)
        o.transition(OrderState.SUBMITTED)
        fill = match_buy_limit(bar, setup.entry)
        if fill.filled:
            o.apply_fill(rd.max_qty, fill.price,
                         fill_id=f"fill_{setup.setup_id}",
                         event_at=bar.bar_end.isoformat())
            d = bar.bar_start.date()
            # T+1：下一交易日（由调用方日历推进，此处用 bar_end+1day 近似）
            from datetime import timedelta
            nxt = bar.bar_end.date() + timedelta(days=1)
            self.ledger.buy(iid, rd.max_qty, fill.price, d,
                            self.cfg.rules, t1_next_trading_day=nxt)
            setup.order = o
            del self.armed[setup.setup_id]
            events.append(
                f"FILL:{setup.setup_id}:{rd.max_qty}@{fill.price}")
        else:
            events.append(f"NO_FILL:{setup.setup_id}:{fill.assumptions}")
        return events

    def _manage_exit(self, instrument_id: str, bar: Bar) -> List[str]:
        """持仓退出：止损走撮合模型（跳空按开盘，一字跌停风险延续）。"""
        events: List[str] = []
        qty = self.ledger.positions.total_qty(instrument_id)
        if qty <= 0:
            return events
        # 找最近一次买入 lot 的止损（简化：用 armed 记录外储——
        # 正式版由 ExitPolicyState 承载；此处以 plan 快照近似）
        stop = getattr(self, "_active_stop", None)
        target = getattr(self, "_active_target", None)
        d = bar.bar_start.date()
        if stop is not None and bar.available_at.date() > self._entry_date:
            r = match_stop_loss_long(bar, stop)
            if r.filled:
                self.ledger.sell(instrument_id, qty, r.price, d,
                                 self.cfg.rules)
                events.append(f"EXIT_STOP:{qty}@{r.price}")
                return events
        if target is not None and bar.available_at.date() > self._entry_date \
                and bar.high >= target:
            self.ledger.sell(instrument_id, qty, target, d, self.cfg.rules)
            events.append(f"EXIT_TARGET:{qty}@{target}")
        return events

    def bind_position_plan(self, stop: float, target: float,
                           entry_date: date) -> None:
        """成交后绑定退出计划（正式版走 ExitPolicyEngine）。"""
        self._active_stop = stop
        self._active_target = target
        self._entry_date = entry_date
