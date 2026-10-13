"""第三轮复审 T09：backtest 与 paper 同一内核（BacktestRunner）。

复审验收：
- 回放只提供时点化数据 + 模拟执行适配，移除独立交易路径；
- 同一冻结事件流在历史/模拟实时模式下决策/订单/成交/账本一致；
- 最后一棒正常处理、未平仓估值、NAV 有写入路径；
- 差异归因来自真实对照运行。

设计：BacktestRunner 驱动 SessionOrchestrator（唯一业务内核），
按 available_at 顺序逐棒投递，mode 只影响时钟来源（历史=事件时间，
paper=墙钟），不复制交易逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Tuple

from pal.data.bars import Bar
from pal.ledger.positions import AccountLedger
from pal.pipeline.orchestrator import (
    OrchestratorConfig,
    SessionOrchestrator,
)
from pal.selection.providers import Candidate


@dataclass(frozen=True)
class BacktestDay:
    """一个交易日全部 30m bar + 可选候选 + 日线背景。"""
    trade_date: date
    bars_30m: Tuple[Bar, ...]
    daily_bars: Tuple[Bar, ...] = ()
    candidates: Tuple[Candidate, ...] = ()


@dataclass
class BacktestResult:
    nav_series: List[Tuple[datetime, float]] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    final_nav: Optional[float] = None
    final_cash: float = 0.0
    open_position_marks: Dict[str, Tuple[int, float]] = field(
        default_factory=dict)   # iid -> (qty, last_close)


class BacktestRunner:
    """历史回放 = 同一 SessionOrchestrator + 事件时间时钟（T09）。

    红线：
    - 不复制交易逻辑（撮合/T+1/退出全在 orchestrator）；
    - 最后一棒正常处理（orchestrator on_bar 本就逐棒），
      期末未平仓只按最后收盘估值（不虚构成交）；
    - NAV 序列由 runner 收集（每棒一条，orchestrator 幂等保证
      重复投递不产生重复 NAV）。
    """

    def __init__(self, config: OrchestratorConfig,
                 initial_cash: float):
        self.cfg = config
        self.initial_cash = initial_cash
        self.ledger = AccountLedger(initial_cash)
        self.orch = SessionOrchestrator(config, self.ledger)
        # V03/AR03：每票跨 run 历史窗口（分日增量 = 整段回放）
        self._history: Dict[str, List[Bar]] = {}

    def run(self, days: Sequence[BacktestDay]) -> BacktestResult:
        res = BacktestResult()
        if not days:
            return res
        # 只收集本次新增（多次 run 累积在 orchestrator 里，不重复抄回）
        nav_offset = len(self.orch.nav_series)
        # V03：历史窗口在实例上持久——逐日 run 与整段 run 结果一致
        history = self._history
        # N04：按 available_at 投递（因果时钟，非 bar_start）
        all_bars = [b for day in days for b in day.bars_30m]
        all_bars.sort(key=lambda b: (b.available_at, b.bar_start))
        day_by_date = {day.trade_date: day for day in days}
        for bar in all_bars:
            day = day_by_date.get(bar.bar_start.date())
            if day is None:
                continue
            cand = next(
                (c for c in day.candidates
                 if c.instrument_id == bar.instrument_id
                 and c.eligible_from <= bar.available_at),
                None)
            hist = history.get(bar.instrument_id, [])
            # 每票各自日线背景（多票日不过滤也安全：orchestrator
            # 只用 daily 的 regime，且 A04 异票防护已就位）
            day_daily = [b for b in day.daily_bars
                         if b.instrument_id == bar.instrument_id]
            ev = self.orch.on_bar(
                bar.instrument_id, bar,
                bars_30m=hist,
                daily_bars=day_daily,
                candidate=cand)
            # 只在成功处理后积累历史（on_bar 异常时不污染）
            history.setdefault(bar.instrument_id, []).append(bar)
            res.events.extend(ev)
        res.nav_series = list(self.orch.nav_series[nav_offset:])
        # 期末估值：各票取 available_at 最大的 bar 收盘（最后有效报价）
        marks: Dict[str, float] = {}
        for bar in all_bars:
            marks[bar.instrument_id] = bar.close
        held = {iid: q for iid, q in (
            (iid, self.ledger.positions.total_qty(iid))
            for iid in {b.instrument_id for d in days for b in d.bars_30m})
            if q > 0}
        res.open_position_marks = {
            iid: (q, marks[iid]) for iid, q in held.items()}
        res.final_cash = self.ledger.cash
        res.final_nav = self.ledger.nav(marks)
        return res
