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
from pal.data.calendar import TradingCalendar
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
from pal.pipeline.event_store import EventStore
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
    calendar: Optional[TradingCalendar] = None   # T06：正式路径必传


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
    """T04/F01：成交时原子绑定的退出计划（多票安全，随持仓走）。

    V07/AR07：计划显式绑定所属买入批次（lot_key=entry_date+setup_id），
    退出只能卖本批可卖量——新批不可卖(T+1)时计划保留，不串卖旧批。
    """
    instrument_id: str
    setup_id: str
    entry: float
    stop: float
    target: float
    entry_date: date
    qty: int
    order: Optional[Order] = None

    def lot_id(self) -> str:
        return f"lot_{self.instrument_id}_{self.entry_date.isoformat()}_{self.qty}"


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
                 engine: Optional[DecisionEngine] = None,
                 store: Optional["EventStore"] = None):
        self.cfg = config
        self.ledger = ledger
        self.engine = engine or DecisionEngine(config.engine, SetupBook())
        self.store = store       # N09：业务事件持久化（可选注入）
        if self.store is not None and len(store) == 0:
            # V05：仅全新仓库写 session_init——重启恢复不得把现金归零重置
            self.store.append("session_init",
                              {"initial_cash": ledger.initial_cash})
        self.constraints = PortfolioConstraints(config.paper)
        # AR08/AR09：组合分配器 + OMS 接入主链
        from pal.portfolio.allocator import PortfolioAllocator
        from pal.oms.service import OrderManagementService
        self.allocator = PortfolioAllocator(config.paper)
        self.oms = OrderManagementService(store)
        self.armed: Dict[str, ArmedSetup] = {}
        self.position_plans: Dict[str, PositionPlan] = {}   # T04：原子绑定
        self.decisions_log: List[DecisionSnapshot] = []
        self.nav_series: List[Tuple[datetime, float]] = []
        self.rejected_candidates: List[Tuple[str, str]] = []  # (instrument_id|candidate_id, reason)
        self.event_log: List[str] = []
        self._consumed_bars: set = set()      # T02/F04：bar 幂等键
        self._last_clock: Optional[datetime] = None
        self._marks_cache: Dict[str, float] = {}   # A04：全票最新收盘缓存
        self._industries: Dict[str, str] = {}      # AR08：行业映射（注入）

    def _industry_of(self, iid: str) -> str:
        return self._industries.get(iid, "unknown")

    def _trigger_regime_ok(self, instrument_id: str, asof: datetime,
                           daily_bars: Sequence[Bar]) -> bool:
        """AR10/A11：armed 触发前的环境重查。

        有当时可知的日线且判定 downtrend → 拒绝成交（环境变更生效）；
        无日线背景（如纯 30m 流）→ armed 产生时已过门，放行。
        """
        from pal.context.regime import RegimeKind, assess_trend_regime
        dailies = [b for b in daily_bars
                   if b.is_final
                   and b.instrument_id == instrument_id
                   and b.available_at <= asof]
        if not dailies:
            return True      # 无背景可查：不因缺数据冻结已武装计划
        kind = assess_trend_regime(dailies).kind
        return kind != RegimeKind.DOWNTREND

    # ── T02：bar 幂等键 ──
    @staticmethod
    def _bar_key(bar: Bar) -> str:
        return f"{bar.instrument_id}|{bar.timeframe}|{bar.bar_start.isoformat()}"

    def _require_next_trading_day(self, bar: Bar) -> None:
        """A08：交易必需的日历查询前置验证——失败零副作用可重试。"""
        if (self.cfg.calendar is not None
                and self.ledger.positions.total_qty(bar.instrument_id) == 0
                and any(s.instrument_id == bar.instrument_id
                        for s in self.armed.values())):
            d = bar.bar_start.date()
            self.cfg.calendar.next_trading_day(d)   # 仅验证，KeyError 时未标 consumed

    def admit_candidate(self, cand: Candidate, instrument_id: str,
                        asof: datetime) -> bool:
        if cand.instrument_id != instrument_id:
            self.rejected_candidates.append(
                (cand.instrument_id, "INSTRUMENT_MISMATCH"))
            return False
        ok, why = CandidateLifecycle().validate_for_session(
            cand, session_open=asof, now=asof)
        if not ok:
            self.rejected_candidates.append((cand.instrument_id, why))
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
        # A04：异票防护——bar 本体与 instrument_id 必须一致
        if bar.instrument_id != instrument_id:
            raise DomainValidationError(
                f"异票输入: 声明 {instrument_id} 实为 {bar.instrument_id}"
                f"（零副作用拒绝，不进入任何状态）")
        # A04：触发循环只处理本票 armed（不能按他票行情触发/过期）
        foreign_armed = [sid for sid, s in self.armed.items()
                         if s.instrument_id != instrument_id]
        # T02/F04：幂等——同一bar只处理一次
        key = self._bar_key(bar)
        if key in self._consumed_bars:
            return []
        # T02：单调时钟
        if self._last_clock is not None and bar.available_at < self._last_clock:
            return []
        # A08：先验证（不标 consumed）——校验失败零副作用可重试
        self._require_next_trading_day(bar)
        # AR05 完善：消费标记推迟到处理成功后——磁盘故障/异常时
        # 该棒不丢失（V06 尾巴），重试可完整重新处理
        def _commit_consumed():
            self._consumed_bars.add(key)
            self._last_clock = bar.available_at
            if self.store is not None:
                self.store.append("bar_consumed", {"bar_key": key},
                                  ts=bar.available_at.isoformat())

        events: List[str] = []
        asof = bar.available_at

        # 1) 持仓退出（先于新信号；只处理本票）
        if self.ledger.positions.total_qty(instrument_id) > 0:
            events += self._manage_exit(instrument_id, bar)

        # 2) armed 触发检查（A04：只触发本票 setup）
        for sid in list(self.armed):
            setup = self.armed[sid]
            if setup.instrument_id != instrument_id:
                continue      # A04：异票 setup 不因他票行情推进
            # T02/F04：armed_at 必须严格早于本bar可用时刻（信号棒不回填）
            if setup.armed_at >= asof:
                continue
            setup.bars_since_armed += 1
            # AR10/A11：触发前资格重查——环境变坏时已有 armed 不得开仓
            # （复审复现：DOWNTREND 时仍成交 8300@10.2）
            if bar.high >= setup.entry and self._trigger_regime_ok(
                    instrument_id, asof, daily_bars):
                events += self._try_fill(setup, bar)
            elif setup.bars_since_armed >= self.cfg.trigger_expiry_bars:
                del self.armed[sid]
                events.append(f"EXPIRED:{sid}")
            elif setup.stop and bar.close < setup.stop:
                del self.armed[sid]
                events.append(f"SETUP_INVALID:{sid}")

        # 3) 新信号评估（N02/A01：一次评估——先算 regime，再基于
        #    同一结果决定资格，不二次 evaluate 消耗 SetupBook 状态）
        if candidate is not None and self.admit_candidate(
                candidate, instrument_id, asof):
            eff_regime = regime_kind
            if eff_regime is None:
                # regime 只读行情背景，不推进 SetupBook。
                # V02/AR03：只看当时可知（available_at<=asof）且属于
                # 本票的 final 日线——未来/异票日线不得改变过去的门
                from pal.context.regime import assess_trend_regime
                dailies = [b for b in daily_bars
                           if b.is_final
                           and b.instrument_id == instrument_id
                           and b.available_at <= asof]
                if dailies:
                    eff_regime = assess_trend_regime(dailies).kind
                else:
                    eff_regime = RegimeKind.UNKNOWN
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
                    (candidate.instrument_id, f"REJ_REGIME_{eff_regime.value}"))
                events.append(f"REGIME_BLOCK:{eff_regime.value}")

        # 4) NAV（A04：全票 marks 缓存——他票行情推进时本票用最后已知价；
        #    缺持仓报价时显式降级跳过本条 NAV，不崩溃）
        self._marks_cache[instrument_id] = bar.close
        missing = [iid for iid, lots
                   in self.ledger.positions._lots.items()
                   if lots and iid not in self._marks_cache]
        if missing:
            events.append(f"NAV_DEGRADED_MISSING_MARK:{','.join(missing)}")
        else:
            self.nav_series.append(
                (asof, self.ledger.nav(dict(self._marks_cache))))
        self.event_log.extend(events)
        _commit_consumed()      # AR05：处理成功才标记消费
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

    # ── T03/T04/A05/A06：撮合 + 实际价风控 + 原子退出绑定 ──
    def _try_fill(self, setup: ArmedSetup, bar: Bar) -> List[str]:
        events: List[str] = []
        iid = setup.instrument_id
        # A05：先用保守价格上界（bar 开盘与触发价的较大者——跳空场景）
        # 重算定仓，再用实际成交价复核
        est_px = max(bar.open, setup.entry)
        marks = dict(self._marks_cache)
        marks[iid] = bar.close     # 本票最新价
        # AR08：账户级分配（allocator 扣已有持仓/行业/持仓数/熔断/在途）
        from pal.portfolio.allocator import AllocationRequest
        alloc_results = self.allocator.allocate(
            [AllocationRequest(iid, setup.setup_id, est_px, setup.stop,
                               setup.target, score=1.0,
                               industry=self._industry_of(iid))],
            self.ledger, marks,
            industry_of=self._industries or None)
        ar = alloc_results[0]
        if not ar.allow or ar.qty <= 0:
            events.append(
                f"NO_CAPACITY:{setup.setup_id}:{ar.reason_codes}")
            return events
        # 适配 RiskDecision 形状（下游用 rd.max_qty）
        from pal.portfolio.risk import RiskDecision
        rd = RiskDecision(True, ar.reason_codes, ar.qty,
                          0.0, 0.0, 0.0, self.ledger.cash)
        # T03/F02：buy-stop 撮合（量/参与率内部检查）
        fill = match_buy_stop(bar, setup.entry,
                              self.cfg.max_participation_pct)
        if not fill.filled or fill.qty <= 0:
            events.append(f"NO_FILL:{setup.setup_id}:{fill.assumptions}")
            return events
        # A05：实际成交价不得劣于定仓用的保守上界；劣于则按实际价缩量
        if fill.price > est_px:
            from pal.portfolio.allocator import AllocationRequest
            recheck = self.allocator.allocate(
                [AllocationRequest(iid, setup.setup_id, fill.price,
                                   setup.stop, setup.target, score=1.0,
                                   industry=self._industry_of(iid))],
                self.ledger, marks,
                industry_of=self._industries or None)[0]
            if not recheck.allow or recheck.qty <= 0:
                events.append(
                    f"FILL_REJECTED_RISK:{setup.setup_id}@{fill.price}")
                return events
            rd = RiskDecision(True, recheck.reason_codes, recheck.qty,
                              0.0, 0.0, 0.0, self.ledger.cash)
        # A06：lot 取整（MarketRuleSet.lot_size）——零股缩为合法申报量
        qty = min(fill.qty, rd.max_qty)
        lot = self.cfg.rules.lot_size
        qty = (qty // lot) * lot
        if qty <= 0:
            events.append(f"NO_LOT:{setup.setup_id}:qty<{lot}")
            return events
        o = Order(order_id=f"ord_{setup.setup_id}",
                  plan_id=setup.setup_id, side="buy", order_type="stop",
                  qty=qty, stop_price=setup.entry)
        o.transition(OrderState.SUBMITTED)
        o.apply_fill(qty, fill.price, fill_id=f"fill_{setup.setup_id}",
                     event_at=bar.bar_end.isoformat())
        d = bar.bar_start.date()
        nxt = (self.cfg.calendar.next_trading_day(d)
               if self.cfg.calendar is not None else d + timedelta(days=1))
        # V06/AR05：先持久化（write-ahead），成功后才改账本——
        # fill 写失败时零半状态（现金不变、持仓不变、可重试）
        if self.store is not None:
            self.store.append("order", {
                "order_id": o.order_id, "plan_id": setup.setup_id,
                "side": "buy", "qty": qty, "price": fill.price,
                "instrument_id": iid}, ts=bar.available_at.isoformat())
            self.store.append("fill", {
                "fill_id": f"fill_{setup.setup_id}", "order_id": o.order_id,
                "side": "buy", "qty": qty, "price": fill.price,
                "instrument_id": iid,
                "commission": round(
                    max(qty * fill.price * self.cfg.rules.commission_bps
                        / 10000, self.cfg.rules.min_commission), 4),
                "sellable_from": nxt.isoformat(),
                # AR05：计划随 fill 持久化（恢复退出计划用）
                "plan": {"stop": setup.stop, "target": setup.target,
                         "entry_date": d.isoformat(), "qty": qty,
                         "setup_id": setup.setup_id}},
                ts=bar.available_at.isoformat())
        self.ledger.buy(iid, qty, fill.price, d, self.cfg.rules,
                        t1_next_trading_day=nxt)
        # T04/F01：原子绑定退出计划（不再依赖手工 bind）
        # A06：同票多批不静默覆盖——旧计划未平仓时保留为分批计划
        self._bind_position_plan(iid, setup, fill.price, qty, d, o)
        del self.armed[setup.setup_id]
        events.append(f"FILL:{setup.setup_id}:{qty}@{fill.price}")
        return events

    def _bind_position_plan(self, iid: str, setup: "ArmedSetup",
                            fill_price: float, qty: int,
                            d: date, o: Optional[Order]) -> None:
        """A06：position_plans 按票追加批次，不再覆盖。"""
        plan = PositionPlan(
            instrument_id=iid, setup_id=setup.setup_id,
            entry=fill_price, stop=setup.stop, target=setup.target,
            entry_date=d, qty=qty, order=o)
        existing = self.position_plans.get(iid)
        if existing is None:
            self.position_plans[iid] = plan
        elif isinstance(existing, list):
            existing.append(plan)
        else:
            self.position_plans[iid] = [existing, plan]

    def _manage_exit(self, instrument_id: str, bar: Bar) -> List[str]:
        """T04/A06：退出计划驱动（多批计划；零量卖不出留风险）。"""
        events: List[str] = []
        raw = self.position_plans.get(instrument_id)
        if raw is None:
            return events
        plans = raw if isinstance(raw, list) else [raw]
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
        remaining_plans = []
        for plan in plans:
            if self.ledger.positions.total_qty(instrument_id) <= 0:
                remaining_plans.append(plan)
                continue
            # A06：卖出侧流动性检查（零量/一字跌停不能卖出）
            if bar.volume <= 0 or bar.high == bar.low:
                events.append(
                    f"EXIT_BLOCKED_NO_LIQUIDITY:{instrument_id}")
                remaining_plans.append(plan)
                continue
            # V07/AR07：本批可卖量 = min(本计划剩余量, 全票当日可卖)
            # ——新批 T+1 不可卖时本计划保留，绝不串卖旧批
            batch = [l for l in self.ledger.positions._lots.get(
                instrument_id, [])
                if l.acquired_date == plan.entry_date]
            batch_sellable = min(
                plan.qty,
                sum(l.sellable_qty(d) for l in batch))
            if batch_sellable <= 0:
                events.append(f"EXIT_BLOCKED_T1_PLAN:{plan.setup_id}")
                remaining_plans.append(plan)
                continue
            sellable = batch_sellable
            # 止损优先（跳空按开盘，一字跌停卖不出→留风险）
            if plan.stop and bar.low <= plan.stop:
                r = match_stop_loss_long(bar, plan.stop)
                if r.filled:
                    so = Order(order_id=f"ord_exit_{plan.setup_id}_{d.isoformat()}",
                               plan_id=plan.setup_id, side="sell",
                               order_type="stop", qty=sellable,
                               stop_price=plan.stop)
                    so.transition(OrderState.SUBMITTED)
                    so.apply_fill(sellable, r.price,
                                  fill_id=f"fillx_{plan.setup_id}_{d}",
                                  event_at=bar.bar_end.isoformat())
                    if self.store is not None:   # V06：先落盘
                        self.store.append("fill", {
                            "fill_id": f"fillx_{plan.setup_id}_{d}",
                            "order_id": so.order_id, "side": "sell",
                            "qty": sellable, "price": r.price,
                            "instrument_id": instrument_id,
                            "commission": round(max(
                                sellable * r.price
                                * self.cfg.rules.commission_bps / 10000,
                                self.cfg.rules.min_commission), 4),
                            "stamp_tax": round(
                                sellable * r.price
                                * self.cfg.rules.stamp_tax_sell_bps
                                / 10000, 4)},
                            ts=bar.available_at.isoformat())
                    self.ledger.sell_batch(instrument_id, sellable, r.price,
                                           d, self.cfg.rules,
                                           acquired_date=plan.entry_date)
                    events.append(f"EXIT_STOP:{sellable}@{r.price}")
                else:
                    events.append(f"EXIT_BLOCKED:{r.assumptions}")
                    remaining_plans.append(plan)
                continue
            # 止盈（A06：同样建卖出 Order，走同一订单链）
            if plan.target and bar.high >= plan.target:
                exit_px = (max(bar.open, plan.target)
                           if bar.open >= plan.target else plan.target)
                so = Order(order_id=f"ord_tp_{plan.setup_id}_{d.isoformat()}",
                           plan_id=plan.setup_id, side="sell",
                           order_type="limit", qty=sellable,
                           limit_price=plan.target)
                so.transition(OrderState.SUBMITTED)
                so.apply_fill(sellable, exit_px,
                              fill_id=f"filltp_{plan.setup_id}_{d}",
                              event_at=bar.bar_end.isoformat())
                if self.store is not None:   # V06：先落盘
                    self.store.append("fill", {
                        "fill_id": f"filltp_{plan.setup_id}_{d}",
                        "order_id": so.order_id, "side": "sell",
                        "qty": sellable, "price": exit_px,
                        "instrument_id": instrument_id,
                        "commission": round(max(
                            sellable * exit_px
                            * self.cfg.rules.commission_bps / 10000,
                            self.cfg.rules.min_commission), 4),
                        "stamp_tax": round(
                            sellable * exit_px
                            * self.cfg.rules.stamp_tax_sell_bps
                            / 10000, 4)},
                        ts=bar.available_at.isoformat())
                self.ledger.sell_batch(instrument_id, sellable, exit_px,
                                       d, self.cfg.rules,
                                       acquired_date=plan.entry_date)
                events.append(f"EXIT_TARGET:{sellable}@{exit_px}")
                continue
            # 无退出条件命中：计划保留
            remaining_plans.append(plan)
        if not remaining_plans:
            self.position_plans.pop(instrument_id, None)
        else:
            self.position_plans[instrument_id] = remaining_plans
        return events

    # 兼容旧接口（标记 deprecated）
    def bind_position_plan(self, stop: float, target: float,
                           entry_date: date) -> None:
        """DEPRECATED（T04）：退出计划已由成交原子绑定。"""
        raise DeprecationWarning(
            "bind_position_plan 已废弃：退出计划在成交时原子绑定（T04/F01）")
