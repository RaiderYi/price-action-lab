"""
P7.2: 价格真实性硬约束测试

验证:
1. entry 偏离 >30% → REJECT
2. stop_loss 偏离 >30% → REJECT
3. take_profit 偏离 >30% → REJECT
4. 批量伪造检测
5. system_price_builder 生成真实价格
6. 价格伪造不得进入 OBSERVE
"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rule_guardrail import (ScoredSignal, apply_guardrails,
                            detect_batch_fabrication, get_batch_fabrication_result)
from system_price_builder import build_system_prices


class TestPriceFabricationHardReject:
    """P7.2: 价格伪造 → REJECT (不是 C)"""

    def test_entry_fabrication_reject(self):
        s = ScoredSignal(symbol="X", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=46, llm_tp1=52,
                        llm_score=75, llm_confidence=0.7, llm_rr=2.0, current_price=10)
        r = apply_guardrails(s)
        assert r.final_grade == "REJECT"

    def test_stop_fabrication_reject(self):
        s = ScoredSignal(symbol="X", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=10, llm_entry_max=11, llm_stop_loss=48, llm_tp1=13,
                        llm_score=75, llm_confidence=0.7, llm_rr=2.0, current_price=10)
        r = apply_guardrails(s)
        assert r.final_grade == "REJECT"

    def test_tp_fabrication_reject(self):
        s = ScoredSignal(symbol="X", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=10, llm_entry_max=11, llm_stop_loss=9, llm_tp1=49,
                        llm_score=75, llm_confidence=0.7, llm_rr=2.0, current_price=10)
        r = apply_guardrails(s)
        assert r.final_grade == "REJECT"

    def test_9yuan_stock_with_48_entry_reject(self):
        s = ScoredSignal(symbol="601985", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=47, llm_tp1=50,
                        llm_score=75, llm_confidence=0.7, llm_rr=1.2, current_price=9.0)
        r = apply_guardrails(s)
        assert r.final_grade == "REJECT"

    def test_1161_stock_with_48_entry_reject(self):
        s = ScoredSignal(symbol="300308", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=47, llm_tp1=50,
                        llm_score=75, llm_confidence=0.7, llm_rr=1.2, current_price=1161.0)
        r = apply_guardrails(s)
        assert r.final_grade == "REJECT"

    def test_realistic_prices_pass(self):
        s = ScoredSignal(symbol="600036", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=37, llm_entry_max=38, llm_stop_loss=36, llm_tp1=41,
                        llm_score=75, llm_confidence=0.7, llm_rr=2.5, current_price=38.0)
        r = apply_guardrails(s)
        assert r.final_grade != "REJECT"  # Realistic prices should not trigger fabrication


class TestBatchFabrication:
    """P7.2: 批量伪造检测"""

    def test_batch_template_detected(self):
        signals = [
            ScoredSignal(symbol="A", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=47, llm_tp1=50,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=1000),
            ScoredSignal(symbol="B", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=47, llm_tp1=50,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=800),
            ScoredSignal(symbol="C", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=47, llm_tp1=50,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=700),
            ScoredSignal(symbol="D", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=48, llm_entry_max=49, llm_stop_loss=47, llm_tp1=50,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=600),
        ]
        for s in signals:
            s.entry_mid = (s.llm_entry_min + s.llm_entry_max) / 2
        result = detect_batch_fabrication(signals)
        assert result["detected"] is True
        assert len(result["affected"]) >= 3

    def test_diverse_prices_no_batch(self):
        signals = [
            ScoredSignal(symbol="A", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=100, llm_entry_max=101, llm_stop_loss=98, llm_tp1=105,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=100),
            ScoredSignal(symbol="B", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=50, llm_entry_max=51, llm_stop_loss=48, llm_tp1=55,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=50),
            ScoredSignal(symbol="C", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=10, llm_entry_max=11, llm_stop_loss=9, llm_tp1=13,
                        llm_score=75, llm_confidence=0.7, llm_rr=0, current_price=10),
        ]
        for s in signals:
            s.entry_mid = (s.llm_entry_min + s.llm_entry_max) / 2
        result = detect_batch_fabrication(signals)
        assert result["detected"] is False


class TestSystemPriceBuilder:
    """P7.2: 系统价格计算"""

    def test_h2_long_builds_prices(self):
        result = build_system_prices("300308", "H2", "long", 1161.0,
                                     {"HL1": 1180, "HL2": 1140})
        assert result["entry_min"] > 0
        assert result["stop_loss"] > 0
        assert result["tp1"] > 0
        assert "system" in result["price_source"]

    def test_prices_near_current_price(self):
        result = build_system_prices("test", "H2", "long", 100.0, {})
        # entry should be near current price
        assert abs(result["entry_min"] - 99.0) < 2  # ~1% of 100
        assert abs(result["entry_max"] - 101.0) < 2

    def test_rr_is_computable(self):
        result = build_system_prices("test", "H2", "long", 100.0, {})
        # Generic H2: stop at 93, tp at 106 → risk=7, reward=6
        assert result["execution_rr"] > 0.5  # Should be reasonable

    def test_h2_long_tp1_from_prior_high_not_hl1(self):
        """A2: tp1 应来自 prior_high，不是 HL1（prior swing low）"""
        # HL1=90 (prior low, 不能作为做多目标), prior_high=115 (上方目标)
        result = build_system_prices("X", "H2", "long", 100.0,
                                     {"HL1": 90, "HL2": 95, "prior_high": 115})
        assert result["tp1"] == 115.0, f"tp1 should be prior_high=115, got {result['tp1']}"

    def test_h2_long_tp1_fallback_no_prior_high(self):
        """A2: 无 prior_high 时 tp1 fallback 到 cp*1.06"""
        result = build_system_prices("X", "H2", "long", 100.0,
                                     {"HL1": 90, "HL2": 95})
        assert result["tp1"] == round(100.0 * 1.06, 2)

    def test_h2_long_tp1_ignores_prior_high_below_cp(self):
        """A2: prior_high 低于 cp 时忽略，fallback 到 cp*1.06"""
        result = build_system_prices("X", "H2", "long", 100.0,
                                     {"HL1": 90, "HL2": 95, "prior_high": 98})
        assert result["tp1"] == round(100.0 * 1.06, 2)

    def test_insufficient_on_zero_price(self):
        result = build_system_prices("test", "H2", "long", 0.0, {})
        assert "insufficient" in result["price_source"]
        assert result["entry_min"] == 0

    def test_wedge_with_push_points(self):
        result = build_system_prices("test", "wedge", "short", 100.0,
                                     {"push_1_price": 110, "push_2_price": 105, "push_3_price": 100})
        # short wedge: entry near 100, stop above p1(110), target below
        assert result["stop_loss"] > 100  # Short: stop above

    def test_wedge_short_stop_has_daily_bar_buffer(self):
        result = build_system_prices("test", "wedge", "short", 108.96, {
            "push_1_price": 103.0,
            "push_2_price": 106.0,
            "push_3_price": 108.96,
            "wedge_extreme": 108.96,
            "wedge_start": 103.0,
            "push_3_confirmed": True,
        })

        assert result["stop_loss"] >= round(108.96 * 1.02, 2)
        assert result["execution_rr"] < 10.0

    def test_wedge_execution_rr_is_capped(self):
        result = build_system_prices("test", "wedge", "short", 102.0, {
            "push_1_price": 100.0,
            "push_2_price": 101.0,
            "push_3_price": 102.0,
            "wedge_extreme": 102.0,
            "wedge_start": 1.0,
            "push_3_confirmed": True,
        })

        assert result["execution_rr"] == 10.0

    def test_tr_fade_with_range(self):
        result = build_system_prices("test", "tr_fade", "long", 50.0,
                                     {"range_high": 55, "range_low": 45})
        # Long tr_fade: buy near range_low, target midpoint (=50 for range 45-55)
        assert result["tp1"] >= 50  # Target at or above entry

    def test_measured_move_projection(self):
        result = build_system_prices("test", "measured_move", "long", 100.0,
                                     {"measure_start": 80, "measure_end": 100, "breakout_point": 100})
        # Move=20, target=120
        assert result["tp2"] > 110

    def test_fallback_uses_current_price(self):
        result = build_system_prices("test", "unknown_type", "long", 50.0, {})
        assert "fallback" in result["price_source"]
        assert result["entry_min"] > 0
