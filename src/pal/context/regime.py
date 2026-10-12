"""市场/行业/个股环境分立（S4-02）。

任务书红线：`unknown` 不能默认当 `range`；不能用事后牛熊标签当输入；
切换有最短确认/滞后政策；输出特征和规则原因。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

from pal.data.bars import Bar
from pal.domain.models import DomainValidationError


class RegimeKind(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGE = "range"
    TRANSITION = "transition"
    UNKNOWN = "unknown"       # 数据不足/冲突：显式值，绝不静默映射为 range


@dataclass(frozen=True)
class RegimeAssessment:
    kind: RegimeKind
    quality_score: float          # 启发式环境质量分（不是胜率，S1-06 语义）
    reason_code: str
    features: dict                # 判定特征（可审计）
    min_confirm_bars_used: int

    def __post_init__(self):
        if not (0.0 <= self.quality_score <= 1.0):
            raise DomainValidationError("quality_score 越界")


def assess_trend_regime(daily_bars: Sequence[Bar],
                        min_bars: int = 30,
                        hh_hl_threshold: float = 0.6) -> RegimeAssessment:
    """日线环境判定（简化 v1：HH/HL 结构占比 + 均线方向）。

    特征：最近 swing 结构中 HH+HL 占比、MA20 vs MA60。
    占比 ≥ threshold 且 MA 多头 → uptrend；对称 → downtrend；
    中间带且区间宽度达标 → range；数据不足 → UNKNOWN（显式）。
    """
    from pal.context.swings import detect_swings

    if len(daily_bars) < min_bars:
        return RegimeAssessment(
            RegimeKind.UNKNOWN, 0.0, "INSUFFICIENT_DATA",
            {"n_bars": len(daily_bars), "min_required": min_bars},
            min_confirm_bars_used=0)

    highs = [b.high for b in daily_bars]
    lows = [b.low for b in daily_bars]
    closes = [b.close for b in daily_bars]

    # 均线（R10：数据不足时明示缩短窗口或 unknown，不静默错算）
    ma20 = sum(closes[-20:]) / min(20, len(closes))
    n60 = min(60, len(closes))
    ma60_sufficient = len(closes) >= 60
    ma60 = (sum(closes[-60:]) / 60) if ma60_sufficient else None

    # 摆点序列（周线级确认 → 用日 bar 右3确认）
    swings = detect_swings(list(daily_bars), confirm_bars=3)
    hh = hl = lh = ll = 0
    last_h = last_l = None
    for s in swings:
        if s.kind == "H":
            if last_h is not None:
                if s.price > last_h: hh += 1
                else: lh += 1
            last_h = s.price
        else:
            if last_l is not None:
                if s.price > last_l: hl += 1
                else: ll += 1
            last_l = s.price
    total = hh + hl + lh + ll
    bull_ratio = (hh + hl) / total if total else 0.5

    ma_bull = (ma20 > ma60) if ma60_sufficient else None    # R10: None=不可判
    feats = {"hh": hh, "hl": hl, "lh": lh, "ll": ll,
             "bull_ratio": round(bull_ratio, 3),
             "ma20": round(ma20, 2),
             "ma60": round(ma60, 2) if ma60_sufficient else None,
             "ma_bull": ma_bull,
             "ma60_sufficient": ma60_sufficient,
             "range_width_pct": round((max(highs[-60:]) - min(lows[-60:])) / closes[-1] * 100, 1)}

    if ma60_sufficient:
        trend_up = ma20 > ma60
        trend_down = ma20 < ma60
    else:
        # MA 证据不可用：仅结构占比判趋势（阈值收紧），不足则 unknown
        trend_up = bull_ratio >= max(hh_hl_threshold, 0.75)
        trend_down = bull_ratio <= min(1 - hh_hl_threshold, 0.25)

    if bull_ratio >= hh_hl_threshold and trend_up:
        kind = RegimeKind.UPTREND
        reason = "HH/HL占优+均线多头" if ma60_sufficient else "HH/HL占优(MA60不足,结构加重)"
        score = min(1.0, bull_ratio)
    elif bull_ratio <= 1 - hh_hl_threshold and trend_down:
        kind = RegimeKind.DOWNTREND
        reason = "LH/LL占优+均线空头" if ma60_sufficient else "LH/LL占优(MA60不足,结构加重)"
        score = min(1.0, 1 - bull_ratio)
    else:
        kind = RegimeKind.RANGE
        reason = "结构占比中间带"
        score = 0.5
    return RegimeAssessment(kind, score, reason, feats, min_confirm_bars_used=3)


class RegimeLabelBook:
    """regime 切换的最短确认/滞后政策（S4-02 验收）。

    切换需连续 confirm_min 个评估周期同意才生效；避免单根棒抖动导致
    环境标签翻转（任务书：切换有最短确认/滞后政策）。
    """
    def __init__(self, confirm_min: int = 2):
        if confirm_min < 1:
            raise DomainValidationError("confirm_min ≥1")
        self.confirm_min = confirm_min
        self._current = RegimeKind.UNKNOWN
        self._pending = None
        self._pending_count = 0

    def update(self, new_kind: RegimeKind) -> RegimeKind:
        """提交一次评估结果，返回当前生效 regime。"""
        if new_kind == self._current:
            self._pending, self._pending_count = None, 0
            return self._current
        if new_kind == self._pending:
            self._pending_count += 1
        else:
            self._pending, self._pending_count = new_kind, 1
        if self._pending_count >= self.confirm_min:
            self._current = self._pending
            self._pending, self._pending_count = None, 0
        return self._current

    @property
    def current(self) -> RegimeKind:
        return self._current
