"""因果摆点检测（S4-01，F17）。

任务书 §7 因果验收：
- "使用右侧3棒确认的摆点：第3根右棒可用前不可发出基于该摆点的决策"；
- "在 t 之后追加或改变K线，再回放到 t：t及之前已形成决策不变"。

设计：摆点 = 局部极值 + 右侧 N 棒确认。每个摆点带 formed_at（极值棒
时间）与 confirmed_at（第 N 根右棒收盘时间）与 available_at（=confirmed_at）。
追加未来数据不得改变已确认摆点（追加只可能产生新摆点候选）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from pal.data.bars import Bar
from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class SwingPoint:
    """已确认摆点。kind: 'H'=局部高点 'L'=局部低点。"""
    kind: str                    # "H" | "L"
    price: float
    formed_at: datetime          # 极值棒 bar_start
    confirmed_at: datetime       # 第 confirm_bars 根右棒 bar_end
    available_at: datetime       # 系统可知（=confirmed_at）

    def __post_init__(self):
        if self.kind not in ("H", "L"):
            raise DomainValidationError(f"摆点类型非法: {self.kind!r}")
        if self.available_at < self.confirmed_at:
            raise DomainValidationError("摆点 available_at 早于 confirmed_at")
        if self.confirmed_at <= self.formed_at:
            raise DomainValidationError("摆点 confirmed_at 必须晚于 formed_at")
        if self.price <= 0:
            raise DomainValidationError("摆点价格必须为正")


def detect_swings(bars: Sequence[Bar], confirm_bars: int = 3) -> List[SwingPoint]:
    """右确认摆点检测（只用序列内信息，天然因果）。

    高点 H：high[i] 严格高于左右各 confirm_bars 根的 high；
    确认时刻 = 右侧第 confirm_bars 根棒的 bar_end。
    数据不足确认的候选不输出（不能把未确认摆点当可用）。
    """
    if confirm_bars < 1:
        raise DomainValidationError("confirm_bars 必须 ≥1")
    n = len(bars)
    ordered = sorted(bars, key=lambda b: b.bar_start)
    out: List[SwingPoint] = []
    for i in range(n):
        left = ordered[max(0, i - confirm_bars):i]
        right = ordered[i + 1:i + 1 + confirm_bars]
        if len(right) < confirm_bars:
            continue    # 右侧不足 → 未确认，不可用（任务书红线）
        b = ordered[i]
        is_h = all(b.high > x.high for x in left) and all(b.high > x.high for x in right)
        is_l = all(b.low < x.low for x in left) and all(b.low < x.low for x in right)
        if is_h:
            confirmed = right[-1].bar_end
            out.append(SwingPoint("H", b.high, b.bar_start, confirmed, confirmed))
        elif is_l:
            confirmed = right[-1].bar_end
            out.append(SwingPoint("L", b.low, b.bar_start, confirmed, confirmed))
    return out


def swings_asof(swings: Sequence[SwingPoint], when: datetime) -> List[SwingPoint]:
    """as-of 视图：只含 available_at <= when 的摆点。"""
    return [s for s in swings if s.available_at <= when]


def prefix_stability(bars: Sequence[Bar], confirm_bars: int = 3) -> bool:
    """前缀一致性自检：任意前缀 t 的摆点集合是全量摆点在 t 可见集的子集。

    即：追加数据不改变过去决策（任务书 §7 因果场景的可执行验证）。
    """
    full = detect_swings(bars, confirm_bars)
    for cut in range(1, len(bars) + 1):
        prefix = list(bars[:cut])
        cut_time = prefix[-1].bar_end
        from_prefix = detect_swings(prefix, confirm_bars)
        visible_full = swings_asof(full, cut_time)
        # 前缀产生的摆点必须 ⊆ 全量摆点（同 formed_at+kind）
        a = {(s.kind, s.formed_at) for s in from_prefix}
        b = {(s.kind, s.formed_at) for s in visible_full}
        if not a <= b:
            return False
    return True
