"""历史回放（S5-07）与 legacy-vs-corrected 差异分解（S5-08）。

S5-07 红线：
- 最后bar正常处理（末尾不再无条件强平）；
- 期末未平仓→按收盘估值标记，不虚构成交；
- 超时退出走正常撮合。

S5-08：差异分解报告（规则修复/信号替换/价格模型/费用 各自贡献）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence

from pal.data.bars import Bar
from pal.domain.models import DomainValidationError
from pal.execution.market_rules import MarketRuleSet
from pal.ledger.positions import AccountLedger


@dataclass(frozen=True)
class ReplayTrade:
    instrument_id: str
    entry_date: date
    entry_price: float
    exit_date: Optional[date]
    exit_price: Optional[float]
    exit_reason: str          # "stop" | "target" | "timeout" | "open_eod_mark"
    qty: int


@dataclass
class ReplayResult:
    trades: List[ReplayTrade] = field(default_factory=list)
    open_positions_marked: List[ReplayTrade] = field(default_factory=list)
    n_bars_processed: int = 0
    final_nav: Optional[float] = None
    nav_series: List[float] = field(default_factory=list)


class SinglePositionReplayer:
    """单票单仓回放（S5-07：修 F08 尾bar bug 的正确实现）。

    与 legacy 差异（任务书 F08）：
    - legacy 循环 range(LOOKBACK, n-1) 跳过最后一根的持仓逻辑，末尾强平；
    - 本实现处理全部 bar；期末持仓→估值（open_positions_marked），
      不虚构成交、不绕过 T+1。
    """
    def __init__(self, rules: MarketRuleSet, stop_pct: float = 0.05,
                 target_pct: float = 0.10, timeout_bars: int = 20):
        self.rules = rules
        self.stop_pct = stop_pct
        self.target_pct = target_pct
        self.timeout_bars = timeout_bars

    def replay(self, instrument_id: str, bars: Sequence[Bar],
               entry_signal_idx: Sequence[int],
               initial_cash: float = 100_000.0) -> ReplayResult:
        if not bars:
            raise DomainValidationError("空序列")
        ordered = sorted(bars, key=lambda b: b.bar_start)
        led = AccountLedger(initial_cash)
        res = ReplayResult(n_bars_processed=len(ordered))
        entry_set = set(entry_signal_idx)
        open_trade: Optional[ReplayTrade] = None
        stop = target = 0.0
        entry_i = 0
        qty = 0

        for i, b in enumerate(ordered):
            td = b.bar_start.date()
            t1_next = date.max   # 简化：T+1 由 bar 序列自然推进（同日不再卖）
            if open_trade is None:
                if i in entry_set and i >= 1:
                    px = ordered[i].close
                    qty = int(initial_cash * 0.5 / px)
                    qty = qty - (qty % self.rules.lot_size)
                    if qty > 0:
                        # T+1 sellable：下一交易日（找下一个不同日期）
                        nxt = next((x.bar_start.date() for x in ordered[i+1:]
                                    if x.bar_start.date() > td), td)
                        led.buy(instrument_id, qty, px, td, self.rules,
                                t1_next_trading_day=nxt)
                        open_trade = ReplayTrade(
                            instrument_id, td, px, None, None, "open", qty)
                        entry_i = i
                        stop = px * (1 - self.stop_pct)
                        target = px * (1 + self.target_pct)
                continue

            # 持仓管理：只在可卖日（T+1）执行退出
            can_exit = b.bar_start.date() > open_trade.entry_date
            if can_exit:
                if b.low <= stop:
                    exit_px = min(b.open, stop)     # 跳空按开盘
                    if b.open <= stop and b.high == b.low:
                        continue    # 一字跌停卖不出，风险延续
                    led.sell(instrument_id, qty, exit_px, td, self.rules)
                    open_trade = ReplayTrade(
                        instrument_id, open_trade.entry_date,
                        open_trade.entry_price, td, exit_px, "stop", qty)
                    res.trades.append(open_trade)
                    open_trade = None
                    continue
                if b.high >= target:
                    exit_px = max(b.open, target) if b.open >= target else target
                    led.sell(instrument_id, qty, exit_px, td, self.rules)
                    res.trades.append(ReplayTrade(
                        instrument_id, open_trade.entry_date,
                        open_trade.entry_price, td, exit_px, "target", qty))
                    open_trade = None
                    continue
                if i - entry_i >= self.timeout_bars:
                    led.sell(instrument_id, qty, b.close, td, self.rules)
                    res.trades.append(ReplayTrade(
                        instrument_id, open_trade.entry_date,
                        open_trade.entry_price, td, b.close, "timeout", qty))
                    open_trade = None

        # 期末：未平仓 → 估值标记（不虚构成交）
        if open_trade is not None:
            last = ordered[-1]
            marked = ReplayTrade(
                instrument_id, open_trade.entry_date, open_trade.entry_price,
                last.bar_start.date(), last.close, "open_eod_mark", qty)
            res.open_positions_marked.append(marked)
        res.final_nav = led.nav({instrument_id: ordered[-1].close})
        return res


# ═══════════════════════════════════════════════════════════
# S5-08: legacy vs corrected 差异分解
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DiffAttribution:
    component: str      # "rule_fix" | "signal_swap" | "pricing_model" | "costs"
    legacy_value: float
    corrected_value: float
    contribution: float


def decompose_diff(legacy_total: float, rule_fix: float,
                   signal_swap: float, pricing_model: float,
                   costs: float) -> List[DiffAttribution]:
    """差异分解（S5-08）：分别报告各成分贡献，不把全部差异归于 regime。

    各成分为同口径增量收益（pp）；总额应≈Σ成分（校验在测试）。
    """
    out = [
        DiffAttribution("rule_fix", legacy_total, legacy_total + rule_fix, rule_fix),
        DiffAttribution("signal_swap", legacy_total, legacy_total + signal_swap, signal_swap),
        DiffAttribution("pricing_model", legacy_total, legacy_total + pricing_model, pricing_model),
        DiffAttribution("costs", legacy_total, legacy_total + costs, costs),
    ]
    return out
