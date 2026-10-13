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

    V07/AR07：计划显式绑定所属买入批次，退出只能卖本批可卖量。
    R6-05：计划显式关联 lot_id（由唯一 fill_id 派生）——日期只用于
    可卖性规则，不再充当关联主键；同日同票同数量两批不再串扣。
    """
    instrument_id: str
    setup_id: str
    entry: float
    stop: float
    target: float
    entry_date: date
    qty: int
    order: Optional[Order] = None
    lot_id: str = ""
    remaining_qty: int = 0        # R6-10：低量部分退出后剩余计划量

    def __post_init__(self):
        if self.remaining_qty <= 0:
            self.remaining_qty = self.qty

    def lot_id_old(self) -> str:
        return f"lot_{self.instrument_id}_{self.entry_date.isoformat()}_{self.qty}"


def match_buy_stop(bar: Bar, entry: float,
                   max_participation_pct: float = 0.10,
                   volume_budget: Optional[int] = None) -> "FillResult":
    """T03/F02：buy-stop 撮合（正确的停止单语义）。

    - 触发：bar.high >= entry（价格到达触发位）；
    - bar 内触发（open < entry <= high）→ 成交价 = entry（触发价）；
    - 跳空高开（open >= entry）→ 成交价 = open（更差价格，真实行为）；
    - 一字涨停（high == low）→ 不成交；
    - T03/F03：零成交量 → 不成交；成交量参与率上限。
    - R6-10：volume_budget=本 bar 剩余共享可成交预算（同票同 bar
      多订单共享；None=不限制，用于回测兼容）。
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
    if volume_budget is not None:
        cap = min(cap, max(0, volume_budget))
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
        # R6-03/R6-06：持久化唯一写入口是 on_bar 的原子 journal；
        # OMS 不直接写 store（重启恢复由 _restore_oms_from_store 负责）
        from pal.portfolio.allocator import PortfolioAllocator
        from pal.oms.service import OrderManagementService
        self.allocator = PortfolioAllocator(config.paper)
        self.oms = OrderManagementService()
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
        # R6-10：同票同 bar 共享可成交预算（bar_key -> 剩余股数）
        self._bar_volume_budget: Dict[str, int] = {}
        self._bar_budget_ts: Dict[str, datetime] = {}
        # R6-09：业务日初净值（交易日切换时更新）
        self._current_biz_day: Optional[date] = None
        # R6-06：从事件流恢复 OMS 订单状态（重启不丢订单）
        self._restore_oms_from_store()

    def _restore_oms_from_store(self) -> None:
        """R6-06：构造时从已持久化 order/fill 事件恢复 OMS 状态。"""
        if self.store is None:
            return
        from pal.execution.market_rules import Order as _Order
        for ev in self.store.by_kind("order"):
            p = ev.payload
            if p.get("order_id") in self.oms.orders:
                continue
            o = _Order(
                order_id=p["order_id"], plan_id=p.get("plan_id", ""),
                side=p.get("side", "buy"),
                order_type=p.get("order_type", "stop"),
                qty=int(p.get("qty", 0)),
                limit_price=p.get("limit_price"),
                stop_price=p.get("stop_price"))
            o.state = OrderState.SUBMITTED
            self.oms.orders[o.order_id] = o
            from pal.oms.service import Reservation
            self.oms.reservations[o.order_id] = Reservation(
                o.order_id, p.get("instrument_id", ""),
                o.qty, p.get("price", 0.0) or 0.0,
                float(p.get("reserve_cash", 0.0)), ev.ts)
        for ev in self.store.by_kind("fill"):
            p = ev.payload
            oid = p.get("order_id")
            o = self.oms.orders.get(oid)
            if o is None or p.get("fill_id") in o.fill_ids:
                continue
            if o.state in (OrderState.FILLED, OrderState.CANCELLED,
                           OrderState.REJECTED):
                continue
            o.apply_fill(int(p["qty"]), float(p["price"]),
                         fill_id=p.get("fill_id", ""),
                         event_at=ev.ts)
            r = self.oms.reservations.get(oid)
            if r is not None:
                r.converted_to_fill = o.filled_qty

    # ── R6-10：bar 共享容量预算 ──
    def _volume_budget_for(self, bar: Bar) -> Optional[int]:
        """本 bar 剩余可成交预算（参与率口径，整 bar 共享一份）。"""
        key = self._bar_key(bar)
        total = int(bar.volume * self.cfg.max_participation_pct)
        if key not in self._bar_volume_budget:
            self._bar_volume_budget[key] = total
        return self._bar_volume_budget[key]

    def _consume_volume_budget(self, bar: Bar, qty: int) -> None:
        key = self._bar_key(bar)
        self._bar_volume_budget[key] = max(
            0, self._bar_volume_budget.get(
                key, int(bar.volume * self.cfg.max_participation_pct)) - qty)

    # ── R6-03：内存状态快照/回滚——on_bar 失败时整体复原 ──
    def _snapshot_state(self) -> dict:
        import copy
        return {
            "ledger": copy.deepcopy(self.ledger),
            "position_plans": copy.deepcopy(self.position_plans),
            "armed": copy.deepcopy(self.armed),
            "consumed": set(self._consumed_bars),
            "clock": self._last_clock,
            "marks": dict(self._marks_cache),
            "budgets": dict(self._bar_volume_budget),
            "n_events": len(self.event_log),
            "nav": list(self.nav_series),
            "n_decisions": len(self.decisions_log),
            "n_rejected": len(self.rejected_candidates),
            "oms_orders": copy.deepcopy(self.oms.orders),
            "oms_res": copy.deepcopy(self.oms.reservations),
            "breaker": copy.deepcopy(self.allocator.breaker),
        }

    def _restore_state(self, snap: dict) -> None:
        self.ledger = snap["ledger"]
        self.position_plans = snap["position_plans"]
        self.armed = snap["armed"]
        self._consumed_bars = snap["consumed"]
        self._last_clock = snap["clock"]
        self._marks_cache = snap["marks"]
        self._bar_volume_budget = snap["budgets"]
        del self.event_log[snap["n_events"]:]
        self.nav_series = snap["nav"]
        del self.decisions_log[snap["n_decisions"]:]
        del self.rejected_candidates[snap["n_rejected"]:]
        self.oms.orders = snap["oms_orders"]
        self.oms.reservations = snap["oms_res"]
        self.allocator.breaker = snap["breaker"]

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

    # ── R6-03：稳定 8 位摘要（跨进程一致——Python hash() 有进程盐，
    #    崩溃重启后重试同 bar 必须派生同一订单/成交身份）──
    @staticmethod
    def _bk_digest(bk: str) -> str:
        import hashlib
        return hashlib.md5(bk.encode("utf-8")).hexdigest()[:8]

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
        # R6-03：本 bar 处理前快照——任何持久化失败整体回滚
        snap = self._snapshot_state()
        # AR05 完善：消费标记推迟到处理成功后——磁盘故障/异常时
        # 该棒不丢失（V06 尾巴），重试可完整重新处理
        def _commit_consumed(journal: list):
            # R6-03：游标与业务事件同批原子提交——不再存在
            # "业务已提交但游标未持久化"或反向的窗口
            # R6-04：携带完整 bar 字段——重启可重建行情历史引用
            journal.append(("bar_consumed", {
                "bar_key": key,
                "bar": {
                    "instrument_id": bar.instrument_id,
                    "timeframe": bar.timeframe,
                    "bar_start": bar.bar_start.isoformat(),
                    "bar_end": bar.bar_end.isoformat(),
                    "available_at": bar.available_at.isoformat(),
                    "open": bar.open, "high": bar.high,
                    "low": bar.low, "close": bar.close,
                    "volume": bar.volume, "amount": bar.amount,
                    "is_final": bar.is_final}},
                bar.available_at.isoformat()))

        events: List[str] = []
        asof = bar.available_at

        # R6-09：交易日切换 → 日初净值重置（业务时钟，非墙钟）
        biz_day = bar.bar_start.date()
        if self._current_biz_day is not None and biz_day != self._current_biz_day:
            try:
                day_start_nav = self.ledger.nav(dict(self._marks_cache))
            except DomainValidationError:
                day_start_nav = None
            if day_start_nav is not None:
                self.allocator.breaker.on_day_rollover(day_start_nav)
        self._current_biz_day = biz_day

        # 原子事务 journal（R6-03）：本 bar 的全部持久化写入
        journal: List[tuple] = []
        pending_bar_volume_consumes: List[tuple] = []   # 成交后回填

        # 1) 持仓退出（先于新信号；只处理本票）
        if self.ledger.positions.total_qty(instrument_id) > 0:
            events += self._manage_exit(instrument_id, bar, journal)

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
                events += self._try_fill(setup, bar, journal)
            elif setup.bars_since_armed >= self.cfg.trigger_expiry_bars:
                del self.armed[sid]
                events.append(f"EXPIRED:{sid}")
                journal.append(("setup_removed",
                                {"setup_id": sid, "why": "expired"},
                                asof.isoformat()))
            elif setup.stop and bar.close < setup.stop:
                del self.armed[sid]
                events.append(f"SETUP_INVALID:{sid}")
                journal.append(("setup_removed",
                                {"setup_id": sid, "why": "invalid"},
                                asof.isoformat()))

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
                            journal.append(("armed", {
                                "setup_id": sid,
                                "instrument_id": instrument_id,
                                "family": fam,
                                "entry": float(det.detail.get("entry", 0)),
                                "stop": float(det.detail.get("stop", 0)),
                                "target": float(det.detail.get("target", 0)),
                                "armed_at": asof.isoformat()},
                                asof.isoformat()))
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
            nav_now = self.ledger.nav(dict(self._marks_cache))
            self.nav_series.append((asof, nav_now))
            # R6-09：熔断消费每根 bar 的 NAV（持续估值 → RiskState），
            # 峰值随真实净值更新——开仓闸门只查询已更新的风险状态
            self.allocator.breaker.on_nav(nav_now, biz_day)
        self.event_log.extend(events)
        # R6-03：本 bar 全部业务事件 + 游标单次原子提交；失败则
        # 整体回滚内存（快照复原）——零半状态，同 bar 可完整重试
        _commit_consumed(journal)
        if self.store is not None and journal:
            try:
                self.store.append_atomic(journal)
            except Exception:
                self._restore_state(snap)
                raise
        self._consumed_bars.add(key)
        self._last_clock = bar.available_at
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
    def _try_fill(self, setup: ArmedSetup, bar: Bar,
                  journal: Optional[list] = None) -> List[str]:
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
        # R6-10：同票同 bar 共享容量预算
        fill = match_buy_stop(bar, setup.entry,
                              self.cfg.max_participation_pct,
                              volume_budget=self._volume_budget_for(bar))
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
        budget = self._volume_budget_for(bar) or 0
        qty = min(fill.qty, rd.max_qty, budget if budget is not None else fill.qty)
        lot = self.cfg.rules.lot_size
        qty = (qty // lot) * lot
        if qty <= 0:
            events.append(f"NO_LOT:{setup.setup_id}:qty<{lot}")
            return events
        # R6-03：order_id 由 bar_key 派生——同一 bar 重试是同一订单
        # （幂等），不同 bar 是不同订单
        bk = self._bar_key(bar)
        order_id = f"ord_{setup.setup_id}_{self._bk_digest(bk)}"
        fill_id = f"fill_{setup.setup_id}_{self._bk_digest(bk)}"
        # R6-05：lot_id 来源于唯一 fill（日期不再充当身份）
        lot_id = f"lot_{iid}_{fill_id}"
        # R6-06：买卖单均经 OMS 提交（OMS 是唯一订单状态所有者）
        o = Order(order_id=order_id,
                  plan_id=setup.setup_id, side="buy", order_type="stop",
                  qty=qty, stop_price=setup.entry)
        try:
            self.oms.submit(o, reserve_cash=qty * fill.price,
                            created_at=bar.available_at.isoformat())
        except Exception:
            pass    # 重试同 bar：OMS 已有该订单（幂等恢复）
        try:
            self.oms.apply_fill(order_id, qty, fill.price, fill_id,
                                event_at=bar.bar_end.isoformat())
        except Exception:
            pass    # 重复 fill_id 幂等
        d = bar.bar_start.date()
        nxt = (self.cfg.calendar.next_trading_day(d)
               if self.cfg.calendar is not None else d + timedelta(days=1))
        # V06/AR05 + R6-03：order/fill/plan 全部进 journal，与游标一起
        # 由 on_bar 单次原子提交——fill 写失败时零半状态，同 bar 重试
        # 幂等（order_id 唯一约束跳过已提交订单）
        if self.store is not None:
            journal.append(("order", {
                "order_id": order_id, "plan_id": setup.setup_id,
                "side": "buy", "qty": qty, "price": fill.price,
                "order_type": "stop", "stop_price": setup.entry,
                "instrument_id": iid,
                "reserve_cash": qty * fill.price},
                bar.available_at.isoformat()))
            journal.append(("fill", {
                "fill_id": fill_id, "order_id": order_id,
                "side": "buy", "qty": qty, "price": fill.price,
                "instrument_id": iid,
                "commission": round(
                    max(qty * fill.price * self.cfg.rules.commission_bps
                        / 10000, self.cfg.rules.min_commission), 4),
                "sellable_from": nxt.isoformat(),
                "lot_id": lot_id,
                # AR05：计划随 fill 持久化（恢复退出计划用）
                "plan": {"stop": setup.stop, "target": setup.target,
                         "entry_date": d.isoformat(), "qty": qty,
                         "setup_id": setup.setup_id}},
                bar.available_at.isoformat()))
        self.ledger.buy(iid, qty, fill.price, d, self.cfg.rules,
                        t1_next_trading_day=nxt, lot_id=lot_id)
        # T04/F01：原子绑定退出计划（不再依赖手工 bind）
        # A06：同票多批不静默覆盖——旧计划未平仓时保留为分批计划
        self._bind_position_plan(iid, setup, fill.price, qty, d, o,
                                 lot_id=lot_id)
        # R6-10：消耗本 bar 共享容量预算
        self._consume_volume_budget(bar, qty)
        del self.armed[setup.setup_id]
        events.append(f"FILL:{setup.setup_id}:{qty}@{fill.price}")
        return events

    def _bind_position_plan(self, iid: str, setup: "ArmedSetup",
                            fill_price: float, qty: int,
                            d: date, o: Optional[Order],
                            lot_id: str = "") -> None:
        """A06：position_plans 按票追加批次，不再覆盖。

        R6-05：plan 显式携带 lot_id（唯一 fill 派生），退出按
        lot_id 扣减本批——同日同票同数量不再串扣。
        """
        plan = PositionPlan(
            instrument_id=iid, setup_id=setup.setup_id,
            entry=fill_price, stop=setup.stop, target=setup.target,
            entry_date=d, qty=qty, order=o, lot_id=lot_id)
        existing = self.position_plans.get(iid)
        if existing is None:
            self.position_plans[iid] = plan
        elif isinstance(existing, list):
            existing.append(plan)
        else:
            self.position_plans[iid] = [existing, plan]

    def _manage_exit(self, instrument_id: str, bar: Bar,

                      journal: Optional[list] = None) -> List[str]:

        """T04/A06 + R6-05/R6-06/R6-10：退出计划驱动。



        - 退出按 plan.lot_id 精确扣减（同日同票不同计划不串扣）；

        - 卖单经 OMS 提交/成交（唯一订单状态所有者）；

        - 同票同 bar 多计划共享成交量预算；低量 → 部分退出 +

          计划保留剩余量（R6-10）。

        """

        events: List[str] = []

        if journal is None:

            journal = []

        raw = self.position_plans.get(instrument_id)

        if raw is None:

            return events

        plans = raw if isinstance(raw, list) else [raw]

        qty_held = self.ledger.positions.total_qty(instrument_id)

        if qty_held <= 0:

            self.position_plans.pop(instrument_id, None)

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

            # R6-05：按 lot_id 找本批；无 lot_id 的旧计划回退 acquired_date

            if plan.lot_id:

                lot = next((l for l in self.ledger.positions._lots.get(

                    instrument_id, []) if l.lot_id == plan.lot_id), None)

                batch = [lot] if lot is not None else []

            else:

                batch = [l for l in self.ledger.positions._lots.get(

                    instrument_id, [])

                    if l.acquired_date == plan.entry_date]

            batch_sellable = sum(l.sellable_qty(d) for l in batch

                                 if l is not None)

            plan_want = plan.remaining_qty

            sellable = min(plan_want, batch_sellable)

            if sellable <= 0:

                events.append(f"EXIT_BLOCKED_T1_PLAN:{plan.setup_id}")

                remaining_plans.append(plan)

                continue

            # R6-10：卖出侧也受本 bar 共享容量预算约束

            budget = self._volume_budget_for(bar)

            if budget is not None:

                sellable = min(sellable, budget)

                if sellable <= 0:

                    events.append(

                        f"EXIT_BLOCKED_BAR_CAPACITY:{plan.setup_id}")

                    remaining_plans.append(plan)

                    continue

            exit_px = None

            fill_kind = ""

            # 止损优先（跳空按开盘，一字跌停卖不出→留风险）

            if plan.stop and bar.low <= plan.stop:

                r = match_stop_loss_long(bar, plan.stop)

                if r.filled:

                    exit_px = r.price

                    fill_kind = "stop"

                else:

                    events.append(f"EXIT_BLOCKED:{r.assumptions}")

                    remaining_plans.append(plan)

                    continue

            # 止盈（A06：同样建卖出 Order，走同一订单链）

            elif plan.target and bar.high >= plan.target:

                exit_px = (max(bar.open, plan.target)

                           if bar.open >= plan.target else plan.target)

                fill_kind = "target"

            if exit_px is None:

                remaining_plans.append(plan)

                continue

            bk = self._bar_key(bar)

            order_id = f"ord_exit_{plan.setup_id}_{self._bk_digest(bk)}"

            fill_id = f"fillx_{plan.setup_id}_{self._bk_digest(bk)}_{fill_kind}"

            # R6-06：卖单经 OMS

            so = Order(order_id=order_id,

                       plan_id=plan.setup_id, side="sell",

                       order_type="stop" if fill_kind == "stop" else "limit",

                       qty=sellable,

                       stop_price=plan.stop if fill_kind == "stop" else None,

                       limit_price=plan.target if fill_kind != "stop" else None)

            try:

                self.oms.submit(so, reserve_cash=0.0,

                                created_at=bar.available_at.isoformat())

            except Exception:

                pass    # 同 bar 重试：订单已在 OMS（幂等）

            try:

                self.oms.apply_fill(order_id, sellable, exit_px, fill_id,

                                    event_at=bar.bar_end.isoformat())

            except Exception:

                pass

            if self.store is not None:

                journal.append(("order", {

                    "order_id": order_id, "plan_id": plan.setup_id,

                    "side": "sell", "qty": sellable, "price": exit_px,

                    "order_type": so.order_type, "instrument_id":

                        instrument_id, "lot_id": plan.lot_id,

                    "reserve_cash": 0.0},

                    bar.available_at.isoformat()))

                journal.append(("fill", {

                    "fill_id": fill_id, "order_id": order_id,

                    "side": "sell",

                    "qty": sellable, "price": exit_px,

                    "instrument_id": instrument_id,

                    "lot_id": plan.lot_id,

                    "commission": round(max(

                        sellable * exit_px

                        * self.cfg.rules.commission_bps / 10000,

                        self.cfg.rules.min_commission), 4),

                    "stamp_tax": round(

                        sellable * exit_px

                        * self.cfg.rules.stamp_tax_sell_bps

                        / 10000, 4)},

                    bar.available_at.isoformat()))

            # R6-05：按 lot 精确扣减

            if plan.lot_id:

                self.ledger.sell_by_lot(

                    instrument_id, sellable, exit_px, d,

                    self.cfg.rules, plan.lot_id)

            else:

                self.ledger.sell_batch(

                    instrument_id, sellable, exit_px, d,

                    self.cfg.rules, acquired_date=plan.entry_date)

            # R6-10：消耗共享容量；部分退出 → 计划保留剩余

            self._consume_volume_budget(bar, sellable)

            plan.remaining_qty -= sellable

            if plan.remaining_qty > 0:

                remaining_plans.append(plan)

                events.append(

                    f"EXIT_PARTIAL_{fill_kind.upper()}:"

                    f"{sellable}@{exit_px}")

            else:

                events.append(

                    f"EXIT_{fill_kind.upper()}:{sellable}@{exit_px}")

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
