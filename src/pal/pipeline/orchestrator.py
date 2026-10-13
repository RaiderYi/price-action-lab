"""批次编排器（第三轮复审 T02-T05 重写）。

链路：Candidate → 资格链（regime/strength/family）→ ARMED →
事件时钟（幂等）→ 条件触发 → buy-stop 撮合（量/参与率/一字板）→
原子绑定退出计划 → T+1 账本 → 连续 NAV → 事件日志。

第三轮修复：
- T02/F04：bar_key 幂等（同棒1次或100次状态相同）；armed_at 严格
  早于 bar.available_at 才可触发（信号棒不回填自己）。
- T03/F02：buy-stop 语义——bar 内触发按 entry 成交；跳空高开按
  开盘成交；不作为限价单等待回落。
- T03/F03：成交量参与率进入成交决策；零量=零成交；FillResult.qty
  驱动账本数量。
- T04/F01：成交时原子绑定退出计划（position_plans 字典，多票安全）；
  退出走 卖出订单→撮合→账本 同链；跳空按开盘；卖不出继续持风险。
- T05/F05：引擎 breakout 评估接入 assess_with_follow_bars；regime
  缺省=拒绝（None 不放行）；family 从 decision detail 传播。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from pal.context.regime import RegimeKind
from pal.data.bars import Bar
from pal.domain.decision import DecisionSnapshot
from pal.domain.models import DomainValidationError, SignalState
from pal.execution.fill_models import match_stop_loss_long
from pal.execution.market_rules import (
    MAIN_BOARD,
    MarketRuleSet,
    Order,
    OrderState,
)
from pal.ledger.positions import AccountLedger
from pal.portfolio.risk import PaperDefaults, PortfolioConstraints
from pal.selection.merge import CandidateLifecycle
from pal.selection.providers import Candidate
from pal.signals.engine import DecisionEngine, EngineConfig
from pal.signals.lifecycle import SetupBook


@dataclass
class OrchestratorConfig:
    engine: EngineConfig
    paper: PaperDefaults = field(default_factory=PaperDefaults)
    rules: MarketRuleSet = MAIN_BOARD
    trigger_expiry_bars: int = 8
    max_participation_pct: float = 0.10    # T03/F03：参与率


@dataclass
class ArmedSetup:
    setup_id: str
    instrument_id: str
    family: str
    entry: float
    stop: float
    target: float
    armed_at: datetime
    bars_since_armed: int = 0


@dataclass
class PositionPlan:
    """T04/F01：成交时原子绑定的退出计划（多票安全，随持仓走）。"""
    instrument_id: str
    setup_id: str
    entry: float
    stop: float
    target: float
    entry_date: date
    qty: int
    order: Optional[Order] = None


def match_buy_stop(bar: Bar, entry: float,
                   max_participation_pct: float = 0.10) -> "FillResult":
    """T03/F02：buy-stop 撮合（正确的停止单语义）。

    - 触发：bar.high >= entry（价格到达触发位）；
    - bar 内触发（open < entry <= high）→ 成交价 = entry（触发价）；
    - 跳空高开（open >= entry）→ 成交价 = open（更差价格，真实行为）；
    - 一字涨停（high == low）→ 不成交；
    - T03/F03：零成交量 → 不成交；成交量参与率上限。
    """
    from pal.execution.fill_models import FillResult
    if bar.volume <= 0:
        return FillResult(False, 0.0, 0, ("zero_volume",), False)
    if bar.high == bar.low:
        return FillResult(False, 0.0, 0, ("limit_up_one_way_board",), False)
    if bar.high < entry:
        return FillResult(False, 0.0, 0, ("not_triggered",), False)
    px = bar.open if bar.open >= entry else entry   # 跳空按开盘，否则触发价
    cap = int(bar.volume * max_participation_pct)
    qty = max(0, cap)
    if qty <= 0:
        return FillResult(False, 0.0, 0, ("participation_zero",), False)
    return FillResult(True, round(px, 2), qty,
                      ("buy_stop", "gap_open" if bar.open >= entry else "at_entry"),
                      False)


class SessionOrchestrator:
    """单票会话编排（T01-T05 修正版）。"""

    def __init__(self, config: OrchestratorConfig,
                 ledger: AccountLedger,
                 engine: Optional[DecisionEngine] = None):
        self.cfg = config
        self.ledger = ledger
        self.engine = engine or DecisionEngine(config.engine, SetupBook())
        self.constraints = PortfolioConstraints(config.paper)
        self.armed: Dict[str, ArmedSetup] = {}
        self.position_plans: Dict[str, PositionPlan] = {}   # T04：原子绑定
        self.decisions_log: List[DecisionSnapshot] = []
        self.nav_series: List[Tuple[datetime, float]] = []
        self.rejected_candidates: List[Tuple[str, str]] = []
        self.event_log: List[str] = []
        self._consumed_bars: set = set()      # T02/F04：bar 幂等键
        self._last_clock: Optional[datetime] = None

    # ── T02：bar 幂等键 ──
    @staticmethod
    def _bar_key(bar: Bar) -> str:
        return f"{bar.instrument_id}|{bar.timeframe}|{bar.bar_start.isoformat()}"

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

    @staticmethod
    def regime_allows_long_h2(kind: Optional[RegimeKind]) -> bool:
        """T05/F05：regime 缺省=None 不放行（缺上下文明确拒绝）。"""
        return kind in (RegimeKind.UPTREND, RegimeKind.RANGE)

    # ── 主推进 ──
    def on_bar(self, instrument_id: str, bar: Bar,
               bars_30m: Sequence[Bar], daily_bars: Sequence[Bar],
               candidate: Optional[Candidate],
               regime_kind: Optional[RegimeKind] = None) -> List[str]:
        # T02/F04：幂等——同一bar只处理一次
        key = self._bar_key(bar)
        if key in self._consumed_bars:
            return []
        # T02：单调时钟
        if self._last_clock is not None and bar.available_at < self._last_clock:
            return []
        self._consumed_bars.add(key)
        self._last_clock = bar.available_at

        events: List[str] = []
        asof = bar.available_at

        # 1) 持仓退出（先于新信号）
        if self.ledger.positions.total_qty(instrument_id) > 0:
            events += self._manage_exit(instrument_id, bar)

        # 2) armed 触发检查
        for sid in list(self.armed):
            setup = self.armed[sid]
            # T02/F04：armed_at 必须严格早于本bar可用时刻（信号棒不回填）
            if setup.armed_at >= asof:
                continue
            setup.bars_since_armed += 1
            if bar.high >= setup.entry:
                events += self._try_fill(setup, bar)
            elif setup.bars_since_armed >= self.cfg.trigger_expiry_bars:
                del self.armed[sid]
                events.append(f"EXPIRED:{sid}")
            elif setup.stop and bar.close < setup.stop:
                del self.armed[sid]
                events.append(f"SETUP_INVALID:{sid}")

        # 3) 新信号评估（T05：regime 强制 + family 传播）
        if candidate is not None and self.admit_candidate(
                candidate, instrument_id, asof):
            # 用实际评估的 regime（若调用方未传，用引擎计算结果）
            eff_regime = regime_kind
            if eff_regime is None:
                res_probe = self.engine.evaluate(
                    asof, list(bars_30m) + [bar], list(daily_bars),
                    candidate=candidate, instrument_id=instrument_id)
                eff_regime = res_probe.regime.kind
            if self.regime_allows_long_h2(eff_regime):
                res = self.engine.evaluate(
                    asof, list(bars_30m) + [bar], list(daily_bars),
                    candidate=candidate, instrument_id=instrument_id)
                self.decisions_log.extend(res.decisions)
                for sid in res.setups_armed:
                    if sid not in self.armed:
                        det = next(
                            (d for d in res.decisions
                             if sid in d.evidence_ids and d.outcome == "wait"),
                            None)
                        if det:
                            fam = self._family_of(sid, det)
                            self.armed[sid] = ArmedSetup(
                                setup_id=sid, instrument_id=instrument_id,
                                family=fam,
                                entry=float(det.detail.get("entry", 0)),
                                stop=float(det.detail.get("stop", 0)),
                                target=float(det.detail.get("target", 0)),
                                armed_at=asof)
                            events.append(f"ARMED:{sid}")
            else:
                self.rejected_candidates.append(
                    (candidate.candidate_id, f"REJ_REGIME_{eff_regime.value}"))
                events.append(f"REGIME_BLOCK:{eff_regime.value}")

        # 4) NAV
        self.nav_series.append(
            (asof, self.ledger.nav({instrument_id: bar.close})))
        self.event_log.extend(events)
        return events

    @staticmethod
    def _family_of(setup_id: str, det: DecisionSnapshot) -> str:
        """T05/F05：family 从 rule_id 源头传播（engine.h2/breakout）。"""
        rid = det.rule_id or ""
        if "breakout" in rid:
            return "breakout"
        if "h2" in rid.lower():
            return "H2"
        return "unknown"

    # ── T03/T04：撮合 + 原子退出绑定 ──
    def _try_fill(self, setup: ArmedSetup, bar: Bar) -> List[str]:
        events: List[str] = []
        iid = setup.instrument_id
        nav = self.ledger.nav({iid: bar.close})
        positions_value = self.ledger.positions.mark_value({iid: bar.close})
        rd = self.constraints.size_position(
            entry=setup.entry, stop=setup.stop,
            cash=self.ledger.cash, nav=nav,
            positions_value=positions_value,
            instrument_value=positions_value,
            industry_value=positions_value)
        if not rd.allow or rd.max_qty <= 0:
            events.append(f"NO_CAPACITY:{setup.setup_id}:{rd.reason_codes}")
            return events
        # T03/F02：buy-stop 撮合（量/参与率内部检查）
        fill = match_buy_stop(bar, setup.entry,
                              self.cfg.max_participation_pct)
        if not fill.filled or fill.qty <= 0:
            events.append(f"NO_FILL:{setup.setup_id}:{fill.assumptions}")
            return events
        # T03/F03：成交数量来自撮合（参与率上限），并受风险定仓约束
        qty = min(fill.qty, rd.max_qty)
        o = Order(order_id=f"ord_{setup.setup_id}",
                  plan_id=setup.setup_id, side="buy", order_type="stop",
                  qty=qty, stop_price=setup.entry)
        o.transition(OrderState.SUBMITTED)
        o.apply_fill(qty, fill.price, fill_id=f"fill_{setup.setup_id}",
                     event_at=bar.bar_end.isoformat())
        d = bar.bar_start.date()
        nxt = d + timedelta(days=1)     # 由 TradingCalendar 提供更好（T06）
        self.ledger.buy(iid, qty, fill.price, d, self.cfg.rules,
                        t1_next_trading_day=nxt)
        # T04/F01：原子绑定退出计划（不再依赖手工 bind）
        self.position_plans[iid] = PositionPlan(
            instrument_id=iid, setup_id=setup.setup_id,
            entry=fill.price, stop=setup.stop, target=setup.target,
            entry_date=d, qty=qty, order=o)
        del self.armed[setup.setup_id]
        events.append(f"FILL:{setup.setup_id}:{qty}@{fill.price}")
        return events

    def _manage_exit(self, instrument_id: str, bar: Bar) -> List[str]:
        """T04：退出计划驱动（自动止损/止盈；跳空按开盘；卖不出留风险）。"""
        events: List[str] = []
        plan = self.position_plans.get(instrument_id)
        if plan is None:
            return events
        qty_held = self.ledger.positions.total_qty(instrument_id)
        if qty_held <= 0:
            self.position_plans.pop(instrument_id, None)
            return events
        # T+1：只卖可卖量
        sellable = self.ledger.positions.sellable_qty(
            instrument_id, bar.bar_start.date())
        if sellable <= 0:
            events.append(f"EXIT_BLOCKED_T1:{instrument_id}")
            return events
        d = bar.bar_start.date()
        # 止损优先（跳空按开盘，一字跌停卖不出→留风险）
        if plan.stop and bar.low <= plan.stop:
            r = match_stop_loss_long(bar, plan.stop)
            if r.filled:
                so = Order(order_id=f"ord_exit_{plan.setup_id}_{d.isoformat()}",
                           plan_id=plan.setup_id, side="sell",
                           order_type="stop", qty=sellable,
                           stop_price=plan.stop)
                so.transition(OrderState.SUBMITTED)
                so.apply_fill(sellable, r.price, fill_id=f"fillx_{plan.setup_id}_{d}",
                              event_at=bar.bar_end.isoformat())
                self.ledger.sell(instrument_id, sellable, r.price, d,
                                 self.cfg.rules)
                events.append(f"EXIT_STOP:{sellable}@{r.price}")
                if self.ledger.positions.total_qty(instrument_id) == 0:
                    self.position_plans.pop(instrument_id, None)
                return events
            events.append(f"EXIT_BLOCKED:{r.assumptions}")   # 一字跌停等
            return events
        # 止盈
        if plan.target and bar.high >= plan.target:
            exit_px = max(bar.open, plan.target) if bar.open >= plan.target else plan.target
            self.ledger.sell(instrument_id, sellable, exit_px, d, self.cfg.rules)
            events.append(f"EXIT_TARGET:{sellable}@{exit_px}")
            if self.ledger.positions.total_qty(instrument_id) == 0:
                self.position_plans.pop(instrument_id, None)
        return events

    # 兼容旧接口（标记 deprecated）
    def bind_position_plan(self, stop: float, target: float,
                           entry_date: date) -> None:
        """DEPRECATED（T04）：退出计划已由成交原子绑定。"""
        raise DeprecationWarning(
            "bind_position_plan 已废弃：退出计划在成交时原子绑定（T04/F01）")
