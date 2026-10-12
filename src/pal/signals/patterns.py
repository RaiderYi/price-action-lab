"""研究级形态检测（S4-05）：wedge / final_flag / tr_fade。

默认 research 成熟度（不进生产信号面）；每类绑定结构证据字段，
方向/间隔/幅度校验有正反例（任务书 S4-05 验收）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from pal.context.swings import SwingPoint, detect_swings
from pal.data.bars import Bar
from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class PatternDetection:
    family: str
    triggered: bool
    evidence: dict
    counter_examples: tuple = ()   # 触发失败时的具体反例（可审计）


def detect_wedge(swings: Sequence[SwingPoint], atr: float,
                 min_push_gap_bars: int = 3) -> PatternDetection:
    """三推楔形（KR 待补：三推各自绑定 bar，校验方向/间隔/幅度）。

    向下楔形（多头反转）：三个 LH 依次下移但幅度递减，且间隔≥min_push_gap。
    仅"幅度递减"不够——推点必须同向单调（F18）。
    """
    highs = [s for s in swings if s.kind == "H"]
    if len(highs) < 3:
        return PatternDetection("wedge", False, {},
                                ("fewer_than_3_highs",))
    p1, p2, p3 = highs[-3], highs[-2], highs[-1]
    fails = []
    # 方向单调：三个推点依次下移（向下楔形）
    if not (p1.price > p2.price > p3.price):
        fails.append("not_monotonic_down")
    # 幅度递减
    d1 = p1.price - p2.price
    d2 = p2.price - p3.price
    if not (d2 < d1):
        fails.append("push_sizes_not_shrinking")
    # 间隔有效（用 bar 时间差近似，最少 min_push_gap 根 30m）
    if (p2.formed_at - p1.formed_at).total_seconds() < min_push_gap_bars * 1800 * 0.5:
        fails.append("push_gap_too_small_12")
    if (p3.formed_at - p2.formed_at).total_seconds() < min_push_gap_bars * 1800 * 0.5:
        fails.append("push_gap_too_small_23")
    if atr <= 0:
        fails.append("atr_not_positive")
    return PatternDetection(
        "wedge", not fails,
        {"p1": p1.price, "p2": p2.price, "p3": p3.price,
         "d1": round(d1, 4), "d2": round(d2, 4), "atr": atr},
        tuple(fails))


def detect_final_flag_formation(bars: Sequence[Bar],
                                trend_direction: str) -> PatternDetection:
    """final_flag 事件1：旗形本体（紧凑小区间），只观察（KR-FINAL-FLAG-001）。"""
    if trend_direction not in ("up", "down"):
        raise DomainValidationError("trend_direction 非法")
    if len(bars) < 8:
        return PatternDetection("final_flag_formation", False, {}, ("insufficient_bars",))
    recent = sorted(bars, key=lambda b: b.bar_start)[-5:]
    bodies = [abs(b.close - b.open) for b in recent]
    ranges = [b.high - b.low for b in recent]
    prior = sorted(bars, key=lambda b: b.bar_start)[:-5][-20:]
    prior_avg_range = (sum(b.high - b.low for b in prior) / len(prior)) if prior else 0
    compact = all(r <= 0.7 * prior_avg_range for r in ranges if prior_avg_range > 0)
    small_body = all(bd <= 0.5 * rg for bd, rg in zip(bodies, ranges) if rg > 0)
    fails = []
    if prior_avg_range > 0 and not compact:
        fails.append("not_compact")
    if not small_body:
        fails.append("bodies_too_large")
    return PatternDetection("final_flag_formation", not fails,
                            {"recent_ranges": [round(r, 3) for r in ranges],
                             "prior_avg_range": round(prior_avg_range, 3)},
                            tuple(fails))


def detect_range_fade_setup(bars: Sequence[Bar], range_high: float,
                            range_low: float, atr: float,
                            min_width_atr: float = 2.5) -> PatternDetection:
    """tr_fade：区间归一化位置（F19：不用固定2%，用区间宽度归一）。"""
    if atr <= 0:
        return PatternDetection("tr_fade", False, {"atr": atr}, ("atr_not_positive",))
    width = range_high - range_low
    if width < min_width_atr * atr:
        return PatternDetection("tr_fade", False,
                                {"width": width, "required": min_width_atr * atr},
                                ("range_too_narrow"))
    last = sorted(bars, key=lambda b: b.bar_start)[-1]
    pos = (last.close - range_low) / width     # 归一化 0..1
    evidence = {"normalized_pos": round(pos, 3), "width": width, "atr": atr}
    # 靠近下沿做多：pos ≤ 0.25（归一化尺度，非固定百分比价格带）
    if pos <= 0.25:
        return PatternDetection("tr_fade", True,
                                {**evidence, "side": "long"}, ())
    if pos >= 0.75:
        return PatternDetection("tr_fade", True,
                                {**evidence, "side": "short"}, ())
    return PatternDetection("tr_fade", False, evidence, ("middle_of_range",))
