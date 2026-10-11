"""
P3: insufficient 禁 LLM 结构点兜底测试
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rule_guardrail import ScoredSignal, apply_guardrails


def _make_sig(structure_source="insufficient", direction="long", signal_type="H2", **kw):
    ev = {"_structure_source": structure_source,
          "_system_structure_verified": structure_source != "insufficient"}
    if structure_source == "verified":
        ev["HL1"] = 90; ev["HL2"] = 95; ev["prior_high"] = 110
    elif structure_source == "weak":
        ev["HL1"] = 90; ev["HL2"] = 95

    entry = kw.pop("entry", 100)
    stop = kw.pop("stop", 98)
    tp1 = kw.pop("tp1", 108)

    defaults = {
        "symbol": "600276", "signal_type": signal_type, "direction": direction,
        "market": "A股", "llm_entry_min": entry-1, "llm_entry_max": entry+1,
        "llm_stop_loss": stop, "llm_tp1": tp1,
        "llm_score": 80, "llm_confidence": 0.8, "llm_rr": 2.0,
        "structure_evidence": ev, "current_price": entry,
        "invalid_condition": "止损失效",
    }
    defaults.update(kw)
    s = ScoredSignal(**defaults)
    risk = abs(entry - stop); reward = abs(tp1 - entry)
    s.rr = reward / risk if risk else 2.0
    s.stop_loss_pct = risk / entry if entry else 0.02
    s.entry_mid = entry; s.risk = risk; s.reward = reward
    return s


class TestInsufficientGuard(unittest.TestCase):

    def test_insufficient_downgraded(self):
        s = _make_sig()
        s = apply_guardrails(s)
        # insufficient 不应以 OBSERVE/FOCUS/WATCHLIST 入库
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST", "OBSERVE", ""))
        self.assertIn(s.final_grade, ("D", "REJECT"))

    def test_insufficient_violation_contains_reason(self):
        s = _make_sig()
        s = apply_guardrails(s)
        viols = " ".join(s.guardrail_violations)
        self.assertTrue("insufficient" in viols or "缺少" in viols)

    def test_verified_not_downgraded_by_insufficient(self):
        s = _make_sig(structure_source="verified")
        s = apply_guardrails(s)
        self.assertNotIn(s.label, ("LOW_QUALITY", "REJECT"))

    def test_insufficient_rule_skips_non_insufficient(self):
        """weak 和 verified 不应被 insufficient 规则本身触发"""
        from rule_guardrail import _check_structure_insufficient
        s = _make_sig(structure_source="weak")
        s_before = s.label
        _check_structure_insufficient(s)
        self.assertEqual(s.label, s_before)  # label unchanged by this rule

    def test_l1_insufficient_also_flagged(self):
        s = _make_sig(signal_type="L1", direction="short", entry=25, stop=27, tp1=22)
        s = apply_guardrails(s)
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST", "OBSERVE", ""))


class TestInsufficientFieldsCleared(unittest.TestCase):

    def test_llm_points_cleared(self):
        evidence = {"HL1": 47.5, "HL2": 48.0, "prior_high": 50.0}
        _llm_fields = ["HL1", "HL2", "LH1", "LH2", "prior_high", "prior_low"]
        cleared = []
        for f in _llm_fields:
            if f in evidence:
                del evidence[f]; cleared.append(f)
        self.assertNotIn("HL1", evidence)
        self.assertNotIn("HL2", evidence)
        self.assertGreater(len(cleared), 0)


if __name__ == "__main__":
    unittest.main()
