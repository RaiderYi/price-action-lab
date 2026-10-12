"""撮合模型（S5-03）与涨跌停/流动性约束（S5-04）。

红线（任务书 §7 交易场景）：
- 多头止损遇开盘跳空低于 stop：按开盘价成交（更差），不填 stop 价；
- 触价≠成交；
- 一字板不保证成交（保守模型）；
- 同bar双触达给保守结果并标路径不确定；
- 成交量参与率上限。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pal.data.bars import Bar
from pal.domain.models import DomainValidationError
from pal.execution.market_rules import MarketRuleSet


@dataclass(frozen=True)
class FillResult:
    filled: bool
    price: float
    qty: int
    assumptions: tuple         # 撮合假设（可审计）
    path_uncertain: bool       # 同bar双触达等场景


def limit_up_price(prev_close: float, rules: MarketRuleSet,
                   is_st: bool = False) -> float:
    pct = rules.st_price_limit_pct if is_st else rules.price_limit_pct
    p = round(prev_close * (1 + pct), 2)
    return p


def limit_down_price(prev_close: float, rules: MarketRuleSet,
                     is_st: bool = False) -> float:
    pct = rules.st_price_limit_pct if is_st else rules.price_limit_pct
    return round(prev_close * (1 - pct), 2)


def match_buy_limit(bar: Bar, limit_price: float,
                    max_participation_pct: float = 0.1) -> FillResult:
    """限价买单撮合（保守）。

    可成交条件：bar.low <= limit_price（价格触达）且非一字涨停开盘。
    成交价：min(bar.open, limit_price)——开盘更低按开盘（对买方更优但
    保守按开盘成交反映可执行现实）。
    """
    if bar.low > limit_price:
        return FillResult(False, 0.0, 0, ("price_not_touched",), False)
    # 一字涨停：high==low==涨停 → 买不进（保守）
    if bar.high == bar.low:
        return FillResult(False, 0.0, 0, ("limit_up_one_way_board",), False)
    px = min(bar.open, limit_price)
    if px <= 0:
        raise DomainValidationError("成交价非法")
    return FillResult(True, round(px, 2), 0, ("open_or_limit",), False)


def match_stop_loss_long(bar: Bar, stop_price: float) -> FillResult:
    """多头止损卖出撮合（F07 核心）。

    跳空规则：开盘价 < stop → 按开盘成交（更差价格），绝不按 stop 成交。
    bar 内触发（low <= stop < open）→ 按 stop 成交。
    一字跌停（high==low==跌停位且 <= stop）→ 无法成交，风险继续存在。
    """
    if bar.open <= stop_price:
        # 开盘即低于止损 → 开盘价成交（跳空损失>1R 可能）
        if bar.high == bar.low and bar.open <= stop_price:
            return FillResult(False, 0.0, 0,
                              ("limit_down_cannot_sell",), False)
        return FillResult(True, round(bar.open, 2), 0,
                          ("gap_open_fill_at_open",), False)
    if bar.low <= stop_price:
        return FillResult(True, round(stop_price, 2), 0,
                          ("intra_bar_stop",), False)
    return FillResult(False, 0.0, 0, ("stop_not_touched",), False)


def dual_touch_conservative(bar: Bar, stop_price: float,
                            target_price: float) -> FillResult:
    """同bar先触止损后触止盈（或反之）未知顺序 → 保守取止损。

    任务书 §7：同一30m棒先后顺序不明，双触达 → 保守规则 + 路径不确定标记。
    """
    touched_stop = bar.low <= stop_price
    touched_target = bar.high >= target_price
    if touched_stop and touched_target:
        r = match_stop_loss_long(bar, stop_price)
        return FillResult(r.filled, r.price, 0,
                          r.assumptions + ("dual_touch_conservative_stop",),
                          path_uncertain=True)
    if touched_stop:
        return match_stop_loss_long(bar, stop_price)
    if touched_target:
        return FillResult(True, round(target_price, 2), 0,
                          ("target_hit",), False)
    return FillResult(False, 0.0, 0, ("nothing_touched",), False)


def participation_cap_qty(desired_qty: int, bar: Bar,
                          max_participation_pct: float = 0.1) -> int:
    """成交量参与率上限（S5-04）。"""
    if not (0 < max_participation_pct <= 1):
        raise DomainValidationError("参与率须在(0,1]")
    cap = int(bar.volume * max_participation_pct)
    return min(desired_qty, cap)
