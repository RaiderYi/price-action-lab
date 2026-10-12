"""统一突破强度服务（R05 修正：本棒突破 ≠ 下一棒跟随）。

修正规则：
- crossed：信号棒收盘越位（本棒事件）；
- follow_through：只有**信号棒之后的新完成棒**收盘仍在位上方才 True
  （调用方逐棒推进传入 follow_bars）；无后续棒时为 None（尚未可判）；
- strong 需：大棒 + 收盘越位 + 极端收盘（继承 F03 质量条件）；
- actionable_strong = strong 且 follow_through is True。
引擎准入必须核验强度（weak 不 ARMED——由 engine 侧执行）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from pal.data.bars import Bar
from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class BreakoutStrength:
    level: str              # "strong" | "moderate" | "weak" | "none"
    has_breakout_level: bool
    crossed_level: bool
    follow_through: Optional[bool]   # None=尚无后续棒可判
    extreme_close: Optional[bool]    # R05：继承极端收盘质量条件
    breakout_bar_id: Optional[str]   # R05：冻结突破棒与位
    reasons: tuple

    @property
    def actionable_strong(self) -> bool:
        return self.level == "strong" and self.follow_through is True


def assess_breakout_strength(bars: Sequence[Bar],
                             breakout_level: Optional[float],
                             confirm_follow: bool = True,
                             extreme_close_pct: float = 0.7) -> BreakoutStrength:
    """统一强度评估（R05 语义）。

    bars[-1] = 信号棒；bars[:-1] 尾部为已完成的**后续跟随棒**（若有）。
    调用约定：调用方在信号棒出现后的下一棒再次调用本函数，把两棒都
    传入——follow_through 由后续棒判定，本棒自身永不构成跟随。
    """
    if not bars:
        raise DomainValidationError("空序列")
    ordered = sorted(bars, key=lambda b: b.bar_start)
    last = ordered[-1]

    if breakout_level is None or breakout_level <= 0:
        return BreakoutStrength("none", False, False, None, None, None,
                                ("no_breakout_level",))
    crossed = last.close > breakout_level
    if not crossed:
        return BreakoutStrength("none", True, False, None, None,
                                str(last.bar_start), ("close_below_level",))

    # 大棒
    ranges = [b.high - b.low for b in ordered[:-1][-14:]] or [last.high - last.low]
    avg_range = sum(ranges) / len(ranges)
    big_bar = (last.high - last.low) >= 1.2 * avg_range

    # R05：极端收盘（继承 F03 质量条件，非仅越位）
    bar_range = last.high - last.low
    pos = (last.close - last.low) / bar_range if bar_range > 0 else 0.5
    extreme = pos >= extreme_close_pct

    # R05：跟随只能来自信号棒之后的完成棒。
    # 本函数把 last 视为信号棒：无先验突破棒信息时 follow=None（不可判）。
    # 若调用方把信号棒与后续棒一起传入（信号棒=倒数第二根），则由
    # follow_bars 参数变体判定——见 assess_with_follow_bars。
    follow = None

    if big_bar and extreme:
        level = "strong"
    elif big_bar:
        level = "moderate"
    else:
        level = "weak"
    reasons = [r for r, ok in (("big_bar", big_bar),
                               ("crossed", True),
                               ("extreme_close", extreme)) if ok]
    if follow is None:
        reasons.append("follow_undetermined_needs_next_bar")
    return BreakoutStrength(level, True, True, follow, extreme,
                            str(last.bar_start), tuple(reasons))


def assess_with_follow_bars(bars: Sequence[Bar],
                            breakout_bar_start,
                            breakout_level: float,
                            extreme_close_pct: float = 0.7) -> BreakoutStrength:
    """信号棒已冻结后，用后续完成棒判跟随（R05 主入口）。

    - 在 bars 中定位突破棒（bar_start == breakout_bar_start）；
    - follow_through = 突破棒之后存在完成棒且其收盘 > breakout_level；
    - 强度等级仍按突破棒本体计算（大棒+极端收盘）。
    """
    if not bars:
        raise DomainValidationError("空序列")
    ordered = sorted(bars, key=lambda b: b.bar_start)
    idx = next((i for i, b in enumerate(ordered)
                if str(b.bar_start) == str(breakout_bar_start)), None)
    if idx is None:
        raise DomainValidationError(f"突破棒不在序列中: {breakout_bar_start}")
    sig = ordered[idx]
    follow_bars = ordered[idx + 1:]
    if not follow_bars:
        follow = None
    else:
        follow = all(b.close > breakout_level for b in follow_bars)

    ranges = [b.high - b.low for b in ordered[:idx][-14:]] or [sig.high - sig.low]
    avg_range = sum(ranges) / len(ranges) if ranges else 0.0
    big_bar = (sig.high - sig.low) >= 1.2 * avg_range if avg_range > 0 else False
    bar_range = sig.high - sig.low
    pos = (sig.close - sig.low) / bar_range if bar_range > 0 else 0.5
    extreme = pos >= extreme_close_pct

    if big_bar and extreme:
        level = "strong"
    elif big_bar:
        level = "moderate"
    else:
        level = "weak"
    return BreakoutStrength(level, True, True, follow, extreme,
                            str(sig.bar_start),
                            ("big_bar", big_bar, "extreme_close", extreme,
                             "follow_from_later_bars", follow))
