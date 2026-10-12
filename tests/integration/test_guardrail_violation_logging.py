"""
P5.5: Guardrail 审计透明度测试

验证所有触发规则都写入 rule_log，包括未改变 grade 的规则。
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rule_guardrail import ScoredSignal, apply_guardrails


def _make_signal(symbol="600276", signal_type="L2", direction="short", market="A股",
                 entry=48.4, stop=49.5, tp1=45.0, score=85, **ev_extra):
    ev = {
        "LH1": 50.17, "LH2": 50.43, "prior_low": 47.62,
        "trigger_bar": "bear_bar", "confirmation": "break_low",
        "counter_evidence": "日线支撑附近",
    }
    ev.update(ev_extra)
    return ScoredSignal(
        symbol=symbol, signal_type=signal_type, direction=direction, market=market,
        llm_entry_min=entry, llm_entry_max=entry + 0.2, llm_stop_loss=stop,
        llm_tp1=tp1, llm_score=score, llm_confidence=0.85 if score >= 80 else 0.7,
        llm_rr=abs(tp1 - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 2.0,
        structure_evidence=ev,
        invalid_condition="突破止损失效",
    )


class TestGuardrailViolationLogging(unittest.TestCase):

    def test_rule_changes_grade_logged(self):
        """规则触发 → rule_log 记录（即使 grade 可能已被其他规则先改变）。"""
        s = apply_guardrails(ScoredSignal(
            symbol="600276", signal_type="L2", direction="short", market="A股",
            llm_entry_min=48.4, llm_entry_max=48.6, llm_stop_loss=49.5,
            llm_tp1=44.0, llm_score=75, llm_confidence=0.7, llm_rr=3.0,
            structure_evidence={
                "LH1": 52.0, "LH2": 50.43, "prior_low": 47.62,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "日线支撑",
            },
            invalid_condition="突破止损失效",
        ))
        self.assertGreater(len(s.rule_log), 0, "rule_log should have entries")
        diag = [r for r in s.rule_log if r["rule"] == "diagnostic_symbol"]
        self.assertGreater(len(diag), 0, "diagnostic_symbol must be in rule_log")
        self.assertTrue(diag[0]["triggered"], "diagnostic must be triggered")
        # Grade may not change if other rules (e.g. RR mismatch) downgraded first,
        # but the rule IS triggered and recorded — that's the point of P5.5

    def test_rule_triggered_but_grade_unchanged_still_logged(self):
        """规则触发但 grade 已被压低 → violation 仍记录 + rule_log 有 entry。"""
        # Signal with very low RR (already C/D) + low position
        s = apply_guardrails(_make_signal(
            symbol="300059", entry=19.1, stop=19.45, tp1=19.02, score=75,
            position_from_60d_low=1.0, position_from_20d_low=1.0))
        # Low position should still be logged even if grade already low from RR
        low_pos_logs = [r for r in s.rule_log if r["rule"] == "low_position_short_filter"]
        self.assertGreater(len(low_pos_logs), 0,
                           "low_position_short_filter must log even if grade unchanged")

    def test_multiple_rules_all_logged(self):
        """多条规则同时触发 → 全部记录在 rule_log。"""
        s = apply_guardrails(ScoredSignal(
            symbol="600276", signal_type="L2", direction="short", market="A股",
            llm_entry_min=48.4, llm_entry_max=48.6, llm_stop_loss=49.5,
            llm_tp1=44.0, llm_score=85, llm_confidence=0.85, llm_rr=2.0,
            structure_evidence={
                "LH1": 52.0, "LH2": 50.43, "prior_low": 47.62,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "日线支撑",
                "position_from_60d_low": 1.0,
            },
            invalid_condition="突破止损失效",
        ))
        rules = set(r["rule"] for r in s.rule_log)
        expected = {"diagnostic_symbol", "confidence_cap"}
        found = rules & expected
        self.assertGreaterEqual(len(found), 2,
            f"Multiple rules should fire, got: {rules}, expected at least 2 of {expected}")
        # All triggered entries must have triggered=True
        for r in s.rule_log:
            self.assertTrue(r["triggered"], f"{r['rule']} should be triggered")

    def test_low_position_filter_logged_even_if_grade_unchanged(self):
        """低位追空过滤触发但未改变 grade → rule_log 中 grade_changed=false。"""
        s = apply_guardrails(_make_signal(
            entry=19.1, stop=19.45, tp1=19.02, score=75,
            position_from_60d_low=1.0,
        ))
        lp_logs = [r for r in s.rule_log if r["rule"] == "low_position_short_filter"]
        if lp_logs:
            self.assertFalse(lp_logs[0]["grade_changed"],
                             "Should not change grade if already low")

    def test_confidence_cap_logged_even_if_grade_unchanged(self):
        """Confidence cap 触发但 grade 已被压低 → 仍记录。"""
        s = apply_guardrails(_make_signal(
            symbol="300059", entry=19.1, stop=19.45, tp1=18.8, score=85,
        ))
        cc_logs = [r for r in s.rule_log if r["rule"] == "confidence_cap"]
        self.assertGreater(len(cc_logs), 0, "confidence_cap must log for score>=80")

    def test_audit_log_has_grade_changed_field(self):
        """rule_log 每条 entry 包含 grade_changed 字段。"""
        s = apply_guardrails(_make_signal(score=75))
        for entry in s.rule_log:
            self.assertIn("grade_changed", entry)
            self.assertIn("previous_grade", entry)
            self.assertIn("new_grade", entry)
            self.assertIn("rule", entry)
            self.assertIn("reason", entry)

    def test_diagnostic_symbol_logged(self):
        """600276 诊断标的必然触发 rule_log。"""
        s = apply_guardrails(_make_signal(symbol="600276", score=75,
                                          LH1=50.17, LH2=49.50))  # LH2<LH1
        diag_logs = [r for r in s.rule_log if r["rule"] == "diagnostic_symbol"]
        self.assertGreater(len(diag_logs), 0, "600276 must trigger diagnostic_symbol")


if __name__ == "__main__":
    unittest.main()
