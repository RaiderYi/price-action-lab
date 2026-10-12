"""P7.4: 系统结构点接管测试"""
import pytest, sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from system_structure_builder import (build_structure_points,
                                       validate_structure_points_kline,
                                       _detect_swings)


def make_kline(highs, lows, closes=None):
    if closes is None:
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({'high': highs, 'low': lows, 'close': closes})


class TestSwingDetection:
    def test_detect_swing_high_and_low(self):
        highs = [10, 11, 12, 15, 13, 12, 11, 10]*3 + [11, 12, 15, 13, 12, 11, 10]
        lows = [9, 10, 11, 14, 12, 11, 10, 9]*3 + [10, 11, 14, 12, 11, 10, 9]
        sh, sl = _detect_swings(np.array(highs), np.array(lows), window=3)
        assert len(sh) > 0
        assert len(sl) > 0


class TestH2Structure:
    def test_h2_with_swings(self):
        n = 80
        highs = 100 + np.abs(np.random.randn(n) * 3)
        lows = 100 - np.abs(np.random.randn(n) * 3)
        highs[40] = 108; highs[41] = 107
        lows[60] = 92; lows[61] = 93
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 100)
        assert r["structure_status"] == "verified"
        assert "HL1" in r["structure_points"]
        assert "HL2" in r["structure_points"]

    def test_h2_long_standard_higher_low_sequence(self):
        """最近两个 swing low 满足 HL2 > HL1 → 应由 evidence_verifier 判 standard"""
        n = 50
        highs = [105.0] * n
        lows  = [100.0] * n
        # 制造两个递增的 swing low
        lows[15] = 88.0   # HL1: 更早的 swing low, 更低 (倒 V 底)
        lows[35] = 92.0   # HL2: 更近的 swing low, 更高 (higher low)
        # 保证 window=4 的 swing 检测能识别
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 106.0)
        assert r["structure_status"] == "verified"
        hl1 = r["structure_points"]["HL1"]
        hl2 = r["structure_points"]["HL2"]
        assert hl1 < hl2, f"HL1({hl1}) should be < HL2({hl2}) for higher low sequence"

    def test_h2_long_falling_lows_preserved_for_verifier(self):
        """最近两个 swing low 下降 (HL2 < HL1) → 不跳过, 保留给 verifier 判 invalid"""
        n = 50
        highs = [105.0] * n
        lows  = [100.0] * n
        # 最近两个 swing low 下降: HL2 < HL1
        lows[15] = 92.0   # HL1: 更早的 swing low, 更高 (higher)
        lows[35] = 88.0   # HL2: 更近的 swing low, 更低 (lower → 下降)
        # 更早还有一个 swing low: lows[5]=85.0 — 不应被选中
        lows[5]  = 85.0
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 106.0)
        assert r["structure_status"] in ("verified", "weak")
        hl1 = r["structure_points"]["HL1"]
        hl2 = r["structure_points"]["HL2"]
        # HL2 < HL1 → 保留下降关系, 不跳过
        assert hl2 < hl1, f"HL2({hl2}) should be < HL1({hl1}) — verifier should catch as invalid"
        # HL1 不应等于 85.0（更早的 low）— 必须是紧邻的前一个
        assert hl1 != 85.0, f"HL1({hl1}) should NOT skip to earlier low(85.0)"

    def test_h2_long_insufficient_with_one_swing_low(self):
        """只有一个 swing low 时返回 insufficient"""
        n = 50
        highs = [105.0] * n
        lows  = [100.0] * n
        lows[30] = 95.0   # 唯一一个 swing low
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 106.0)
        assert r["structure_status"] == "insufficient"
        assert "HL1/HL2" in str(r.get("missing_points", []))

    def test_h2_insufficient_short_kline(self):
        df = make_kline([10]*10, [9]*10)
        r = build_structure_points("X", "H2", "long", df, 10)
        assert r["structure_status"] == "insufficient"

    def test_h2_hl2_above_cp_is_invalid(self):
        n = 80
        highs = 50 + np.abs(np.random.randn(n))
        lows = 50 - np.abs(np.random.randn(n))
        lows[70] = 49; lows[71] = 50  # HL2 near cp
        highs[50] = 55
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 51)
        # HL2 should be below current price for long
        if r["structure_status"] != "insufficient":
            assert r["structure_points"].get("HL2", 999) < 51

    def test_h2_long_outputs_prior_high(self):
        """H2 long 应输出 prior_high: 最近一个高于 cp 的 swing high"""
        n = 50
        highs = [105.0] * n
        lows  = [100.0] * n
        highs[25] = 115.0   # swing high above cp
        lows[20]  = 88.0
        lows[40]  = 92.0
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 106.0)
        assert r["structure_status"] == "verified"
        assert "prior_high" in r["structure_points"]
        assert r["structure_points"]["prior_high"] > 106.0

    def test_h2_long_no_prior_high_when_none_above_cp(self):
        """无上方 swing high 时不输出 prior_high"""
        n = 50
        highs = [105.0] * n
        lows  = [100.0] * n
        lows[20] = 88.0
        lows[40] = 92.0
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 120.0)
        if r["structure_status"] != "insufficient":
            assert "prior_high" not in r["structure_points"]


class TestRangeDetection:
    def test_tr_fade_with_range(self):
        highs = [53]*40 + [50]*10 + [47]*10  # Current near 47.5 (range low)
        lows = [49]*40 + [47]*10 + [46]*10
        df = make_kline(highs, lows)
        r = build_structure_points("X", "tr_fade", "long", df, 47.0)
        assert r["structure_status"] == "verified"
        assert "range_high" in r["structure_points"]
        assert "range_low" in r["structure_points"]


class TestStructureValidation:
    def test_point_not_in_kline_invalid(self):
        invalid = validate_structure_points_kline(
            {"HL1": 9999, "HL2": 50},
            np.array([40, 42, 41, 40]),
            np.array([38, 39, 38, 38]),
            40)
        assert len(invalid) >= 1
        assert any("HL1" in i for i in invalid)

    def test_point_in_kline_valid(self):
        invalid = validate_structure_points_kline(
            {"HL1": 41, "HL2": 39},
            np.array([40, 42, 41, 40]),
            np.array([38, 39, 38, 38]),
            40)
        assert len(invalid) == 0


class TestSystemStructureIntegration:
    def test_no_kline_returns_insufficient(self):
        r = build_structure_points("X", "H2", "long", None, 100)
        assert r["structure_status"] == "insufficient"

    def test_structure_source_is_system(self):
        n = 80
        highs = 100 + np.abs(np.random.randn(n) * 2)
        lows = 100 - np.abs(np.random.randn(n) * 2)
        highs[30] = 106; lows[60] = 94
        df = make_kline(highs, lows)
        r = build_structure_points("X", "H2", "long", df, 100)
        assert "system" in r["structure_source"]
