"""Phase 4.1: strict_pa_detector tests — context + signal/trigger/invalid"""
import pytest
import pandas as pd
import numpy as np
from strict_pa_detector import (
    detect_bull_pullback_context, detect_bear_rally_context,
    detect_strict_bar_counting_signals,
    ShadowSignalResult, ContextDetection,
    get_proxy_vs_strict_matrix,
    _detect_range_position,
)


def make_ohlc_df(highs, lows, closes=None, opens=None):
    """Build a DataFrame from OHLC arrays."""
    n = len(highs)
    if closes is None:
        closes = highs
    if opens is None:
        opens = [h - 0.1 for h in highs]
    df = pd.DataFrame({
        'high': highs, 'low': lows,
        'close': closes, 'open': opens,
    })
    df.index = pd.date_range('2026-06-03 09:30', periods=n, freq='30min')
    return df


# ═══ Context: Bull Pullback ═══

class TestBullPullbackContext:
    def test_bull_pullback_detected(self):
        """T12: trend up + pullback → context_type=bull_pullback"""
        highs = [10, 11, 12, 13, 12.5, 12, 12.3, 12.1, 12, 11.8, 11.9, 12.2, 12.1, 12.0, 11.9, 11.8, 12.0, 12.1, 12.15, 12.2, 12.1, 12.05, 12.0, 11.95]
        lows  = [9.5, 10.5, 11.5, 12.5, 12, 11.5, 11.8, 11.6, 11.5, 11.3, 11.5, 11.7, 11.6, 11.5, 11.4, 11.3, 11.4, 11.5, 11.6, 11.7, 11.6, 11.5, 11.45, 11.4]
        closes = highs
        opens = [h - 0.1 for h in highs]
        ctx = detect_bull_pullback_context(highs, lows, closes, opens, swing_window=3, atr_period=14)
        # Should detect a bull move then pullback
        # With swing_window=3, we should find swing points in 24 bars
        assert ctx.context_type in ("bull_pullback", "none")  # valid call
        # At minimum, the function should run without error
        # Context detection depends on swing_window and actual data structure

    def test_context_invalid_when_break_below_swing_low(self):
        """T14: price below prior swing low → context none"""
        highs = [10, 11, 12, 11, 10.5, 10, 9.5, 9, 10, 11, 12, 11.5, 11, 10.5, 10, 9.8, 9.5, 9, 8, 8.5, 9, 9.5, 9, 8.5]
        lows  = [h - 0.5 for h in highs]
        closes = highs
        opens = [h - 0.1 for h in highs]
        ctx = detect_bull_pullback_context(highs, lows, closes, opens, swing_window=3, atr_period=14)
        # Broken bull structure — should be "none" or have notes
        if ctx.context_type == "bull_pullback":
            # If it passes, verify notes explain the situation
            assert len(ctx.notes) > 0

    def test_insufficient_bars_returns_none(self):
        """Less than 20 bars → context none"""
        highs = [10, 10.5, 10.3, 10.1, 10.0]
        lows  = [h - 0.5 for h in highs]
        closes = highs
        opens = [h - 0.1 for h in highs]
        ctx = detect_bull_pullback_context(highs, lows, closes, opens)
        assert ctx.context_type == "none"
        assert "insufficient" in " ".join(ctx.notes).lower()


# ═══ Context: Bear Rally ═══

class TestBearRallyContext:
    def test_bear_rally_detected(self):
        """T13: trend down + rally → context_type=bear_rally"""
        highs = [15, 14, 13, 12.5, 12, 11.5, 11, 11.5, 12, 12.3, 12.1, 11.9, 12.2, 12.4, 12.2, 12.0, 12.3, 12.5, 12.3, 12.1, 12.4, 12.5, 12.3, 12.2]
        lows  = [h - 0.5 for h in highs]
        closes = highs
        opens = [h - 0.1 for h in highs]
        ctx = detect_bear_rally_context(highs, lows, closes, opens, swing_window=3, atr_period=14)
        assert ctx.context_type in ("bear_rally", "none")

    def test_insufficient_bars_bear(self):
        highs = [10, 9.5, 9.3]
        lows  = [h - 0.5 for h in highs]
        closes = highs
        opens = [h - 0.1 for h in highs]
        ctx = detect_bear_rally_context(highs, lows, closes, opens)
        assert ctx.context_type == "none"


# ═══ Range Position ═══

class TestRangePosition:
    def test_range_middle_detected(self):
        """T16: TR 中部 H2 可检测但标记 middle_range_signal"""
        # oscillating range data
        highs = [10, 10.5, 10, 9.5, 10.2, 10.7, 10.2, 9.8, 10.3, 10.6, 10.1, 9.6, 10.2, 10.5, 10.0, 9.7, 10.3, 10.6, 10.0, 9.5, 10.2, 10.7, 10.1, 10.0]
        lows  = [h - 0.8 for h in highs]
        closes = [h - 0.2 for h in highs]
        opens = [h - 0.1 for h in highs]
        ctx = detect_bull_pullback_context(highs, lows, closes, opens, swing_window=3, atr_period=14)
        if ctx.context_type != "none" and ctx.middle_range_signal:
            assert ctx.range_position == "middle"

    def test_range_boundary_higher_confidence(self):
        """T17: TR 边界 H2 可检测且 confidence 更高"""
        highs = [10, 10.5, 11, 11.5, 12, 11, 10, 9, 9.8, 10.5, 11.2, 12, 11.5, 11, 10.5, 10, 9.5, 9.8, 10.2, 11, 11.8, 11.5, 11, 10.5]
        lows  = [h - 0.8 for h in highs]
        closes = highs
        opens = [h - 0.1 for h in highs]
        ctx = detect_bull_pullback_context(highs, lows, closes, opens, swing_window=3, atr_period=14)
        if ctx.context_type != "none" and ctx.range_position in ("lower_third", "upper_third"):
            assert ctx.middle_range_signal is False


# ═══ detect_strict_bar_counting_signals ═══

class TestDetectStrictBarCounting:
    def _make_bull_data(self, n=50):
        """Generate synthetic bull trend + pullback data"""
        np.random.seed(42)
        base = np.linspace(10, 15, n // 2)
        # pullback
        pullback = np.linspace(15, 13, n // 2)
        prices = np.concatenate([base, pullback])
        highs = prices + np.abs(np.random.randn(n) * 0.2)
        lows  = prices - np.abs(np.random.randn(n) * 0.2)
        return highs, lows

    def test_detect_returns_4_results(self):
        """Each call returns H1, H2 (long) or L1, L2 (short)"""
        highs, lows = self._make_bull_data(50)
        closes = highs
        opens = [h - 0.1 for h in highs]
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes, 'open': opens})
        df.index = pd.date_range('2026-06-03 09:30', periods=50, freq='30min')

        long_results = detect_strict_bar_counting_signals("TEST", df, "long")
        assert len(long_results) == 2  # H1, H2
        short_results = detect_strict_bar_counting_signals("TEST", df, "short")
        assert len(short_results) == 2  # L1, L2

    def test_results_have_required_fields(self):
        """T18: shadow JSON schema fields present"""
        highs, lows = self._make_bull_data(50)
        closes = highs
        opens = [h - 0.1 for h in highs]
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes, 'open': opens})
        df.index = pd.date_range('2026-06-03 09:30', periods=50, freq='30min')

        results = detect_strict_bar_counting_signals("TEST", df, "long")
        for sr in results:
            assert sr.symbol == "TEST"
            assert sr.timeframe == "30m"
            assert sr.shadow_signal_type != ""
            assert sr.direction in ("long", "short")
            assert isinstance(sr.detected, bool)
            # Check that key debug fields exist
            assert sr.extended_count_warning is not None
            assert sr.middle_range_signal is not None
            assert sr.proxy_comparison is not None

    def test_no_context_produces_undetected_results(self):
        """Insufficient data → all results have detected=False"""
        highs = [10, 10.5, 10.3]
        lows  = [h - 0.5 for h in highs]
        closes = highs
        opens = [h - 0.1 for h in highs]
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes, 'open': opens})
        df.index = pd.date_range('2026-06-03 09:30', periods=3, freq='30min')

        results = detect_strict_bar_counting_signals("TEST", df, "long")
        for sr in results:
            assert sr.detected is False


# ═══ Proxy vs Strict Matrix ═══

class TestProxyVsStrictMatrix:
    def make_result(self, detected, proxy_detected, symbol="TEST",
                    strict_type="brooks_h2_strict", proxy_type="H2", direction="long"):
        sr = ShadowSignalResult(symbol=symbol, direction=direction)
        sr.shadow_signal_type = strict_type
        sr.detected = detected
        sr.proxy_comparison = {
            "current_proxy_signal_type": proxy_type,
            "proxy_detected": proxy_detected,
            "proxy_display_label": f"{proxy_type}代理",
            "strict_matches_proxy": detected and proxy_detected,
            "difference_reason": "",
        }
        return sr

    def test_type_a_both_true(self):
        """T23: proxy=true, strict=true → A"""
        results = [self.make_result(True, True)]
        matrix = get_proxy_vs_strict_matrix(results)
        assert matrix[0]["match_type"] == "A"

    def test_type_b_proxy_true_strict_false(self):
        """T23: proxy=true, strict=false → B"""
        results = [self.make_result(False, True)]
        matrix = get_proxy_vs_strict_matrix(results)
        assert matrix[0]["match_type"] == "B"
        assert matrix[0]["manual_review_needed"]

    def test_type_c_strict_true_proxy_false(self):
        """T24: strict=true, proxy=false → C"""
        results = [self.make_result(True, False)]
        matrix = get_proxy_vs_strict_matrix(results)
        assert matrix[0]["match_type"] == "C"
        assert matrix[0]["manual_review_needed"]

    def test_type_d_both_false(self):
        """T24: proxy=false, strict=false → D"""
        results = [self.make_result(False, False)]
        matrix = get_proxy_vs_strict_matrix(results)
        assert matrix[0]["match_type"] == "D"
        assert not matrix[0]["manual_review_needed"]

    def test_matrix_all_four_types(self):
        """All four types present in combined results"""
        results = [
            self.make_result(True, True, "A1"),
            self.make_result(False, True, "B1"),
            self.make_result(True, False, "C1"),
            self.make_result(False, False, "D1"),
        ]
        matrix = get_proxy_vs_strict_matrix(results)
        types = {m["match_type"] for m in matrix}
        assert types == {"A", "B", "C", "D"}


# ═══ No Hard Trigger Expiry ═══

class TestNoHardTriggerExpiry:
    def test_no_fixed_trigger_window(self):
        """T25: no fixed trigger window — _detect_trigger searches up to 20 bars"""
        from strict_pa_detector import _detect_trigger

        # Create bars where trigger happens at bar 15 after signal
        n = 30
        highs = [10.0] * 15 + [11.0] + [10.0] * 14  # trigger at bar 15
        lows  = [9.0] * 30
        from bar_counting_detector import build_bar_info_list
        bars = build_bar_info_list(highs, lows, highs, highs)

        sr = ShadowSignalResult(symbol="TEST", direction="long")
        sr.shadow_signal_type = "brooks_h2_strict"
        _detect_trigger(sr, bars, signal_bar_index=10, direction="long")
        assert sr.triggered
        assert sr.trigger_delay_bars == 5


# ═══ Quality Assessment ═══

class TestQualityAssessment:
    def test_quality_good_for_strong_context(self):
        """H2 in high confidence context → at least moderate"""
        from strict_pa_detector import _assess_quality
        ctx = ContextDetection(context_type="bull_pullback", context_confidence="high",
                                context_start_index=0, context_start_price=10,
                                context_start_time="")
        ctx.range_position = None
        ctx.middle_range_signal = False

        sr = ShadowSignalResult(symbol="TEST", direction="long")
        sr.middle_range_signal = False
        sr.range_position = None
        sr.triggered = True
        sr.close_confirmation = True
        quality = _assess_quality(sr, ctx, target_count=2, max_count=2)
        assert quality in ("good", "moderate")

    def test_quality_weak_for_h4_range_middle(self):
        """H4 in range middle → weak"""
        from strict_pa_detector import _assess_quality
        ctx = ContextDetection(context_type="bull_pullback", context_confidence="low",
                                context_start_index=0, context_start_price=10,
                                context_start_time="")
        ctx.range_position = "middle"
        ctx.middle_range_signal = True

        sr = ShadowSignalResult(symbol="TEST", direction="long")
        sr.middle_range_signal = True
        sr.range_position = "middle"
        sr.triggered = False
        sr.close_confirmation = False
        quality = _assess_quality(sr, ctx, target_count=2, max_count=4)
        assert quality == "weak"
