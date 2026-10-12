#!/usr/bin/env python3
"""
P3 结构化证据 Schema 测试

覆盖:
  - L2 缺 LH1/LH2 → INCOMPLETE_EVIDENCE, 不是 standard_L2
  - L2 LH2>LH1 → LOW_QUALITY
  - L2 LH2<LH1 且 RR合格 → WATCHLIST/FOCUS
  - wedge 缺三推 → INCOMPLETE_EVIDENCE
  - double_bottom 缺二次测试 → INCOMPLETE_EVIDENCE
  - counter_evidence 缺失 → 不能 A 级
  - invalid_condition 缺失 → 最高 C
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails
from signal_registry import check_evidence_completeness


def _make(signal_type, direction, evidence=None, **kw):
    """快捷工厂。"""
    defaults = {
        "symbol": "TEST", "signal_type": signal_type, "direction": direction,
        "market": "A股", "llm_entry_min": 100, "llm_entry_max": 100,
        "llm_stop_loss": 102, "llm_tp1": 96,  # RR=2.0, short, 达标
        "llm_score": 80, "llm_confidence": 0.8, "llm_position_pct": 0.02,
        "structure_evidence": evidence or {},
        "invalid_condition": "价格突破止损位",
    }
    defaults.update(kw)
    s = ScoredSignal(**defaults)
    return apply_guardrails(s)


class TestEvidenceSchema(unittest.TestCase):
    """结构化证据 schema 测试。"""

    # ── L2 证据 ──

    def test_l2_missing_lh1_lh2_incomplete(self):
        """L2 缺少 LH1/LH2 → INCOMPLETE_EVIDENCE。"""
        s = _make("L2", "short", evidence={"counter_evidence": "Support at 95 could hold"})
        self.assertIn(s.label, ("INCOMPLETE_EVIDENCE", "LOW_QUALITY"),
                     f"缺 LH1/LH2 应 INCOMPLETE_EVIDENCE，实际 {s.label}")
        self.assertNotEqual(s.signal_variant, "standard_L2")
        self.assertGreater(len(s.evidence_missing), 0,
                          f"应有 evidence_missing: {s.evidence_missing}")

    def test_l2_lh2_gt_lh1_low_quality(self):
        """L2 LH2>LH1 → LOW_QUALITY。"""
        s = _make("L2", "short", evidence={
            "LH1": 100.0, "LH2": 103.0, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "counter_evidence": "Previous support at 95 may hold",
        })
        self.assertEqual(s.signal_variant, "invalid_or_weak_L2")
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST"),
                        f"LH2>LH1 不应 FOCUS/WATCHLIST: {s.label}")

    def test_l2_complete_rr_ok_watchlist(self):
        """L2 LH2<LH1 + RR≥1.5 + 证据全 → WATCHLIST 或以上。"""
        s = _make("L2", "short", evidence={
            "LH1": 105.0, "LH2": 100.0, "prior_low": 95,
            "trigger_bar": "bear_engulfing", "confirmation": "break_low",
            "counter_evidence": "Previous support at 95 may hold",
        })
        self.assertEqual(s.signal_variant, "standard_L2")
        self.assertIn(s.label, ("WATCHLIST", "FOCUS", "OBSERVE"))

    # ── Wedge 证据 ──

    def test_wedge_missing_pushes_incomplete(self):
        """wedge 缺三推数据 → INCOMPLETE_EVIDENCE。"""
        s = _make("wedge", "short", evidence={"counter_evidence": "Rebound risk at 50"})
        self.assertGreater(len(s.evidence_missing), 0)
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST"),
                         f"wedge 缺三推不应 FOCUS/WATCHLIST: {s.label}")
        self.assertNotEqual(s.signal_variant, "clear_wedge",
                           "缺推杆应不能 clear_wedge")

    def test_double_bottom_missing_second_test_incomplete(self):
        """double_bottom 缺第二次测试 → INCOMPLETE_EVIDENCE。"""
        s = _make("double_bottom", "long", evidence={"counter_evidence": "Bearish breakout at 30"},
                  llm_stop_loss=98, llm_tp1=105)
        self.assertGreater(len(s.evidence_missing), 0)

    # ── Counter evidence / invalid condition ──

    def test_missing_counter_evidence_max_B(self):
        """缺 counter_evidence → 不能 A 级。"""
        s = _make("L2", "short", evidence={
            "LH1": 105.0, "LH2": 100.0, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            # 故意不设 counter_evidence
        })
        self.assertNotEqual(s.final_grade, "A",
                           f"缺 counter_evidence 不能 A，实际 {s.final_grade}")

    def test_missing_invalid_condition_max_C(self):
        """缺 invalid_condition → 最高 C。"""
        s = _make("L2", "short", evidence={
            "LH1": 105.0, "LH2": 100.0, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "counter_evidence": "Support at 95 could hold",
        }, invalid_condition="")
        self.assertIn(s.final_grade, ("C", "D", "REJECT"),
                     f"缺 invalid_condition 最高 C，实际 {s.final_grade}")

    # ── Evidence completeness helper ──

    def test_check_evidence_completeness(self):
        """check_evidence_completeness 正确计算完整性。"""
        result = check_evidence_completeness("L2", {})
        self.assertFalse(result["complete"])
        self.assertGreater(len(result["missing_required"]), 0)

        result2 = check_evidence_completeness("L2", {
            "LH1": 105, "LH2": 100, "prior_low": 95,
            "trigger_bar": "x", "confirmation": "x",
        })
        self.assertTrue(result2["complete"])

    # ── Violation 分类 ──

    def test_violations_classified(self):
        """违规被正确分类为 hard/evidence/warning。"""
        s = _make("L2", "short", evidence={"counter_evidence": "Support at 95 could hold"},
                  llm_entry_min=100, llm_entry_max=100,
                  llm_stop_loss=103, llm_tp1=96.5)  # RR=1.17, short, correct prices
        self.assertGreater(len(s.hard_violations), 0,
                          f"RR=1.17 做空应有 hard_violations: {s.hard_violations}")
        self.assertGreater(len(s.evidence_missing), 0,
                          f"缺 LH1/LH2 应有 evidence_missing: {s.evidence_missing}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
