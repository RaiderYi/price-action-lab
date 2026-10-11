#!/usr/bin/env python3
"""
P4 LLM 输出契约强约束测试

验证 guardrail 对字段缺失的检测能力。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails


class TestOutputContract(unittest.TestCase):
    """LLM 输出契约强约束。"""

    def _base(self, **kw):
        """基准完整信号。"""
        defaults = {
            "symbol": "TEST", "signal_type": "L2", "direction": "short",
            "market": "A股", "llm_entry_min": 100, "llm_entry_max": 100,
            "llm_stop_loss": 102, "llm_tp1": 96,
            "llm_score": 80, "llm_confidence": 0.8, "llm_position_pct": 0.02,
            "structure_evidence": {
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "Breakout above 3500 would invalidate",
            },
            "invalid_condition": "价格回到止损位上方",
        }
        defaults.update(kw)
        return apply_guardrails(ScoredSignal(**defaults))

    # ── 致命字段 ──

    def test_missing_signal_type_reject(self):
        s = self._base(signal_type="")
        self.assertEqual(s.final_grade, "REJECT")

    def test_missing_direction_reject(self):
        s = self._base(direction="")
        self.assertEqual(s.final_grade, "REJECT")

    def test_missing_entry_reject(self):
        s = self._base(llm_entry_min=0, llm_entry_max=0)
        self.assertEqual(s.final_grade, "REJECT")

    def test_missing_stop_loss_reject(self):
        s = self._base(llm_stop_loss=0)
        self.assertEqual(s.final_grade, "REJECT")

    # ── 降级字段 ──

    def test_missing_invalid_condition_max_C(self):
        s = self._base(invalid_condition="")
        self.assertIn(s.final_grade, ("C", "D", "REJECT"))

    def test_missing_structure_evidence_incomplete(self):
        s = self._base(structure_evidence={})
        self.assertGreater(len(s.evidence_missing), 0)
        self.assertNotIn(s.final_grade, ("A", "B"))

    def test_missing_counter_evidence_not_A(self):
        s = self._base(structure_evidence={
            "LH1": 105, "LH2": 100, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            # 无 counter_evidence
        })
        self.assertNotEqual(s.final_grade, "A")

    # ── 完整字段 ──

    def test_complete_fields_rr_ok_watchlist(self):
        """完整字段 + RR合格 → WATCHLIST/FOCUS。"""
        s = self._base()
        self.assertIn(s.final_grade, ("A", "B"),
                     f"完整字段+RR合格应为A/B，实际 {s.final_grade}")

    def test_complete_fields_short_rr_low_max_C(self):
        """完整字段但 RR<1.5 做空 → 最高 C。"""
        s = apply_guardrails(ScoredSignal(
            symbol="TEST", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=101.5, llm_tp1=99.5,
            # RR=(100.5-99.5)/(101.5-100.5)=1.0/1.0=1.0
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "Breakout above 3500 would invalidate",
            },
            invalid_condition="价格回到止损位上方",
        ))
        self.assertIn(s.final_grade, ("C", "D", "REJECT"),
                     f"完整字段但 RR=1.0 做空应≤C，实际 {s.final_grade}")

    def test_complete_fields_lh2_gt_lh1_low_quality(self):
        """完整字段但 LH2>LH1 → LOW_QUALITY。"""
        s = self._base(structure_evidence={
            "LH1": 100, "LH2": 103, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "counter_evidence": "可能出现双底",
        })
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST"),
                        f"LH2>LH1 不应 FOCUS/WATCHLIST: {s.label}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
