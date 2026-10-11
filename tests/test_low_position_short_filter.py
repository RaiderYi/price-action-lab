"""
【自迭代 #10】低位追空临时过滤器测试

覆盖:
1. dist60 < 2% L2 short → max OBSERVE
2. dist20 < 2% L2 short → max OBSERVE
3. ret10 < -8% L2 short → max OBSERVE
4. normal position L2 short 不受影响
5. long signal 不受影响
6. crypto short 不受影响
7. warning 写入 guardrail_violations
8. low_position_short_warning 标记
9. temporary guardrail review_after 正确
"""

import sys, os, unittest, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rule_guardrail import ScoredSignal, apply_guardrails


def _make_l2_short(symbol="600276", position_60=None, position_20=None, ret_10d=None, market="A股"):
    """创建 L2 short 测试信号。"""
    ev = {
        "LH1": 50.17, "LH2": 50.43, "prior_low": 47.62,
        "trigger_bar": "bear_bar", "confirmation": "break_low",
        "counter_evidence": "日线支撑附近",
    }
    if position_60 is not None:
        ev["position_from_60d_low"] = position_60
    if position_20 is not None:
        ev["position_from_20d_low"] = position_20
    if ret_10d is not None:
        ev["recent_10d_return"] = ret_10d

    return ScoredSignal(
        symbol=symbol, signal_type="L2", direction="short", market=market,
        llm_entry_min=48.3, llm_entry_max=48.5, llm_stop_loss=49.5,
        llm_tp1=45.0, llm_tp2=43.0, llm_score=75, llm_confidence=0.7, llm_rr=2.5,
        structure_evidence=ev,
        invalid_condition="突破49.5失效",
    )


class TestLowPositionShortFilter(unittest.TestCase):

    def test_dist60_lt_2pct_capped_to_observe(self):
        """dist60 < 2% → max OBSERVE。"""
        s = apply_guardrails(_make_l2_short(position_60=1.5))
        self.assertIn(s.final_grade, ("C", "D"), f"got {s.final_grade}")
        violations = "; ".join(s.guardrail_violations)
        self.assertIn("低位追空警示", violations, f"no warning in: {violations}")

    def test_dist20_lt_2pct_capped_to_observe(self):
        """dist20 < 2% → max OBSERVE。"""
        s = apply_guardrails(_make_l2_short(position_20=1.0, position_60=10.0))
        violations = "; ".join(s.guardrail_violations)
        self.assertIn("低位追空警示", violations)

    def test_ret10_lt_neg8_capped_to_observe(self):
        """ret10 < -8% → max OBSERVE。"""
        s = apply_guardrails(_make_l2_short(ret_10d=-10.0, position_60=10.0))
        violations = "; ".join(s.guardrail_violations)
        self.assertIn("低位追空警示", violations)

    def test_normal_position_not_affected(self):
        """正常位置 L2 short 不受影响。"""
        s = apply_guardrails(_make_l2_short(position_60=10.0, position_20=8.0, ret_10d=-3.0))
        violations = "; ".join(s.guardrail_violations)
        self.assertNotIn("低位追空警示", violations, f"should not trigger: {violations}")

    def test_long_signal_not_affected(self):
        """做多信号不受低位追空过滤影响。"""
        ev = {
            "HL1": 100.0, "HL2": 102.0, "prior_high": 110.0,
            "trigger_bar": "bull_bar", "confirmation": "break_high",
            "counter_evidence": "日线阻力",
            "position_from_60d_low": 1.0,  # 极端低位但做多
        }
        s_long = ScoredSignal(
            symbol="300750", signal_type="H2", direction="long", market="A股",
            llm_entry_min=105, llm_entry_max=106, llm_stop_loss=102,
            llm_tp1=112, llm_score=75, llm_confidence=0.7, llm_rr=2.5,
            structure_evidence=ev,
            invalid_condition="跌破102失效",
        )
        s_long = apply_guardrails(s_long)
        violations = "; ".join(s_long.guardrail_violations)
        self.assertNotIn("低位追空警示", violations)

    def test_crypto_short_not_affected(self):
        """crypto short 不受 A股 规则影响。"""
        s = apply_guardrails(_make_l2_short(
            symbol="BTCUSDT", position_60=1.0, market="crypto"))
        violations = "; ".join(s.guardrail_violations)
        self.assertNotIn("低位追空警示", violations)

    def test_warning_in_guardrail_violations(self):
        """触发时 guardrail_violations 包含警示标签。"""
        s = apply_guardrails(_make_l2_short(position_60=1.0))
        has_warning = any("低位追空警示" in v for v in s.guardrail_violations)
        self.assertTrue(has_warning, f"violations: {s.guardrail_violations}")

    def test_low_position_short_warning_flag(self):
        """structure_evidence 中的 low_position_short_warning 标记。"""
        s = apply_guardrails(_make_l2_short(position_60=1.0))
        self.assertTrue(
            s.structure_evidence.get("low_position_short_warning"),
            "should set low_position_short_warning flag"
        )

    def test_temporary_guardrail_config(self):
        """验证 temporary guardrail review_after 配置。"""
        import json
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.json"
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        tg = cfg.get("temporary_guardrails", {})
        lp = tg.get("low_position_short_temporary_filter", {})
        self.assertTrue(lp.get("enabled"))
        self.assertTrue(lp.get("temporary"))
        self.assertEqual(lp.get("review_after"), "2026-06-07")


if __name__ == "__main__":
    unittest.main()
