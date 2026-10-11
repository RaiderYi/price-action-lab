"""Phase 5.0: strict_paper_price_model tests"""
import pytest
from strict_paper_price_model import (
    compute_ideal_entry, compute_realistic_entry, compute_stop_loss,
    compute_risk, compute_tp, build_paper_prices, check_atr_quality,
    get_execution_type, is_real_executable, A_SHARE_TICK,
)


class TestIdealEntry:
    def test_long_ideal_entry_high_plus_tick(self):
        """T1: long ideal_entry = signal_bar.high + tick"""
        assert compute_ideal_entry(10.50, 10.00, "long") == 10.51

    def test_short_ideal_entry_low_minus_tick(self):
        """T2: short ideal_entry = signal_bar.low - tick"""
        assert compute_ideal_entry(10.50, 10.00, "short") == 9.99


class TestRealisticEntry:
    def test_gap_up_long_uses_open(self):
        """T3: long gap up → realistic = trigger_bar.open"""
        assert compute_realistic_entry(10.51, 10.80, "long") == 10.80

    def test_gap_down_short_uses_open(self):
        """T4: short gap down → realistic = trigger_bar.open"""
        assert compute_realistic_entry(9.99, 9.70, "short") == 9.70

    def test_no_gap_long_uses_ideal(self):
        assert compute_realistic_entry(10.51, 10.40, "long") == 10.51

    def test_no_gap_short_uses_ideal(self):
        assert compute_realistic_entry(9.99, 10.10, "short") == 9.99


class TestStopLoss:
    def test_long_stop_low_minus_tick(self):
        """T5: long stop = signal_bar.low - tick"""
        assert compute_stop_loss(10.50, 10.00, "long") == 9.99

    def test_short_stop_high_plus_tick(self):
        """T6: short stop = signal_bar.high + tick"""
        assert compute_stop_loss(10.50, 10.00, "short") == 10.51


class TestTP:
    def test_tp1_1r_tp2_2r_long(self):
        """T7: TP1=1R, TP2=2R"""
        entry = 10.51; stop = 9.99; risk = 0.52
        assert compute_tp(entry, risk, 1.0, "long") == round(10.51 + 0.52, 2)
        assert compute_tp(entry, risk, 2.0, "long") == round(10.51 + 1.04, 2)

    def test_tp1_1r_tp2_2r_short(self):
        entry = 9.99; stop = 10.51; risk = 0.52
        assert compute_tp(entry, risk, 1.0, "short") == 9.47
        assert compute_tp(entry, risk, 2.0, "short") == 8.95


class TestInvalidRisk:
    def test_risk_zero_or_negative_invalid(self):
        """T8: risk_abs <= 0 → invalid (tick=0 forces zero risk)"""
        r = build_paper_prices(10.00, 10.00, "long", tick=0.0)
        assert r["invalid_risk"]
        assert r["risk_abs"] == 0.0

    def test_valid_risk_not_invalid(self):
        result = build_paper_prices(10.50, 10.00, "long")
        assert not result["invalid_risk"]
        assert result["risk_abs"] > 0


class TestBuildPrices:
    def test_full_price_set_long(self):
        result = build_paper_prices(10.50, 10.00, "long")
        assert result["ideal_entry"] == 10.51
        assert result["stop_loss"] == 9.99
        assert result["risk_abs"] == 0.52
        assert result["tp1"] == 11.03
        assert result["tp2"] == 11.55

    def test_full_price_set_short(self):
        result = build_paper_prices(10.50, 10.00, "short")
        assert result["ideal_entry"] == 9.99
        assert result["stop_loss"] == 10.51
        assert result["risk_abs"] == 0.52
        assert result["tp1"] == 9.47
        assert result["tp2"] == 8.95


class TestATRQuality:
    def test_atr_zero_flags(self):
        flags = check_atr_quality(0, 0.5)
        assert "atr_unavailable" in flags

    def test_tight_stop_flags(self):
        flags = check_atr_quality(1.0, 0.2)
        assert "stop_very_tight_vs_atr" in flags

    def test_normal_stop_no_flag(self):
        flags = check_atr_quality(0.5, 0.5)
        assert len(flags) <= 1  # at most moderate flag


class TestExecutionType:
    def test_a_share_short_hedge(self):
        """T9/T21: A股 short → hedge_reference"""
        assert get_execution_type("short", "A_share") == "hedge_reference"
        assert not is_real_executable("short", "A_share")

    def test_a_share_long_paper_trade(self):
        """T10: A股 long → paper_trade"""
        assert get_execution_type("long", "A_share") == "paper_trade"
        assert is_real_executable("long", "A_share")
