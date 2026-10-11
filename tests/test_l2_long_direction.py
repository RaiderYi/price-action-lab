"""
P2: _l2() long 分支方向审计测试

验证:
  - long: stop < entry, tp1 > entry, tp2 > entry
  - long: prior_high 作为 TP1，非 lh1 (swing low)
  - short: prior_low 作为 TP1 (已收口，不回归)
  - fallback 方向正确
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from system_price_builder import build_system_prices


class TestL2LongDirectionFix(unittest.TestCase):
    """_l2() long 分支方向正确性测试。"""

    def _build_long(self, lh1=90, lh2=95, cp=100, prior_high=110, **kw):
        se = {"LH1": lh1, "LH2": lh2}
        if prior_high:
            se["prior_high"] = prior_high
        se.update(kw)
        return build_system_prices("X", "L2", "long", cp, se)

    def _build_short(self, lh1=110, lh2=105, cp=100, prior_low=90, **kw):
        se = {"LH1": lh1, "LH2": lh2}
        if prior_low:
            se["prior_low"] = prior_low
        se.update(kw)
        return build_system_prices("X", "L2", "short", cp, se)

    # ── long 方向正确性 ──

    def test_long_stop_below_entry(self):
        r = self._build_long()
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertLess(r["stop_loss"], em, "long stop must be < entry_mid")

    def test_long_tp1_above_entry(self):
        r = self._build_long()
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertGreater(r["tp1"], em, "long tp1 must be > entry_mid")

    def test_long_tp2_above_entry(self):
        r = self._build_long()
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertGreater(r["tp2"], em, "long tp2 must be > entry_mid")

    def test_long_uses_prior_high_as_tp1(self):
        r = self._build_long(prior_high=115)
        self.assertAlmostEqual(r["tp1"], 115, delta=1,
            msg="long tp1 should use prior_high")

    def test_long_fallback_tp1_when_no_prior_high(self):
        r = self._build_long(prior_high=None)
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertGreater(r["tp1"], em, "fallback tp1 should be > entry")

    def test_long_rr_positive(self):
        r = self._build_long()
        self.assertGreater(r["execution_rr"], 0, "long RR should be positive")

    # ── short 已收口不回归 ──

    def test_short_stop_above_entry(self):
        r = self._build_short()
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertGreater(r["stop_loss"], em, "short stop must be > entry_mid")

    def test_short_tp1_below_entry(self):
        r = self._build_short()
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertLess(r["tp1"], em, "short tp1 must be < entry_mid")

    def test_short_uses_prior_low_as_tp1(self):
        r = self._build_short(prior_low=88)
        self.assertAlmostEqual(r["tp1"], 88, delta=1,
            msg="short tp1 should use prior_low (P0 fix)")

    # ── fallback 方向 ──

    def test_long_fallback_no_structure(self):
        r = build_system_prices("X", "L2", "long", 100, {})
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertLess(r["stop_loss"], em)
        self.assertGreater(r["tp1"], em)

    def test_short_fallback_no_structure(self):
        r = build_system_prices("X", "L2", "short", 100, {})
        em = (r["entry_min"] + r["entry_max"]) / 2
        self.assertGreater(r["stop_loss"], em)
        self.assertLess(r["tp1"], em)

    # ── L1 路由与 L2 一致 ──

    def test_l1_long_routes_same_as_l2(self):
        r1 = build_system_prices("X", "L1", "long", 100, {"LH1": 90, "LH2": 95, "prior_high": 110})
        r2 = build_system_prices("X", "L2", "long", 100, {"LH1": 90, "LH2": 95, "prior_high": 110})
        self.assertAlmostEqual(r1["tp1"], r2["tp1"], delta=1)

    def test_l1_short_routes_same_as_l2(self):
        r1 = build_system_prices("X", "L1", "short", 100, {"LH1": 110, "LH2": 105, "prior_low": 90})
        r2 = build_system_prices("X", "L2", "short", 100, {"LH1": 110, "LH2": 105, "prior_low": 90})
        self.assertAlmostEqual(r1["tp1"], r2["tp1"], delta=1)


if __name__ == "__main__":
    unittest.main()
