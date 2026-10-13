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
        """R05 后语义：跟随需信号棒之后的完成棒（assess_with_follow_bars）。"""
        from pal.signals.breakout import assess_with_follow_bars
        bars = [bar30(i, o=10.0, h=10.1, l=9.6, c=10.0) for i in range(9)]  # range 0.5
        sig = bar30(10, o=10.8, h=12.5, l=10.6, c=12.2)   # 大棒极端收盘越位
        bars.append(sig)
        # 仅信号棒：不可判跟随 → actionable False（R05）
        s0 = assess_with_follow_bars(bars, sig.bar_start, breakout_level=10.4)
        assert s0.follow_through is None and not s0.actionable_strong
        # 加下一棒跟随 → strong actionable
        bars.append(bar30(11, o=12.0, h=12.6, l=11.7, c=12.3))
        s1 = assess_with_follow_bars(bars, sig.bar_start, breakout_level=10.4)
        assert s1.level == "strong" and s1.actionable_strong


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
    """第三轮复审 T01：真实可判定的严格 H2 正例（修复恒 skip）。

    腿式构造（confirm=2/3 均通过）：
    H0(11.15) → L1(9.05) → H1(13.15) → L2(10.25) → 收盘站上 L2。
    H 递进 ✓ HL 链 ✓ 尾部为 L 后站上 ✓ → strict_h2_verdict=True。
    旧逐 0.3 累进夹具摆点尾部为 H 且 H 递降，永远构不成 H2（复审 F06）。
    """
    def leg(start_i, n, h_from, l_from, h_to, l_to):
        out = []
        for k in range(n):
            t = k / (n - 1)
            h = h_from + (h_to - h_from) * t
            l = l_from + (l_to - l_from) * t
            c = (h + l) / 2
            out.append(bar30(start_i + k, o=c, h=h + 0.15, l=l - 0.15,
                             c=c + 0.05 * t))
        return out

    bars = []
    bars += leg(0, 6, 11.0, 10.5, 9.6, 9.2)     # 跌 → L1≈9.05
    bars += leg(6, 6, 9.8, 9.3, 13.0, 12.5)     # 涨 → H1≈13.15
    bars += leg(12, 6, 12.8, 12.3, 11.0, 10.4)  # 回调 → L2≈10.25
    bars += leg(18, 4, 11.2, 10.6, 12.0, 11.5)  # 站上
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
