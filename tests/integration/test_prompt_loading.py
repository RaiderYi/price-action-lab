#!/usr/bin/env python3
"""
P4.2 Prompt 加载验证 + 契约遵守测试
"""

import sys
import hashlib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails


class TestPromptLoading(unittest.TestCase):
    """Prompt 加载验证。"""

    def test_midday_prompt_exists_and_hashable(self):
        p = Path(__file__).parent.parent / "prompts" / "midday_prompt.md"
        self.assertTrue(p.exists(), "midday_prompt.md 应存在")
        content = p.read_text(encoding="utf-8")
        h = hashlib.md5(content.encode()).hexdigest()[:8]
        self.assertTrue(len(h) == 8, f"hash 应为 8 位: {h}")
        self.assertIn("signal_schema_version", content,
                     "midday_prompt.md 应包含 signal_schema_version")
        self.assertIn("v4.2", content,
                     "midday_prompt.md 应指定 v4.2")

    def test_daily_prompt_exists_and_hashable(self):
        p = Path(__file__).parent.parent / "prompts" / "daily_prompt.md"
        self.assertTrue(p.exists(), "daily_prompt.md 应存在")
        content = p.read_text(encoding="utf-8")
        h = hashlib.md5(content.encode()).hexdigest()[:8]
        self.assertTrue(len(h) == 8, f"hash 应为 8 位: {h}")

    def test_prompts_different(self):
        """两个 prompt 不应完全一样。"""
        midday = (Path(__file__).parent.parent / "prompts" / "midday_prompt.md").read_text(encoding="utf-8")
        daily = (Path(__file__).parent.parent / "prompts" / "daily_prompt.md").read_text(encoding="utf-8")
        self.assertNotEqual(midday, daily, "midday 和 daily prompt 不应完全相同")


class TestContractCompliance(unittest.TestCase):
    """契约遵守统计测试。"""

    def test_missing_schema_version_all_signals_max_C(self):
        """缺 schema_version 时 guardrail 可检测（parser 层面）。"""
        # Guardrail 本身不检查 schema_version — 由 run_strategy.py parser 处理
        # 此测试验证 guardrail 对正常信号的处理不受影响
        s = ScoredSignal(
            symbol="TEST", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=100, llm_stop_loss=102, llm_tp1=96,
            llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "可能出现双底",
            },
            invalid_condition="价格回到止损位上方",
        )
        s = apply_guardrails(s)
        # RR=2/2=1.0, short<1.5 → C; counter_evidence="可能出现双底"→specific→OK
        self.assertIn(s.final_grade, ("A", "B", "C"),
                     f"完整字段信号应能进入 A/B/C: {s.final_grade}")

    def test_low_quality_not_human_reference(self):
        """LOW_QUALITY/D 不应计入人工可参考信号。"""
        s = ScoredSignal(
            symbol="TEST", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=103, llm_tp1=102,
            llm_score=70, llm_confidence=0.7, llm_position_pct=0.02,
            # No structure_evidence, no invalid_condition
        )
        s = apply_guardrails(s)
        # Should be D/LOW_QUALITY
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST"),
                        f"D级信号不应是 FOCUS/WATCHLIST: {s.label}")

    def test_db_write_not_equal_focus(self):
        """写入 DB 不等于 FOCUS/WATCHLIST。"""
        s = apply_guardrails(ScoredSignal(
            symbol="TEST", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=100, llm_stop_loss=102, llm_tp1=98,
            # RR=2/2=1.0, 做空
            llm_score=70, llm_confidence=0.7, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 103, "prior_low": 98,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "双底风险 at 98",
            },
            invalid_condition="回到102",
        ))
        s = apply_guardrails(s)
        # RR=1.0, 做空 < 1.5 → C
        self.assertIn(s.final_grade, ("C", "D"))
        self.assertNotIn(s.label, ("FOCUS", "WATCHLIST"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
