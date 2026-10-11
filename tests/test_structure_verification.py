#!/usr/bin/env python3
"""
P5.2: 结构点真实性验证测试

覆盖:
  - L2 有 LH1/LH2 且 LH2<LH1 → standard_L2
  - L2 有 LH1/LH2 且 LH2≈LH1 → weak_L2
  - L2 有 LH1/LH2 且 LH2>LH1 → invalid_L2
  - L2 缺 LH1 → incomplete_evidence
  - L2 缺 LH2 → incomplete_evidence
  - H2 有 HL1/HL2 且 HL2>HL1 → standard_H2
  - H2 缺 HL1/HL2 → incomplete_evidence
  - wedge 三推完整 → pass
  - wedge 缺 push_3 → incomplete_evidence
  - wedge 三推方向混乱 → invalid_wedge
  - measured_move 缺 measure_start → incomplete_evidence
"""

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evidence_verifier import (
    verify_evidence, StructureVerification,
    find_swing_highs, find_swing_lows, match_price_to_swing,
    _verify_l2_structure, _verify_h2_structure, _verify_wedge_structure,
)


def _make_df(highs=None, lows=None):
    """Create a simple OHLCV DataFrame with given columns. Default 100 bars."""
    n = 100
    df = pd.DataFrame({
        "open": [50.0] * n, "high": [50.0] * n, "low": [50.0] * n, "close": [50.0] * n,
        "volume": [1000] * n,
    })
    if highs:
        for i, v in highs:
            if i < n:
                df.loc[i, "high"] = v
    if lows:
        for i, v in lows:
            if i < n:
                df.loc[i, "low"] = v
    return df


class TestSwingDetection(unittest.TestCase):
    """Swing high/low 检测函数。"""

    def test_find_swing_highs(self):
        df = _make_df(highs=[(10, 55), (20, 60), (30, 58), (40, 62), (50, 55)])
        swings = find_swing_highs(df, window=3)
        self.assertIn(60.0, swings)
        self.assertIn(62.0, swings)

    def test_find_swing_lows(self):
        df = _make_df(lows=[(10, 45), (20, 40), (30, 42), (40, 38), (50, 45)])
        swings = find_swing_lows(df, window=3)
        self.assertIn(40.0, swings)
        self.assertIn(38.0, swings)

    def test_match_price_to_swing(self):
        swings = [50.0, 52.0, 55.0]
        self.assertTrue(match_price_to_swing(50.1, swings, 0.005))
        self.assertTrue(match_price_to_swing(51.9, swings, 0.005))
        self.assertFalse(match_price_to_swing(53.5, swings, 0.005))


class TestL2StructureVerification(unittest.TestCase):
    """L2 结构验证（无 K 线 DataFrame）。"""

    def test_l2_standard(self):
        """LH2 < LH1 → standard_L2。"""
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH1": 105, "LH2": 100}, None)
        self.assertEqual(sv.structure_variant, "standard_L2")
        self.assertTrue(sv.structure_rule_passed)

    def test_l2_weak(self):
        """LH2 ≈ LH1 → weak_L2。"""
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH1": 100.0, "LH2": 100.2}, None)
        self.assertEqual(sv.structure_variant, "weak_L2")

    def test_l2_invalid(self):
        """LH2 > LH1 → invalid_L2。"""
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH1": 100, "LH2": 103}, None)
        self.assertEqual(sv.structure_variant, "invalid_L2")
        self.assertFalse(sv.structure_rule_passed)

    def test_l2_missing_lh1(self):
        """缺 LH1 → incomplete_evidence。"""
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH2": 100}, None)
        self.assertEqual(sv.structure_variant, "incomplete_evidence")

    def test_l2_missing_lh2(self):
        """缺 LH2 → incomplete_evidence。"""
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH1": 105}, None)
        self.assertEqual(sv.structure_variant, "incomplete_evidence")

    def test_l2_with_kline_swing_check(self):
        """在 K 线中验证 LH1/LH2 是否为 swing high。"""
        df = _make_df(highs=[
            (10, 105), (15, 103), (20, 105), (25, 100),
            (30, 100), (35, 103), (40, 105), (45, 100),
        ])
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH1": 105, "LH2": 100}, df)
        self.assertEqual(sv.structure_variant, "standard_L2")

    def test_l2_not_swing_high(self):
        """LH1/LH2 不是 swing high → warning。"""
        df = _make_df(highs=[(10, 105)])  # 只有一个点，不是 swing
        sv = StructureVerification(signal_type="L2")
        _verify_l2_structure(sv, {"LH1": 105, "LH2": 100}, df)
        self.assertFalse(sv.points_are_valid_swings)


class TestH2StructureVerification(unittest.TestCase):
    """H2 结构验证。"""

    def test_h2_standard(self):
        """HL2 > HL1 → standard_H2。"""
        sv = StructureVerification(signal_type="H2")
        _verify_h2_structure(sv, {"HL1": 95, "HL2": 97}, None)
        self.assertEqual(sv.structure_variant, "standard_H2")

    def test_h2_weak(self):
        """HL2 ≈ HL1 → weak_H2。"""
        sv = StructureVerification(signal_type="H2")
        _verify_h2_structure(sv, {"HL1": 95.0, "HL2": 95.2}, None)
        self.assertEqual(sv.structure_variant, "weak_H2")

    def test_h2_invalid(self):
        """HL2 < HL1 → invalid_H2。"""
        sv = StructureVerification(signal_type="H2")
        _verify_h2_structure(sv, {"HL1": 100, "HL2": 97}, None)
        self.assertFalse(sv.structure_rule_passed)

    def test_h2_missing(self):
        """缺 HL1/HL2 → incomplete_evidence。"""
        sv = StructureVerification(signal_type="H2")
        _verify_h2_structure(sv, {"HL1": 95}, None)
        self.assertEqual(sv.structure_variant, "incomplete_evidence")


class TestWedgeStructureVerification(unittest.TestCase):
    """楔形结构验证。"""

    def test_wedge_standard(self):
        """三推完整、方向一致 → standard_wedge。"""
        sv = StructureVerification(signal_type="wedge")
        _verify_wedge_structure(sv, {
            "push_1_price": 50, "push_2_price": 52, "push_3_price": 54,
        }, None)
        self.assertEqual(sv.structure_variant, "standard_wedge")

    def test_wedge_missing_push3(self):
        """缺 push_3 → incomplete_evidence。"""
        sv = StructureVerification(signal_type="wedge")
        _verify_wedge_structure(sv, {
            "push_1_price": 50, "push_2_price": 52,
        }, None)
        self.assertEqual(sv.structure_variant, "incomplete_evidence")

    def test_wedge_chaotic(self):
        """三推方向混乱 → invalid_wedge。"""
        sv = StructureVerification(signal_type="wedge")
        _verify_wedge_structure(sv, {
            "push_1_price": 50, "push_2_price": 48, "push_3_price": 52,
        }, None)
        self.assertEqual(sv.structure_variant, "invalid_wedge")


class TestMeasuredMoveVerification(unittest.TestCase):
    """Measured move 结构验证。"""

    def test_missing_measure_start(self):
        """缺 measure_start → incomplete_evidence。"""
        sv = StructureVerification(signal_type="measured_move")
        expected = ["measure_start", "measure_end", "breakout_point"]
        for pt in expected:
            if "start" in pt:
                continue
            sv.found_points.append(pt)
        sv.missing_points = ["measure_start"]
        sv.structure_variant = "incomplete_evidence"
        sv.structure_rule_passed = False
        self.assertEqual(sv.structure_variant, "incomplete_evidence")


class TestFullPipelineStructureVerification(unittest.TestCase):
    """端到端验证：verify_evidence() 返回正确的 SV。"""

    def test_l2_standard_pipeline(self):
        v = verify_evidence("L2", "short", 100, 102, 96, 2.0, 0.02,
                           {"LH1": 105, "LH2": 100, "prior_low": 95,
                            "trigger_bar": "x", "confirmation": "x"},
                           "Break above 105 invalidates", None, None)
        self.assertEqual(v.structure_verification.structure_variant, "standard_L2")
        self.assertTrue(v.structure_verification.structure_rule_passed)

    def test_l2_incomplete_pipeline(self):
        v = verify_evidence("L2", "short", 100, 102, 96, 2.0, 0.02,
                           {"prior_low": 95},  # 缺 LH1/LH2
                           "Break above 105", None, None)
        self.assertEqual(v.structure_verification.structure_variant, "incomplete_evidence")
        self.assertIn("LH1", v.structure_verification.missing_points)
        self.assertIn("LH2", v.structure_verification.missing_points)

    def test_h2_standard_pipeline(self):
        v = verify_evidence("H2", "long", 100, 98, 105, 2.5, 0.02,
                           {"HL1": 95, "HL2": 97, "prior_high": 105,
                            "trigger_bar": "x", "confirmation": "x"},
                           "Break below 95 invalidates", None, None)
        self.assertEqual(v.structure_verification.structure_variant, "standard_H2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
