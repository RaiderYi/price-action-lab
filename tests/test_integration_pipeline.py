#!/usr/bin/env python3
"""
P1 集成测试: LLM JSON → guardrail → final signal output 全链路

覆盖:
  1. RR=1.29 做空不能进 A/B
  2. LH2>LH1 的 L2 不能标记为 standard_L2
  3. REJECT 信号写入 audit_log (log_reject)
  4. A/B/C/D/REJECT 的状态标签一致
  5. 旧报告 9 信号全量降级验证
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import (
    ScoredSignal, apply_guardrails, log_reject, clear_reject_log,
    get_reject_log, grade_to_label,
)


class TestFullPipeline(unittest.TestCase):
    """LLM JSON → guardrail → output 全链路测试。"""

    def setUp(self):
        clear_reject_log()

    # ── RR 硬约束 ──

    def test_rr_1_29_short_cannot_be_A_or_B(self):
        """RR=1.29 做空信号不能进入 A/B。"""
        s = ScoredSignal(
            symbol="300442", signal_type="L2", direction="short", market="A股",
            llm_entry_min=84.0, llm_entry_max=84.5, llm_stop_loss=86.0,
            llm_tp1=82.0, llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 94.84, "LH2": 90.10, "prior_low": 84.0,
                "trigger_bar": "bear_engulfing", "confirmation": "break_low",
                "counter_evidence": "日线可能形成双底",
            },
            invalid_condition="价格回升到86.0上方",
        )
        s = apply_guardrails(s)
        self.assertNotIn(s.final_grade, ("A", "B"),
                        f"RR=1.29 做空不应为 A/B，实际 {s.final_grade}")
        self.assertIn(s.label, ("OBSERVE", "LOW_QUALITY", "REJECT"),
                      f"RR<1.5 做空应 OBSERVE/LOW_QUALITY/REJECT，实际 {s.label}")

    # ── L2 结构 ──

    def test_lh2_gt_lh1_not_standard_l2(self):
        """LH2 > LH1 的 L2 不能标记为 standard_L2。"""
        s = ScoredSignal(
            symbol="601899", signal_type="L2", direction="short", market="A股",
            llm_entry_min=30.4, llm_entry_max=30.6, llm_stop_loss=31.0,
            llm_tp1=29.9, llm_score=75, llm_confidence=0.75, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 32.0, "LH2": 32.98,  # ❌ LH2 > LH1
                "prior_low": 29.88, "trigger_bar": "bear_bar",
                "confirmation": "break_low",
            },
            invalid_condition="价格回到32.0上方",
        )
        s = apply_guardrails(s)
        self.assertNotEqual(s.signal_variant, "standard_L2",
                           f"LH2>LH1 不应是 standard_L2，实际 {s.signal_variant}")
        self.assertIn(s.signal_variant, ("invalid_or_weak_L2", "weak_L2"))
        self.assertNotIn(s.final_grade, ("A", "B"),
                        f"invalid L2 不应为 A/B，实际 {s.final_grade}")

    def test_lh2_lt_lh1_standard_l2(self):
        """LH2 < LH1 的 L2 应为 standard_L2。"""
        s = ScoredSignal(
            symbol="300442", signal_type="L2", direction="short", market="A股",
            llm_entry_min=84.0, llm_entry_max=84.5, llm_stop_loss=86.0,
            llm_tp1=82.0, llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 94.84, "LH2": 90.10, "prior_low": 84.0,
                "trigger_bar": "bear_engulfing", "confirmation": "break_low",
            },
            invalid_condition="价格回升到86.0上方",
        )
        s = apply_guardrails(s)
        self.assertEqual(s.signal_variant, "standard_L2")

    # ── REJECT 审计日志 ──

    def test_reject_goes_to_audit_log(self):
        """REJECT 信号通过 log_reject() 写入审计日志。"""
        s = ScoredSignal(
            symbol="600050", signal_type="L2", direction="short", market="A股",
            llm_entry_min=4.32, llm_entry_max=4.34, llm_stop_loss=4.40,
            llm_tp1=4.28, llm_score=70, llm_confidence=0.7, llm_position_pct=0.02,
        )
        s = apply_guardrails(s)
        self.assertEqual(s.final_grade, "REJECT")

        # 模拟 run_strategy.py 的行为
        log_reject(s)
        rl = get_reject_log()
        self.assertEqual(len(rl), 1, "REJECT 信号应写入审计日志")
        self.assertEqual(rl[0]["symbol"], "600050")
        self.assertIn("rr", rl[0])

        clear_reject_log()
        self.assertEqual(len(get_reject_log()), 0, "清空后应为 0")

    # ── 状态标签一致性 ──

    def test_grade_label_consistency(self):
        """验证 grade→label 映射一致性。"""
        from rule_guardrail import ScoredSignal, apply_guardrails
        
        # A 级: 完美信号（使用 score=75 避免触发临时置信度上限规则）
        s = ScoredSignal(
            symbol="TEST", signal_type="H2", direction="long", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=98,
            llm_tp1=105, llm_score=75, llm_confidence=0.75, llm_position_pct=0.02,
            # RR=(104.5-100.5)/(100.5-98)=4.0/2.5=1.6 ≥ 1.5 ✓
            # score=75 < 80 不触发 confidence_cap
            structure_evidence={
                "HL1": 95, "HL2": 97, "prior_high": 106,
                "trigger_bar": "bull_bar", "confirmation": "break_high",
                "counter_evidence": "可能出现双顶",
            },
            invalid_condition="跌破 HL2 则信号失效",
        )
        s = apply_guardrails(s)
        self.assertEqual(s.final_grade, "A")
        self.assertEqual(s.label, "FOCUS")
        self.assertEqual(s.position_suggestion, "normal")

        # C 级: RR 不达标做空信号
        s2 = ScoredSignal(
            symbol="TEST2", signal_type="L2", direction="short", market="A股",
            llm_entry_min=100, llm_entry_max=101, llm_stop_loss=102,
            llm_tp1=98.5, llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 105, "LH2": 103, "prior_low": 98,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "可能形成双底",
            },
            invalid_condition="价格回到 102 上方",
        )
        s2 = apply_guardrails(s2)
        self.assertEqual(s2.final_grade, "C")
        self.assertEqual(s2.label, "OBSERVE")
        self.assertEqual(s2.position_suggestion, "half")

    # ── 旧报告全量降级 ──

    def test_old_report_9_signals_all_downgraded(self):
        """旧报告中 9 个 L2 信号应全部被降级（无 A/B）。"""
        old_signals = [
            ("600276", 48.90, 49.60, 48.00, 50.17, 51.30),   # LH2>LH1
            ("601899", 30.50, 31.00, 29.90, 32.00, 32.98),   # LH2>LH1
            ("300442", 84.25, 86.00, 82.00, 94.84, 90.10),
            ("300059", 19.05, 19.40, 18.70, 20.25, 20.19),
            ("600050", 4.33,  4.40,  4.28,  4.48,  4.45),
            ("600030", 25.35, 25.80, 24.90, 26.68, 26.15),
            ("601179", 16.25, 16.60, 15.90, 17.02, 16.87),
            ("BTCUSDT",74150,74600,73800,75502,75415),
            ("ETHUSDT",2015, 2030, 2000, 2079, 2066),
        ]

        grades = {}
        for sym, entry, sl, tp1, lh1, lh2 in old_signals:
            market = "crypto" if sym in ("BTCUSDT", "ETHUSDT") else "A股"
            s = ScoredSignal(
                symbol=sym, signal_type="L2", direction="short", market=market,
                llm_entry_min=entry-0.05, llm_entry_max=entry+0.05,
                llm_stop_loss=sl, llm_tp1=tp1, llm_score=80, llm_confidence=0.8,
                llm_position_pct=0.02 if market == "A股" else 0.01,
                structure_evidence={
                    "LH1": lh1, "LH2": lh2, "prior_low": tp1,
                    "trigger_bar": "bear_bar", "confirmation": "break_low",
                },
                invalid_condition=f"价格回到{sl}上方",
            )
            s = apply_guardrails(s)
            grades[s.final_grade] = grades.get(s.final_grade, 0) + 1

        self.assertEqual(grades.get("A", 0), 0, "旧报告不应有 A 级信号")
        self.assertEqual(grades.get("B", 0), 0, "旧报告不应有 B 级信号")
        self.assertGreater(grades.get("C", 0) + grades.get("D", 0) + grades.get("REJECT", 0),
                          0, "至少应有 C/D/REJECT 级别的降级信号")


if __name__ == "__main__":
    unittest.main(verbosity=2)
