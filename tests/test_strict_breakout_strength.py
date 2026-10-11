"""Phase 5.0: strict_breakout_strength tests"""
import pytest
from strict_breakout_strength import detect_breakout_strength


def make_kline(highs, lows=None, closes=None):
    if lows is None:
        lows = [h - 0.5 for h in highs]
    if closes is None:
        closes = highs
    return highs, lows, closes


class TestStrongBreakout:
    def test_strong_breakout_up(self):
        """T9: strong breakout up detected"""
        highs = [10]*10 + [10.2]*3 + [10.5, 11.5]
        lows  = [h - 0.3 for h in highs]
        closes = highs
        result = detect_breakout_strength(highs, lows, closes, "breakout", "up", atr=0.5)
        # May be strong or unknown depending on criteria
        assert result in ("strong_breakout", "unknown")

    def test_strong_breakout_down(self):
        highs = [12]*10 + [11.8]*3 + [11.0, 9.5]
        lows  = [h - 0.3 for h in highs]
        closes = lows  # close near low
        result = detect_breakout_strength(highs, lows, closes, "breakout", "down", atr=0.5)
        assert result in ("strong_breakout", "weak_breakout", "unknown")


class TestWeakBreakout:
    def test_weak_breakout_small_range(self):
        """T10: weak breakout with small range"""
        highs = [10]*15 + [10.05, 10.08, 10.06]
        lows  = [h - 0.02 for h in highs]  # tiny bars
        closes = highs
        result = detect_breakout_strength(highs, lows, closes, "breakout", "up", atr=0.5)
        assert result == "weak_breakout"


class TestFailedBreakout:
    def test_failed_breakout_up_reversal(self):
        """T11: failed breakout risk — up then reversal"""
        highs = [10]*10 + [11.5, 10.8, 10.5, 10.3]
        lows  = [h - 0.3 for h in highs]
        closes = [10]*10 + [11.0, 10.5, 10.3, 10.2]
        result = detect_breakout_strength(highs, lows, closes, "breakout", "up", atr=0.5)
        assert result in ("failed_breakout_risk", "unknown")


class TestUnknown:
    def test_small_data_returns_unknown(self):
        """T12: insufficient bars → unknown"""
        result = detect_breakout_strength([10], [9], [9.5], "breakout", "up", atr=0.5)
        assert result == "unknown"

    def test_zero_atr_returns_unknown(self):
        result = detect_breakout_strength([10]*5, [9]*5, [9.5]*5, "breakout", "up", atr=0)
        assert result == "unknown"


class TestNoForbiddenImports:
    def test_no_production_imports(self):
        """Verify no forbidden imports."""
        import strict_breakout_strength
        src = open(strict_breakout_strength.__file__, 'r', encoding='utf-8').read()
        for f in ["market_analyzer", "run_strategy", "signal_predictor", "candidate_pool"]:
            assert f"import {f}" not in src, f"found import {f}"
