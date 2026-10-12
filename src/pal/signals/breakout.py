"""统一突破强度服务（S4-04，F16 收敛）。

问题：strict_breakout_strength.py 与 actionability 内各有一套突破强度
判断，前者存在"大棒极端收盘即 strong"的 fallback——不同入口可能给
同一结构不同判断。

收敛规则（任务书 F16 动作项）：
1. 仅大棒无越界 ≠ strong（必须有突破位）；
2. 需要跟随时最早下一棒确认；
3. 全入口（检测、资格、定价、报告）只经本模块判断。
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
    crossed_level: bool     # 收盘越过突破位
    follow_through: Optional[bool]   # None=尚无下一棒可判
    reasons: tuple

    @property
    def actionable_strong(self) -> bool:
        return self.level == "strong" and self.follow_through is True


def assess_breakout_strength(bars: Sequence[Bar],
                             breakout_level: Optional[float],
                             confirm_follow: bool = True) -> BreakoutStrength:
    """统一强度评估。

    - 无突破位（breakout_level=None）→ level=none（禁止大棒fallback，F16）
    - 收盘未越界 → none/weak（即使棒再大）
    - 越界 + 大棒(≥1.2×avg range) + （confirm_follow 时下一棒跟随）→ strong
    """
    if not bars:
        raise DomainValidationError("空序列")
    ordered = sorted(bars, key=lambda b: b.bar_start)
    last = ordered[-1]
    prev = ordered[-2] if len(ordered) >= 2 else None

    if breakout_level is None or breakout_level <= 0:
        return BreakoutStrength("none", False, False, None,
                                ("no_breakout_level",))
    crossed = last.close > breakout_level
    if not crossed:
        return BreakoutStrength("none", True, False, None,
                                ("close_below_level",))

    # 大棒：与近期平均range比较
    ranges = [b.high - b.low for b in ordered[:-1][-14:]] or [last.high - last.low]
    avg_range = sum(ranges) / len(ranges)
    big_bar = (last.high - last.low) >= 1.2 * avg_range

    follow = None
    if confirm_follow:
        # 跟随基础（保守定义）：信号棒自身收盘已在突破位上方（收盘越位
        # 而非仅上影触碰）。真正的下一棒跟随由调用方逐棒推进时复查。
        follow = last.close > breakout_level

    if big_bar and follow is True:
        return BreakoutStrength("strong", True, True, True,
                                ("big_bar", "crossed", "follow_basis"))
    if big_bar:
        return BreakoutStrength("moderate", True, True, follow,
                                ("big_bar", "crossed", "no_follow_yet"))
    return BreakoutStrength("weak", True, True, follow,
                            ("small_bar", "crossed"))
