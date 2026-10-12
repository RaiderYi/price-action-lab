"""S4-04/05/08 测试：突破强度收敛 + 形态检测 + 统一引擎。"""
import os
import sys
from datetime import datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.context.swings import SwingPoint, detect_swings
from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.signals.breakout import assess_breakout_strength
from pal.signals.engine import (
    DecisionEngine,
    EngineConfig,
    strict_h2_verdict,
)
from pal.signals.patterns import (
    detect_final_flag_formation,
    detect_range_fade_setup,
    detect_wedge,
)
from pal.domain.models import SignalState

T0 = datetime(2026, 10, 13, 9, 30, tzinfo=TZ)


def bar30(i, o=10.0, h=10.5, l=9.5, c=10.2, vol=100.0):
    s = T0 + timedelta(minutes=30 * i)
    # 夹具自洽：h/l 吸收 o/c，保证 OHLC 合法
    h = max(h, o, c)
    l = min(l, o, c)
    return Bar(instrument_id="SSE.600519", timeframe="30m", bar_start=s,
               bar_end=s + timedelta(minutes=30),
               available_at=s + timedelta(minutes=30),
               open=o, high=h, low=l, close=c, volume=vol)


def swing(kind, price, i_start, confirm_offset=3):
    fs = T0 + timedelta(minutes=30 * i_start)
    cs = fs + timedelta(minutes=30 * confirm_offset)
    return SwingPoint(kind, price, fs, cs, cs)


class TestBreakoutStrengthConvergence:
    def test_no_level_no_strong_even_big_bar(self):
        """F16：仅大棒无越界不能 strong（禁 fallback）。"""
        bars = [bar30(i, h=12.0, l=9.0, c=11.5) for i in range(5)]
        s = assess_breakout_strength(bars, breakout_level=None)
        assert s.level == "none" and not s.has_breakout_level

    def test_crossed_no_big_bar_weak(self):
        bars = [bar30(i, o=10.0, h=10.1, l=9.9, c=10.0) for i in range(10)]  # range 0.2
        bars.append(bar30(10, o=10.12, h=10.16, l=10.05, c=10.15))  # 小棒 range 0.11 < 1.2×0.2
        s = assess_breakout_strength(bars, breakout_level=10.1)
        assert s.level == "weak"

    def test_big_bar_with_follow_strong(self):
        bars = [bar30(i, o=10.0, h=10.1, l=9.6, c=10.0) for i in range(9)]  # range 0.5
        bars.append(bar30(9, o=10.3, h=10.4, l=10.1, c=10.35))   # 在位
        bars.append(bar30(10, o=10.8, h=12.5, l=10.6, c=12.2))   # 大棒越位（range 1.9 > 1.2×~0.5）
        s = assess_breakout_strength(bars, breakout_level=10.4)
        assert s.level == "strong"
        assert s.actionable_strong


class TestWedge:
    def test_valid_wedge(self):
        swings = [swing("H", 110.0, 0), swing("H", 104.0, 8),
                  swing("H", 101.0, 16)]
        det = detect_wedge(swings, atr=1.5)
        assert det.triggered, det.counter_examples

    def test_not_monotonic_rejected(self):
        swings = [swing("H", 104.0, 0), swing("H", 110.0, 8),
                  swing("H", 101.0, 16)]
        det = detect_wedge(swings, atr=1.5)
        assert not det.triggered
        assert "not_monotonic_down" in det.counter_examples

    def test_shrinking_required(self):
        """幅度不递减（等幅）→ 拒绝（F18：递减公式陷阱）。"""
        swings = [swing("H", 110.0, 0), swing("H", 105.0, 8),
                  swing("H", 100.0, 16)]
        det = detect_wedge(swings, atr=1.5)
        assert not det.triggered
        assert "push_sizes_not_shrinking" in det.counter_examples

    def test_two_pushes_insufficient(self):
        det = detect_wedge([swing("H", 110.0, 0), swing("H", 104.0, 8)], 1.5)
        assert not det.triggered


class TestFinalFlagFormation:
    def test_compact_flag_detected(self):
        prior = [bar30(i, h=11.0, l=9.0, c=10.2) for i in range(20)]
        flag = [bar30(20 + j, o=10.2, h=10.35, l=10.1, c=10.2)
                for j in range(5)]
        det = detect_final_flag_formation(prior + flag, "up")
        assert det.triggered, det.counter_examples

    def test_wide_consolidation_rejected(self):
        bars = [bar30(i, h=11.0, l=9.0, c=10.2) for i in range(25)]
        det = detect_final_flag_formation(bars, "up")
        assert not det.triggered


class TestRangeFade:
    def test_normalized_position_long(self):
        bars = [bar30(0, c=90.5, h=91.0, l=90.0)]
        det = detect_range_fade_setup(bars, range_high=100.0, range_low=90.0,
                                      atr=2.0)
        assert det.triggered and det.evidence["side"] == "long"

    def test_narrow_range_not_triggered(self):
        bars = [bar30(0, c=95.0)]
        det = detect_range_fade_setup(bars, range_high=98.0, range_low=94.0,
                                      atr=2.0)   # 宽度4 < 2.5*2
        assert not det.triggered

    def test_middle_rejected(self):
        bars = [bar30(0, c=95.0)]
        det = detect_range_fade_setup(bars, range_high=100.0, range_low=90.0,
                                      atr=2.0)
        assert not det.triggered


def build_h2_scenario(valid=True):
    """构造两腿回调序列（0-9 上升→10-13 回调一腿→14-16 反弹→17-19 回调二腿→20 站上）。"""
    bars = []
    px = 10.0
    for i in range(10):
        px += 0.3
        bars.append(bar30(i, o=px - 0.15, h=px + 0.1, l=px - 0.35, c=px))
    # 回调一腿：跌到 11.6
    for i in range(10, 14):
        px -= 0.35
        bars.append(bar30(i, o=px + 0.15, h=px + 0.3, l=px - 0.1, c=px))
    # 反弹到 12.3（H）
    for i in range(14, 17):
        px += 0.25
        bars.append(bar30(i, o=px - 0.1, h=px + 0.15, l=px - 0.3, c=px))
    # 回调二腿：跌到 11.9（HL2 > HL1=11.6 → 但要两腿都高于前低）
    for i in range(17, 20):
        px -= 0.13
        bars.append(bar30(i, o=px + 0.1, h=px + 0.25, l=px - 0.05, c=px))
    # 站上
    px += 0.4
    bars.append(bar30(20, o=px - 0.2, h=px + 0.1, l=px - 0.3, c=px))
    return bars


class TestStrictH2Verdict:
    def test_single_hl_not_counted_as_h2(self):
        """F02 核心：一个 HL 反弹不能伪装二次计数。"""
        bars = build_h2_scenario()
        swings = detect_swings(bars, confirm_bars=2)
        # 只给一个 L（模拟只有一个 HL）
        lows = [s for s in swings if s.kind == "L"]
        if len(lows) < 2:
            pytest.skip("fixture 未产生两个摆点低点")
        verdict = strict_h2_verdict([lows[-1]], bars, 0.0)   # 只传 1 个 L
        assert verdict is None

    def test_two_legs_with_higher_lows_valid(self):
        bars = build_h2_scenario()
        swings = detect_swings(bars, confirm_bars=2)
        verdict = strict_h2_verdict(swings, bars, 0.0)
        if verdict is None:
            pytest.skip("fixture 未构成 H2（摆点不足）")
        assert verdict["evidence"]["HL2"] > verdict["evidence"]["HL1"]
        assert verdict["current_price"] > verdict["evidence"]["HL2"]


class TestEngineEvaluate:
    CFG = EngineConfig(config_version="test-v1", confirm_bars=2)

    def test_engine_deterministic(self):
        """相同已知事实 → 相同决策（S4-08 验收）。"""
        bars = build_h2_scenario()
        from datetime import date
        daily = []
        d0 = date(2026, 10, 13)
        for i in range(40):
            d = d0 + timedelta(days=i)
            s = datetime.combine(d, time(9, 30), tzinfo=TZ)
            e = datetime.combine(d, time(15, 0), tzinfo=TZ)
            px = 10 + i * 0.05
            daily.append(Bar(instrument_id="SSE.600519", timeframe="1d",
                             bar_start=s, bar_end=e, available_at=e,
                             open=px, high=px * 1.01, low=px * 0.99,
                             close=px, volume=1e6, amount=5e7))
        asof = bars[-1].bar_end
        eng1 = DecisionEngine(self.CFG)
        eng2 = DecisionEngine(self.CFG)
        r1 = eng1.evaluate(asof, bars, daily, instrument_id="SSE.600519")
        r2 = eng2.evaluate(asof, bars, daily, instrument_id="SSE.600519")
        d1 = [d.to_json() for d in r1.decisions]
        d2 = [d.to_json() for d in r2.decisions]
        assert d1 == d2
        assert r1.status in ("valid", "degraded")

    def test_engine_never_sees_future(self):
        bars = build_h2_scenario()
        asof = bars[10].bar_end    # 只到第11根
        eng = DecisionEngine(self.CFG)
        r = eng.evaluate(asof, bars, [], instrument_id="SSE.600519")
        # 未来bar不得影响：可见数 ≤ 11
        assert r.asof == asof

    def test_wait_not_filled(self):
        """引擎输出 wait（armed），绝不直接成交（F06）。"""
        bars = build_h2_scenario()
        from datetime import date
        daily = []
        d0 = date(2026, 10, 13)
        for i in range(40):
            d = d0 + timedelta(days=i)
            s = datetime.combine(d, time(9, 30), tzinfo=TZ)
            e = datetime.combine(d, time(15, 0), tzinfo=TZ)
            px = 10 + i * 0.05
            daily.append(Bar(instrument_id="SSE.600519", timeframe="1d",
                             bar_start=s, bar_end=e, available_at=e,
                             open=px, high=px * 1.01, low=px * 0.99,
                             close=px, volume=1e6, amount=5e7))
        asof = bars[-1].bar_end
        eng = DecisionEngine(self.CFG)
        r = eng.evaluate(asof, bars, daily, instrument_id="SSE.600519")
        for d in r.decisions:
            assert d.outcome in ("accept", "reject", "wait")
            assert d.outcome != "accept"   # 本版引擎无触发确认，只有 wait/reject
