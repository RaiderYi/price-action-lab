#!/usr/bin/env python3
"""
P2 Regression Fixture: 确保未来修改不会让降级信号重新升回 A/B

固定 5 个真实历史信号作为 fixture，每次修改 guardrail 后必须通过。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails, clear_reject_log


# ═══════════════════════════════════════════════════════════════════
# Fixture: 历史报告中提取的 5 个真实信号
# ═══════════════════════════════════════════════════════════════════

FIXTURE_SIGNALS = [
    # 20260528: 600276 L2 sell, RR=1.29 (LLM评分85)
    {
        "symbol": "600276", "signal_type": "L2", "direction": "short",
        "entry_min": 48.80, "entry_max": 49.00, "stop": 49.60, "tp1": 48.00,
        "market": "A股", "llm_score": 85,
        "lh1": 50.17, "lh2": 51.30,  # LH2 > LH1 — INVALID L2!
    },
    # 20260528: 601899 L2 sell, RR=1.20 (LLM评分75, LH2>LH1)
    {
        "symbol": "601899", "signal_type": "L2", "direction": "short",
        "entry_min": 30.40, "entry_max": 30.60, "stop": 31.00, "tp1": 29.90,
        "market": "A股", "llm_score": 75,
        "lh1": 32.00, "lh2": 32.98,
    },
    # 20260528: 300442 L2 sell, RR=1.25 (LLM评分80, 标准L2)
    {
        "symbol": "300442", "signal_type": "L2", "direction": "short",
        "entry_min": 84.00, "entry_max": 84.50, "stop": 86.00, "tp1": 82.00,
        "market": "A股", "llm_score": 80,
        "lh1": 94.84, "lh2": 90.10,
    },
    # 20260528: 300059 L2 sell, RR=1.00 (LLM评分80)
    {
        "symbol": "300059", "signal_type": "L2", "direction": "short",
        "entry_min": 19.00, "entry_max": 19.10, "stop": 19.40, "tp1": 18.70,
        "market": "A股", "llm_score": 80,
        "lh1": 20.25, "lh2": 20.19,
    },
    # 20260528: 600030 L2 sell, RR=1.00 (LLM评分80)
    {
        "symbol": "600030", "signal_type": "L2", "direction": "short",
        "entry_min": 25.30, "entry_max": 25.40, "stop": 25.80, "tp1": 24.90,
        "market": "A股", "llm_score": 80,
        "lh1": 26.68, "lh2": 26.15,
    },
]


class TestRegressionFixture(unittest.TestCase):
    """回归测试: 历史信号降级不可逆转。"""

    def setUp(self):
        clear_reject_log()

    def test_all_signals_not_A_or_B(self):
        """全部 5 个信号都不应为 A/B（RR<1.5 做空）。"""
        for i, s in enumerate(FIXTURE_SIGNALS):
            scored = ScoredSignal(
                symbol=s["symbol"], signal_type=s["signal_type"],
                direction=s["direction"], market=s["market"],
                llm_entry_min=s["entry_min"], llm_entry_max=s["entry_max"],
                llm_stop_loss=s["stop"], llm_tp1=s["tp1"],
                llm_score=s["llm_score"], llm_confidence=0.8,
                llm_position_pct=0.02,
                structure_evidence={
                    "LH1": s["lh1"], "LH2": s["lh2"],
                    "prior_low": s["tp1"],
                    "trigger_bar": "bear_bar", "confirmation": "break_low",
                },
                invalid_condition="",
            )
            scored = apply_guardrails(scored)
            self.assertNotIn(scored.final_grade, ("A", "B"),
                           f"信号 #{i} ({s['symbol']}) RR={scored.rr:.2f} "
                           f"不应为 A/B，实际 {scored.final_grade}")

    def test_lh2_gt_lh1_signals_not_standard_l2(self):
        """LH2>LH1 的信号 (600276, 601899) 不应标记为 standard_L2。"""
        for s in FIXTURE_SIGNALS:
            if s["lh2"] <= s["lh1"]:
                continue
            scored = ScoredSignal(
                symbol=s["symbol"], signal_type=s["signal_type"],
                direction=s["direction"], market=s["market"],
                llm_entry_min=s["entry_min"], llm_entry_max=s["entry_max"],
                llm_stop_loss=s["stop"], llm_tp1=s["tp1"],
                llm_score=s["llm_score"], llm_confidence=0.8,
                llm_position_pct=0.02,
                structure_evidence={
                    "LH1": s["lh1"], "LH2": s["lh2"],
                    "prior_low": s["tp1"],
                },
                invalid_condition="",
            )
            scored = apply_guardrails(scored)
            self.assertNotEqual(scored.signal_variant, "standard_L2",
                              f"{s['symbol']} LH2={s['lh2']}>{s['lh1']}=LH1 "
                              f"不应为 standard_L2，实际 {scored.signal_variant}")

    def test_lh2_near_lh1_is_weak_l2(self):
        """LH2 ≈ LH1 (容差内) 应标记为 weak_L2。"""
        s = FIXTURE_SIGNALS[3]  # 300059: LH1=20.25, LH2=20.19, 差0.06 < 容差0.10
        scored = ScoredSignal(
            symbol=s["symbol"], signal_type=s["signal_type"],
            direction=s["direction"], market=s["market"],
            llm_entry_min=s["entry_min"], llm_entry_max=s["entry_max"],
            llm_stop_loss=s["stop"], llm_tp1=s["tp1"],
            llm_score=s["llm_score"], llm_confidence=0.8,
            llm_position_pct=0.02,
            structure_evidence={
                "LH1": s["lh1"], "LH2": s["lh2"],
                "prior_low": s["tp1"],
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "可能出现双底",
            },
            invalid_condition="价格回到止损位上方",
        )
        scored = apply_guardrails(scored)
        # LH2(20.19) 与 LH1(20.25) 差 0.06，在 0.10 容差内 → weak_L2
        self.assertEqual(scored.signal_variant, "weak_L2",
                       f"300059 LH2≈LH1 应为 weak_L2，实际 {scored.signal_variant}")

    def test_rr_1_29_short_never_A_or_B(self):
        """RR=1.29 做空信号永远不能回到 A/B——regression 核心断言。"""
        scored = ScoredSignal(
            symbol="600276", signal_type="L2", direction="short", market="A股",
            llm_entry_min=48.80, llm_entry_max=49.00, llm_stop_loss=49.60,
            llm_tp1=48.00, llm_score=85, llm_confidence=0.85, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 50.17, "LH2": 49.80,  # 故意给 LH2<LH1 (理想结构)
                "prior_low": 48.45,
                "trigger_bar": "bear_engulfing", "confirmation": "break_low",
                "counter_evidence": "48.45可能形成双底",
            },
            invalid_condition="价格回到49.60上方则信号失效",
        )
        scored = apply_guardrails(scored)
        # 即使结构完美(LH2<LH1, 证据齐全)，RR=1.29 做空也不能 A/B
        self.assertNotIn(scored.final_grade, ("A", "B"),
                       f"结构完美但 RR=1.29 做空不应为 A/B，实际 {scored.final_grade}")
        self.assertIn(scored.label, ("OBSERVE", "LOW_QUALITY"),
                     f"RR<1.5 做空 label 应 OBSERVE/LOW_QUALITY，实际 {scored.label}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
