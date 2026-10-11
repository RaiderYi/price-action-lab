#!/usr/bin/env python3
"""
P5 证据真实性校验器测试
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails
from evidence_verifier import verify_evidence, EvidenceVerification


class TestPriceConsistency(unittest.TestCase):
    """价格字段方向一致性。"""

    def test_short_stop_below_entry_reject(self):
        """做空 stop < entry → REJECT。"""
        s = apply_guardrails(ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=95, llm_tp1=90,
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={"counter_evidence": "none"},
            invalid_condition="x",
        ))
        self.assertEqual(s.final_grade, "REJECT")

    def test_long_stop_above_entry_reject(self):
        """做多 stop > entry → REJECT。"""
        s = apply_guardrails(ScoredSignal(
            symbol="T", signal_type="H2", direction="long", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=105, llm_tp1=110,
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={"counter_evidence": "none"},
            invalid_condition="x",
        ))
        self.assertEqual(s.final_grade, "REJECT")

    def test_short_tp_above_entry_reject(self):
        """做空 tp1 > entry → REJECT。"""
        s = apply_guardrails(ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=105, llm_tp1=110,
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={"counter_evidence": "none"},
            invalid_condition="x",
        ))
        self.assertEqual(s.final_grade, "REJECT")


class TestRRRecomputation(unittest.TestCase):
    """RR 重算校验。"""

    def test_rr_recalc_diff_small_ok(self):
        """RR 重算差异小 → 不影响等级。"""
        s = apply_guardrails(ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=102, llm_tp1=97,
            # RR=3/2=1.5
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 103, "prior_low": 97,
                "trigger_bar": "x", "confirmation": "x",
                "counter_evidence": "双底风险 at 98.5",
            },
            invalid_condition="回到102",
        ))
        # RR=1.5, 做空 ≥1.5 → 应能通过 RR 检查
        self.assertNotEqual(s.final_grade, "REJECT")

    def test_rr_recalc_diff_large_downgrade(self):
        """RR 重算差异大 → 降级。"""
        s = apply_guardrails(ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=100, llm_stop_loss=105, llm_tp1=97,
            # 真实 RR=(100-97)/(105-100)=3/5=0.6
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 110, "LH2": 108, "prior_low": 95,
                "trigger_bar": "x", "confirmation": "x",
                "counter_evidence": "可能双底 at 99",
            },
            invalid_condition="回到105",
        ))
        # RR=0.6 → REJECT (RR<1.0)
        self.assertEqual(s.final_grade, "REJECT")


class TestCounterEvidenceQuality(unittest.TestCase):
    """Counter evidence 质量。"""

    def test_specific_counter_evidence(self):
        """有具体价格位的 counter_evidence → specific。"""
        v = verify_evidence("L2", "short", 100, 102, 97, 1.5, 0.02,
                           {"LH1": 105, "LH2": 103},
                           "48.45可能形成双底，若守住则做空失败", None)
        self.assertEqual(v.counter_evidence_quality, "specific")

    def test_generic_counter_evidence(self):
        """泛泛而谈 → generic。"""
        v = verify_evidence("L2", "short", 100, 102, 97, 1.5, 0.02,
                           {"LH1": 105, "LH2": 103},
                           "市场风险较大，需谨慎操作", None)
        self.assertEqual(v.counter_evidence_quality, "generic")

    def test_generic_counter_downgrades(self):
        """泛泛 counter_evidence → 最高 B。"""
        s = apply_guardrails(ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=98, llm_tp1=105,
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "x", "confirmation": "x",
                "counter_evidence": "市场风险较大",  # 泛泛
            },
            invalid_condition="回到98",
        ))
        self.assertNotEqual(s.final_grade, "A",
                           f"泛泛 counter_evidence 不能 A: {s.final_grade}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
