"""
P0: micro-stop + inflated RR 治理测试

验证 _check_stop_loss_rules 对止损过近 + RR虚高信号的联合降级。
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rule_guardrail import ScoredSignal, apply_guardrails


def _make_signal(symbol="300750", signal_type="L1", direction="short",
                 entry=424.0, stop=424.79, tp1=406.20, rr=22.53,
                 sl_pct=0.00186, score=65, market="A股", **kw):
    """创建 300750-like 信号。"""
    defaults = {
        "symbol": symbol, "signal_type": signal_type, "direction": direction,
        "market": market,
        "llm_entry_min": entry - 1, "llm_entry_max": entry + 1,
        "llm_stop_loss": stop, "llm_tp1": tp1,
        "llm_score": score, "llm_confidence": 0.7,
        "llm_rr": rr, "structure_evidence": {
            "LH1": 427.0, "LH2": 425.0, "prior_low": 400.0,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
        },
        "invalid_condition": "止损失效",
        "current_price": entry,
    }
    defaults.update(kw)
    s = ScoredSignal(**defaults)
    # Manually set post-guardrail values (normally set by _compute_metrics)
    s.rr = rr
    s.stop_loss_pct = sl_pct
    s.entry_mid = entry
    s.risk = abs(entry - stop)
    s.reward = abs(tp1 - entry)
    return s


class TestMicroStopInflatedRR(unittest.TestCase):

    def test_300750_like_downgraded(self):
        """300750-like: RR=22.53, SL%=0.19% → 降为 LOW_QUALITY/D"""
        s = _make_signal()
        s = apply_guardrails(s)
        self.assertIn("D", s.final_grade)
        self.assertEqual(s.label, "LOW_QUALITY")
        self.assertTrue(any("micro-stop + inflated RR" in v for v in s.guardrail_violations))

    def test_micro_stop_normal_rr_not_downgraded(self):
        """止损过近但 RR 不高 → 仅 warning，不降级"""
        # RR=3.0: risk=0.79, need reward=2.37 → tp1 = entry - reward = 421.63
        s = _make_signal(entry=424.0, stop=424.79, tp1=421.63, rr=22.53, sl_pct=0.00186)
        s = apply_guardrails(s)
        # _compute_metrics 会重算 rr = |424-421.63|/|424-424.79| = 2.37/0.79 = 3.0
        self.assertNotEqual(s.label, "LOW_QUALITY")
        self.assertNotIn("D", s.final_grade)
        self.assertTrue(any("止损距离过近" in v for v in s.guardrail_violations))

    def test_high_rr_with_reasonable_stop_not_downgraded(self):
        """高 RR 但止损合理 (>0.5% entry) → 不降级"""
        s = _make_signal(rr=10.0, sl_pct=0.01, stop=419.76, entry=424.0)
        s.risk = abs(424.0 - 419.76)
        s = apply_guardrails(s)
        self.assertNotEqual(s.label, "LOW_QUALITY")
        # RR=10 high but stop is 1% — reasonable, should not trigger
        self.assertFalse(any("micro-stop + inflated RR" in v for v in s.guardrail_violations))

    def test_borderline_rr_8_not_triggered(self):
        """RR=8.0 恰好在阈值上 — 不触发 (>8.0 才触发)"""
        # RR=8.0: risk=0.79, need reward=6.32 → tp1 = 424 - 6.32 = 417.68
        s = _make_signal(entry=424.0, stop=424.79, tp1=417.68, rr=22.53, sl_pct=0.00186)
        s = apply_guardrails(s)
        # _compute_metrics: rr = |424-417.68|/|424-424.79| = 6.32/0.79 = 8.0
        self.assertNotEqual(s.label, "LOW_QUALITY")

    def test_rr_8_1_triggers(self):
        """RR=8.1 > 8.0 — 触发"""
        s = _make_signal(rr=8.1, sl_pct=0.003)
        s = apply_guardrails(s)
        self.assertEqual(s.label, "LOW_QUALITY")

    def test_other_signal_types_also_covered(self):
        """非 L1 信号也适用同样的 micro-stop 规则"""
        s = _make_signal(symbol="600030", signal_type="L2", direction="short",
                         entry=26.0, stop=26.05, tp1=24.0, rr=15.0, sl_pct=0.0019)
        s = apply_guardrails(s)
        self.assertEqual(s.label, "LOW_QUALITY")

    def test_long_direction_also_covered(self):
        """做多信号同样受 micro-stop 规则约束"""
        s = _make_signal(symbol="600900", signal_type="H2", direction="long",
                         entry=28.0, stop=27.95, tp1=30.0, rr=12.0, sl_pct=0.0018,
                         structure_evidence={"HL1": 27.5, "HL2": 27.8, "prior_high": 30.0,
                                              "trigger_bar": "bull_bar", "confirmation": "break_high"})
        s = apply_guardrails(s)
        self.assertEqual(s.label, "LOW_QUALITY")

    def test_normal_signal_not_affected(self):
        """正常信号（合理止损 + 正常 RR）不受影响"""
        s = _make_signal(symbol="300308", signal_type="H2", direction="long",
                         entry=1161.0, stop=1146.33, tp1=1209.99, rr=3.29, sl_pct=0.0128,
                         structure_evidence={"HL1": 1146.33, "HL2": 1149.55, "prior_high": 1209.99,
                                              "trigger_bar": "bull_bar", "confirmation": "break_high"})
        s = apply_guardrails(s)
        self.assertNotEqual(s.label, "LOW_QUALITY")
        self.assertNotIn("D", s.final_grade)

    def test_violation_message_contains_details(self):
        """降级日志包含具体数值"""
        s = _make_signal()
        s = apply_guardrails(s)
        viols = "\n".join(s.guardrail_violations)
        self.assertIn("micro-stop + inflated RR", viols)
        self.assertIn("RR=22.5", viols)


if __name__ == "__main__":
    unittest.main()
