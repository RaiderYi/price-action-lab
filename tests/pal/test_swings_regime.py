"""S4-01/S4-02 测试：因果摆点 + regime 分立。"""
import os
import sys
from datetime import datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.context.regime import RegimeKind, RegimeLabelBook, assess_trend_regime
from pal.context.swings import SwingPoint, detect_swings, prefix_stability, swings_asof
from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError


def bar(i, o=10.0, h=10.5, l=9.5, c=10.2, vol=100.0, base=None):
    start = datetime(2026, 10, 13, 9, 30, tzinfo=TZ) + timedelta(minutes=30 * i)
    return Bar(instrument_id="X", timeframe="30m", bar_start=start,
               bar_end=start + timedelta(minutes=30),
               available_at=start + timedelta(minutes=30),
               open=o, high=h, low=l, close=c, volume=vol)


def make_with_peak(peak_pos, peak_high=12.0, n=10):
    """构造带单一高点的序列（峰在 peak_pos）。"""
    bars = []
    for i in range(n):
        # 三角形：升到峰再回落
        dist = abs(i - peak_pos)
        h = peak_high - 0.2 * dist
        l = h - 0.8
        bars.append(bar(i, o=h - 0.4, h=h, l=l, c=h - 0.2))
    return bars


class TestCausalSwings:
    def test_swing_confirmed_only_after_right_bars(self):
        """§7：右侧3棒确认——第3根右棒可用前不可用。"""
        bars = make_with_peak(4, n=10)
        # 检查各个时点能看到的摆点
        for cut in range(1, 11):
            visible = detect_swings(bars[:cut], confirm_bars=3)
            for s in visible:
                assert s.available_at <= bars[cut - 1].bar_end

    def test_unconfirmed_candidate_not_emitted(self):
        bars = make_with_peak(4, n=6)   # 峰在4，右侧只有1根 → 未确认
        swings = detect_swings(bars, confirm_bars=3)
        assert not any(s.formed_at == bars[4].bar_start for s in swings)

    def test_confirmed_after_three_right_bars(self):
        bars = make_with_peak(4, n=8)   # 右侧3根（5,6,7）→ 确认
        swings = detect_swings(bars, confirm_bars=3)
        peak = [s for s in swings if s.formed_at == bars[4].bar_start]
        assert len(peak) == 1
        assert peak[0].confirmed_at == bars[7].bar_end   # 第3根右棒结束

    def test_prefix_stability_property(self):
        """追加未来数据不改变过去已确认摆点。"""
        bars = make_with_peak(4, n=12)
        assert prefix_stability(bars, confirm_bars=3)

    def test_asof_view(self):
        bars = make_with_peak(4, n=8)
        all_swings = detect_swings(bars, 3)
        early = swings_asof(all_swings, bars[5].bar_end)
        late = swings_asof(all_swings, bars[7].bar_end)
        assert len(early) <= len(late)

    def test_bad_swing_rejected(self):
        t = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        with pytest.raises(DomainValidationError):
            SwingPoint("X", 10.0, t, t + timedelta(minutes=30), t)
        with pytest.raises(DomainValidationError):
            SwingPoint("H", 10.0, t, t, t)  # confirmed == formed


def daily(i, close, high=None, low=None):
    from datetime import date
    d = date(2026, 1, 5) + timedelta(days=i)
    s = datetime.combine(d, time(9, 30), tzinfo=TZ)
    e = datetime.combine(d, time(15, 0), tzinfo=TZ)
    h = high if high is not None else close * 1.005
    l = low if low is not None else close * 0.995
    o = (h + l) / 2
    return Bar(instrument_id="X", timeframe="1d", bar_start=s, bar_end=e,
               available_at=e, open=o, high=max(h, close, o),
               low=min(l, close, o),
               close=close, volume=1e6, amount=5e7)


def trend_daily(n=80, drift=0.004):
    px = 10.0
    out = []
    for i in range(n):
        px *= 1 + drift
        # 摆动制造 HH/HL
        w = 1.0 if (i // 5) % 2 == 0 else -0.7
        out.append(daily(i, px + w, high=px + w + 0.05, low=px + w - 0.05))
    return out


class TestRegime:
    def test_uptrend_detected(self):
        bars = trend_daily(80, drift=0.004)
        ra = assess_trend_regime(bars)
        assert ra.kind == RegimeKind.UPTREND

    def test_downtrend_detected(self):
        bars = trend_daily(80, drift=-0.004)
        ra = assess_trend_regime(bars)
        assert ra.kind == RegimeKind.DOWNTREND

    def test_insufficient_data_is_unknown_not_range(self):
        """unknown ≠ range（任务书红线）。"""
        ra = assess_trend_regime(trend_daily(10))
        assert ra.kind == RegimeKind.UNKNOWN
        assert ra.reason_code == "INSUFFICIENT_DATA"

    def test_label_book_requires_confirmation(self):
        """切换需连续确认（滞后政策）。"""
        book = RegimeLabelBook(confirm_min=2)
        assert book.update(RegimeKind.UPTREND) == RegimeKind.UNKNOWN  # 第1次不切
        assert book.update(RegimeKind.UPTREND) == RegimeKind.UPTREND  # 第2次切
        assert book.update(RegimeKind.RANGE) == RegimeKind.UPTREND    # 单次抖动不切
        assert book.update(RegimeKind.RANGE) == RegimeKind.RANGE      # 连续2次切

    def test_quality_score_bounds(self):
        ra = assess_trend_regime(trend_daily(80))
        assert 0.0 <= ra.quality_score <= 1.0
        assert "bull_ratio" in ra.features   # 特征可审计
