#!/usr/bin/env python3
"""
策略系统硬规则测试套件

覆盖:
  1. 信号枚举一致性
  2. RR guardrail 硬规则
  3. L2 结构验证
  4. 市场差异化配置
  5. 信号注册表自检
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from signal_registry import (
    SIGNAL_REGISTRY, check_consistency, get_signal_types,
    get_min_rr, get_required_fields, validate_signal_type,
)
from rule_guardrail import ScoredSignal, apply_guardrails, GRADE_ORDER
from market_config import MARKET_CONFIG, get_market_config


# ═══════════════════════════════════════════════════════════════════
# Test 1: Signal Registry Consistency
# ═══════════════════════════════════════════════════════════════════

class TestSignalRegistryConsistency(unittest.TestCase):
    """信号枚举一致性测试。"""

    def test_total_signal_count(self):
        """信号总数应为 14。（Focus v1注: disabled组已移除，buy/sell_the_close不在SIGNAL_REGISTRY）"""
        self.assertEqual(len(SIGNAL_REGISTRY), 14,
                         f"期望 14 种信号，实际 {len(SIGNAL_REGISTRY)}")

    def test_self_check_passes(self):
        """注册表自检应通过。"""
        result = check_consistency()
        self.assertTrue(result["consistent"],
                        f"注册表自检失败: {result['issues']}")

    def test_all_signals_have_min_rr(self):
        """每种信号都必须有 min_rr 字段。"""
        for st, cfg in SIGNAL_REGISTRY.items():
            self.assertIn("min_rr", cfg, f"'{st}' 缺少 min_rr")
            self.assertGreater(cfg["min_rr"], 0, f"'{st}' min_rr 必须 > 0")

    def test_all_signals_have_kb_concepts(self):
        """每种信号都必须有 KB 概念映射。"""
        for st, cfg in SIGNAL_REGISTRY.items():
            self.assertIn("kb_concepts", cfg, f"'{st}' 缺少 kb_concepts")
            self.assertTrue(len(cfg["kb_concepts"]) > 0,
                           f"'{st}' kb_concepts 为空")

    def test_all_signals_have_risk_notes(self):
        """每种信号都必须有风险提示。"""
        for st, cfg in SIGNAL_REGISTRY.items():
            self.assertIn("risk_notes", cfg, f"'{st}' 缺少 risk_notes")

    def test_group_counts(self):
        """各组信号数量应正确。"""
        # Focus v1 (2026-10-11): disabled组已从SIGNAL_REGISTRY移除
        groups = {"trend_continuation": 6, "reversal": 5, "range": 2, "measurement": 1}
        registry = SIGNAL_REGISTRY
        for g, expected in groups.items():
            actual = sum(1 for c in registry.values() if c["group"] == g)
            self.assertEqual(actual, expected,
                             f"组 '{g}' 应有 {expected} 种，实际 {actual}")

    def test_reversal_signals_min_rr(self):
        """反转信号 min_rr 应为 2.0。"""
        for st, cfg in SIGNAL_REGISTRY.items():
            if cfg["group"] == "reversal":
                self.assertEqual(cfg["min_rr"], 2.0,
                                 f"反转信号 '{st}' min_rr 应为 2.0，实际 {cfg['min_rr']}")


# ═══════════════════════════════════════════════════════════════════
# Test 2: RR Guardrail Rules
# ═══════════════════════════════════════════════════════════════════

def _make_signal(symbol="TEST", signal_type="L2", direction="short",
                 entry=100.0, stop=102.0, tp1=98.0, market="A股",
                 structure_evidence=None, llm_score=80):
    """工厂函数：创建测试用 ScoredSignal。"""
    if structure_evidence is None:
        structure_evidence = {}
    # 确保测试信号有基本证据
    if "counter_evidence" not in structure_evidence:
        structure_evidence["counter_evidence"] = "Key support at 90 could hold"
    s = ScoredSignal(
        symbol=symbol,
        signal_type=signal_type,
        direction=direction,
        market=market,
        llm_entry_min=entry - 0.5,
        llm_entry_max=entry + 0.5,
        llm_stop_loss=stop,
        llm_tp1=tp1,
        llm_score=llm_score,
        llm_confidence=0.8,
        llm_position_pct=0.02,
        structure_evidence=structure_evidence,
        invalid_condition="价格突破止损位",
    )
    return s


class TestRRGuardrails(unittest.TestCase):
    """RR 硬规则测试。"""

    def test_rr_below_1_rejected(self):
        """RR < 1.0 必须 REJECT。"""
        s = ScoredSignal(
            symbol="T", signal_type="H1", direction="long", market="A股",
            llm_entry_min=99.5, llm_entry_max=100.5, llm_stop_loss=98.5,
            llm_tp1=100.5, llm_score=85, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={"counter_evidence": "Breakdown below 90 invalidates"},
            invalid_condition="跌破止损位")
        s = apply_guardrails(s)
        self.assertEqual(s.final_grade, "REJECT",
                         f"RR={s.rr:.2f}<1.0 应为 REJECT，实际 {s.final_grade}")
        rr_msgs = [v for v in s.guardrail_violations + s.hard_violations if "RR" in v]
        self.assertTrue(len(rr_msgs) > 0, f"应有 RR 违规消息: {s.guardrail_violations + s.hard_violations}")

    def test_rr_between_1_and_1_5_max_C(self):
        """1.0 ≤ RR < 1.5 最高 C 级。"""
        s = ScoredSignal(
            symbol="T", signal_type="L2", direction="long", market="A股",
            llm_entry_min=99.5, llm_entry_max=100.5, llm_stop_loss=98.5,
            llm_tp1=101.5, llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={"counter_evidence": "Breakdown below 90 invalidates"},
            invalid_condition="跌破止损位")
        s = apply_guardrails(s)
        self.assertIn(s.final_grade, ("C", "D", "REJECT"),
                      f"RR={s.rr:.2f} 在 1.0-1.5 应为 C/D/REJECT，实际 {s.final_grade}")
        self.assertIn(s.label, ("OBSERVE", "LOW_QUALITY", "REJECT"))

    def test_short_rr_below_1_5_max_C(self):
        """做空信号 RR < 1.5 最高 C 级。"""
        s = ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=99.5, llm_entry_max=100.5, llm_stop_loss=103,
            llm_tp1=96.5, llm_score=80, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={"counter_evidence": "Break above 105 invalidates"},
            invalid_condition="价格突破止损位")
        s = apply_guardrails(s)
        self.assertIn(s.final_grade, ("C", "D"),
                      f"做空 RR={s.rr:.2f}<1.5 应 ≤ C，实际 {s.final_grade}")

    def test_rr_1_6_allows_B_or_above(self):
        """RR ≥ 1.5 且结构好时可以 B 或更高。"""
        s = ScoredSignal(
            symbol="T", signal_type="H2", direction="long", market="A股",
            llm_entry_min=99.5, llm_entry_max=100.5, llm_stop_loss=98,
            llm_tp1=103, llm_score=85, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "HL1": 95.0, "HL2": 97.0, "prior_high": 105.0,
                "trigger_bar": "bull_bar", "confirmation": "follow_through",
                "counter_evidence": "Breakthrough above 105 would invalidate"},
            invalid_condition="价格跌破 HL2")
        s = apply_guardrails(s)
        self.assertNotEqual(s.final_grade, "REJECT")

    def test_high_structure_low_rr_max_observe(self):
        """结构好但 RR 不达标 = 只能观察。"""
        s = ScoredSignal(
            symbol="T", signal_type="L2", direction="short", market="A股",
            llm_entry_min=99.5, llm_entry_max=100.5, llm_stop_loss=103,
            llm_tp1=96.5, llm_score=85, llm_confidence=0.8, llm_position_pct=0.02,
            structure_evidence={
                "LH1": 110.0, "LH2": 108.0, "prior_low": 100.0,
                "trigger_bar": "bear_engulfing", "confirmation": "break_low",
                "counter_evidence": "Break above 110 would invalidate"},
            invalid_condition="价格突破止损位")
        s = apply_guardrails(s)
        self.assertNotEqual(s.final_grade, "A",
                           f"结构好但 RR={s.rr:.2f} 不应该是 A")
        self.assertIn(s.label, ("OBSERVE", "LOW_QUALITY", "REJECT"),
                      f"结构好但 RR 不达标应为 OBSERVE/LOW_QUALITY/REJECT，实际 {s.label}")


# ═══════════════════════════════════════════════════════════════════
# Test 3: L2 Structure Validation
# ═══════════════════════════════════════════════════════════════════

class TestL2Validation(unittest.TestCase):
    """L2 信号结构验证测试。"""

    def test_lh2_less_than_lh1_standard(self):
        """LH2 < LH1 → standard_L2。"""
        s = _make_signal(entry=98, stop=100, tp1=94)  # RR=2.0
        s.structure_evidence = {
            "LH1": 105.0, "LH2": 103.0, "prior_low": 98.0,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
        }
        s = apply_guardrails(s)
        self.assertEqual(s.signal_variant, "standard_L2")

    def test_lh2_equals_lh1_weak(self):
        """LH2 ≈ LH1 → weak_L2。"""
        s = _make_signal(entry=98, stop=100, tp1=94)
        s.structure_evidence = {
            "LH1": 105.0, "LH2": 105.1, "prior_low": 98.0,  # 0.1 在容差内
            "trigger_bar": "bear_bar", "confirmation": "break_low",
        }
        s = apply_guardrails(s)
        self.assertIn(s.signal_variant, ("weak_L2", "standard_L2"))

    def test_lh2_greater_than_lh1_invalid(self):
        """LH2 > LH1 → invalid_or_weak_L2，最高 C 级。"""
        s = _make_signal(entry=98, stop=100, tp1=94)
        s.structure_evidence = {
            "LH1": 100.0, "LH2": 103.0, "prior_low": 98.0,  # LH2 > LH1!
            "trigger_bar": "bear_bar", "confirmation": "break_low",
        }
        s = apply_guardrails(s)
        self.assertEqual(s.signal_variant, "invalid_or_weak_L2",
                         f"LH2>LH1 应为 invalid_or_weak_L2，实际 {s.signal_variant}")
        self.assertIn(s.final_grade, ("C", "D", "REJECT"),
                      f"LH2>LH1 最高 C 级，实际 {s.final_grade}")

    def test_missing_lh1_lh2_max_D(self):
        """缺少 LH1/LH2 最高 D 级。"""
        s = _make_signal(entry=98, stop=100, tp1=94)
        s.invalid_condition = "价格突破止损"
        s.structure_evidence = {"counter_evidence": "double bottom risk at 90"}
        s = apply_guardrails(s)
        has_lh_issue = any("LH1" in v or "LH2" in v for v in s.guardrail_violations + s.missing_evidence)
        self.assertTrue(has_lh_issue,
                       f"应记录缺少 LH1/LH2: violations={s.guardrail_violations}, missing={s.missing_evidence}")
        self.assertIn(s.final_grade, ("D", "REJECT"),
                      f"缺少 LH1/LH2 应 ≤ D，实际 {s.final_grade}")

    def test_downtrend_l2_accepted(self):
        """日线下跌趋势中 L2 应被接受。"""
        s = _make_signal(entry=98, stop=100, tp1=94)
        s.structure_evidence = {
            "LH1": 105.0, "LH2": 103.0, "prior_low": 98.0,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "daily_trend": "downtrend",
        }
        s = apply_guardrails(s)
        self.assertEqual(s.signal_variant, "standard_L2")


# ═══════════════════════════════════════════════════════════════════
# Test 4: Market Config Differentiation
# ═══════════════════════════════════════════════════════════════════

class TestMarketConfig(unittest.TestCase):
    """市场差异化配置测试。"""

    def test_ashare_config(self):
        cfg = get_market_config("A股")
        self.assertTrue(cfg["has_t_plus_1"])
        self.assertTrue(cfg["has_price_limit"])
        self.assertTrue(cfg["short_constraint"])
        self.assertEqual(cfg["risk_per_trade"], 0.02)
        self.assertEqual(cfg["expire_bars_30m"], 40)

    def test_crypto_config(self):
        cfg = get_market_config("crypto")
        self.assertFalse(cfg["has_t_plus_1"])
        self.assertFalse(cfg["has_price_limit"])
        self.assertFalse(cfg["short_constraint"])
        self.assertEqual(cfg["risk_per_trade"], 0.01)
        self.assertEqual(cfg["expire_bars_30m"], 80)

    def test_ashare_risk_notes_include_t1(self):
        notes = MARKET_CONFIG["A股"]["risk_notes"]
        t1_note = any("T+1" in n for n in notes)
        self.assertTrue(t1_note, "A股风险提示应包含 T+1")

    def test_crypto_risk_notes_include_wick(self):
        notes = MARKET_CONFIG["crypto"]["risk_notes"]
        wick_note = any("插针" in n for n in notes)
        self.assertTrue(wick_note, "加密风险提示应包含插针")

    def test_position_halved_for_crypto(self):
        """加密信号的仓位应为 A 股的一半。"""
        s_ashare = _make_signal(entry=100, stop=102, tp1=104, direction="long",
                                signal_type="H2", market="A股")
        s_ashare.structure_evidence = {
            "HL1": 95, "HL2": 97, "prior_high": 105,
            "trigger_bar": "bull_bar", "confirmation": "break_high",
            "counter_evidence": "none",
        }
        s_ashare.invalid_condition = "跌破 HL2"
        s_ashare = apply_guardrails(s_ashare)

        s_crypto = _make_signal(entry=100, stop=102, tp1=104, direction="long",
                                signal_type="H2", market="crypto")
        s_crypto.structure_evidence = s_ashare.structure_evidence
        s_crypto.invalid_condition = s_ashare.invalid_condition
        s_crypto = apply_guardrails(s_crypto)

        # 若 A 股为 normal，加密应为 half
        if s_ashare.position_suggestion == "normal":
            self.assertEqual(s_crypto.position_suggestion, "half")


# ═══════════════════════════════════════════════════════════════════
# Test 5: Stop Loss Validation
# ═══════════════════════════════════════════════════════════════════

class TestStopLossValidation(unittest.TestCase):
    """止损规则测试。"""

    def test_stop_loss_exceeds_limit(self):
        """止损超过 2.5% 最高 C 级。"""
        s = _make_signal(entry=100, stop=104, tp1=108)  # 4% 止损
        s = apply_guardrails(s)
        self.assertIn(s.final_grade, ("C", "D", "REJECT"),
                      f"止损 4% 应 ≤ C，实际 {s.final_grade}")


# ═══════════════════════════════════════════════════════════════════
# Test 6: Grade Cap Logic
# ═══════════════════════════════════════════════════════════════════

class TestGradeCaps(unittest.TestCase):
    """等级上限测试。"""

    def test_missing_invalid_condition_max_C(self):
        """缺少失效条件最高 C。"""
        s = _make_signal()
        s.invalid_condition = ""  # 空
        s = apply_guardrails(s)
        self.assertIn(s.final_grade, ("C", "D", "REJECT"))

    def test_missing_counter_evidence_max_C(self):
        """缺少反方证据应由 guardrail 记录。"""
        s = _make_signal()
        # 显式移除 factory 默认的 counter_evidence
        s.structure_evidence.pop("counter_evidence", None)
        s = apply_guardrails(s)
        violations_text = " ".join(s.guardrail_violations)
        self.assertTrue(any("反方证据" in v for v in s.guardrail_violations),
                        f"应提醒缺少反方证据: {violations_text}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
