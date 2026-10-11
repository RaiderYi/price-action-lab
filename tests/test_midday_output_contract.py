#!/usr/bin/env python3
"""
P4.1 午间模式输出契约测试

验证 midday 信号与 daily 信号使用相同的 guardrail 契约。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails


class TestMiddayOutputContract(unittest.TestCase):
    """午间模式信号契约 — 与 daily 共用 guardrail。"""

    def _signal(self, **kw):
        defaults = {
            "symbol": "TEST", "signal_type": "L2", "direction": "short",
            "market": "A股", "llm_entry_min": 100, "llm_entry_max": 100,
            "llm_stop_loss": 102, "llm_tp1": 96, "llm_score": 80,
            "llm_confidence": 0.8, "llm_position_pct": 0.02,
            "invalid_condition": "价格回到止损位上方",
            "structure_evidence": {
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "可能出现双底 at 95",
            },
        }
        defaults.update(kw)
        return apply_guardrails(ScoredSignal(**defaults))

    def test_midday_rr_below_1_reject(self):
        """午间 RR<1.0 → REJECT。"""
        s = self._signal(llm_stop_loss=104, llm_tp1=99)  # RR=(100-99)/(104-100)=1/4=0.25
        self.assertEqual(s.final_grade, "REJECT")

    def test_midday_missing_evidence_not_focus(self):
        """午间缺 structure_evidence → 不能 FOCUS/WATCHLIST。"""
        s = self._signal(structure_evidence={})
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST"))

    def test_midday_missing_invalid_condition_max_C(self):
        """午间缺 invalid_condition → 最高 C。"""
        s = self._signal(invalid_condition="")
        self.assertIn(s.final_grade, ("C", "D", "REJECT"))

    def test_midday_missing_counter_evidence_not_A(self):
        """午间缺 counter_evidence → 不能 A。"""
        s = apply_guardrails(ScoredSignal(
            symbol="TEST", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=98, llm_tp1=105,
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                # 无 counter_evidence
            },
            invalid_condition="价格回到止损位上方",
        ))
        self.assertNotEqual(s.final_grade, "A")

    def test_midday_complete_signal_ok(self):
        """午间完整字段 + RR达标 → 可进入 WATCHLIST/FOCUS。"""
        s = self._signal()
        self.assertIn(s.final_grade, ("A", "B"),
                     f"完整午间信号应为 A/B，实际 {s.final_grade}")

    def test_midday_complete_but_rr_low_max_C(self):
        """午间完整字段但 RR<1.5 做空 → 最高 C。"""
        s = self._signal(llm_stop_loss=104, llm_tp1=95)  # RR=(100-95)/(104-100)=5/4=1.25
        self.assertIn(s.final_grade, ("C", "D", "REJECT"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
