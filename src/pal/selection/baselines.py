"""S3-06 透明基线选股：流动性 + 日线相对强度/趋势。

设计（任务书 S3-06 验收）：
- 从完整可交易池排名（不是从五模型已过滤池）；
- 窗口、调仓频率、排除条件预先固定（写死在构造参数，不偷看结果）；
- 不使用当期未来收益（只用 as-of 可得的收益）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from pal.data.bars import Bar
from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class BaselineParams:
    """透明基线参数（预注册，不调参）。"""
    momentum_window_days: int = 60
    liquidity_min_amount_20d: float = 30_000_000.0   # 20日均成交额下限（元）
    exclude_st: bool = True
    top_k: int = 50


def relative_strength(daily_bars: Sequence[Bar], window_days: int) -> float:
    """as-of 动量：window 前收盘 → 最新收盘 的收益。

    只用已完成日线（Bar 已在构造层保证因果）。
    """
    if len(daily_bars) < window_days + 1:
        raise DomainValidationError(
            f"数据不足：需 {window_days + 1} 根完成日线，实得 {len(daily_bars)}")
    last = daily_bars[-1].close
    base = daily_bars[-1 - window_days].close
    return (last - base) / base


def avg_daily_amount(daily_bars: Sequence[Bar], window_days: int = 20) -> float:
    if len(daily_bars) < window_days:
        raise DomainValidationError("成交额窗口数据不足")
    chunk = daily_bars[-window_days:]
    return sum(b.amount for b in chunk) / window_days


def baseline_rank(daily_by_instrument: Dict[str, Sequence[Bar]],
                  params: BaselineParams,
                  is_st=lambda iid: False) -> List[Tuple[str, float, Dict[str, float]]]:
    """透明基线排名（S0 变体用）。

    返回 [(instrument_id, score, components)]，按动量降序、同分按代码升序。
    """
    out = []
    for iid, bars in daily_by_instrument.items():
        if params.exclude_st and is_st(iid):
            continue
        try:
            mom = relative_strength(bars, params.momentum_window_days)
            liq = avg_daily_amount(bars, 20)
        except DomainValidationError:
            continue  # 数据不足直接不参与（报告层应计数，见返回 components）
        if liq < params.liquidity_min_amount_20d:
            continue
        # 简单趋势确认：20日均线在 60日均线之上加分（0/1）
        ma20 = sum(b.close for b in bars[-20:]) / 20
        ma60 = sum(b.close for b in bars[-60:]) / 60
        trend_ok = 1.0 if ma20 > ma60 else 0.0
        score = mom + 0.1 * trend_ok  # 分解可见
        out.append((iid, score, {"momentum": mom, "liquidity_amount": liq,
                                 "trend_bonus": trend_ok}))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out[:params.top_k]
