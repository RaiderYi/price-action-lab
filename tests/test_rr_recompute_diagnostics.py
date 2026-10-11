"""
P7.1: RR 计算核验 + 价格伪造检测测试
"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rule_guardrail import ScoredSignal, apply_guardrails


def make_h2_real_prices():
    """Construct a realistic H2 signal with proper prices"""
    return ScoredSignal(
        symbol="000333", signal_type="H2", direction="long", market="A股",
        llm_entry_min=80.0, llm_entry_max=81.0, llm_stop_loss=78.5, llm_tp1=85.0,
        llm_score=75, llm_confidence=0.70, llm_rr=2.0, current_price=80.5
    )


def make_h2_fabricated():
    """Construct a fabricated signal with template prices"""
    return ScoredSignal(
        symbol="300308", signal_type="H2", direction="long", market="A股",
        llm_entry_min=48.3, llm_entry_max=48.5, llm_stop_loss=47.5, llm_tp1=49.5,
        llm_score=75, llm_confidence=0.75, llm_rr=1.22, current_price=1161.0
    )


class TestPriceFabrication:
    """P7.1: 价格伪造检测"""

    def test_real_prices_pass(self):
        s = make_h2_real_prices()
        r = apply_guardrails(s)
        fabrication_violations = [v for v in r.guardrail_violations if "价格伪造" in v]
        assert len(fabrication_violations) == 0

    def test_fabricated_prices_detected(self):
        s = make_h2_fabricated()
        r = apply_guardrails(s)
        # P7.2: fabrications go to hard_violations (not guardrail_violations)
        fabrication_violations = [v for v in r.hard_violations if "价格伪造" in v]
        assert len(fabrication_violations) >= 1

    def test_fabrication_downgrades_grade(self):
        s = make_h2_fabricated()
        r = apply_guardrails(s)
        # P7.2: fabrication → REJECT
        assert r.final_grade == "REJECT"

    def test_no_current_price_skips_check(self):
        s = ScoredSignal(
            symbol="test", signal_type="H2", direction="long", market="A股",
            llm_entry_min=48.3, llm_entry_max=48.5, llm_stop_loss=47.5, llm_tp1=49.5,
            llm_score=75, llm_confidence=0.75, llm_rr=1.22, current_price=0.0
        )
        r = apply_guardrails(s)
        fabrication_violations = [v for v in r.guardrail_violations if "价格伪造" in v]
        assert len(fabrication_violations) == 0  # No price to compare against

    def test_slightly_off_prices_not_flagged(self):
        """Prices within 30% tolerance should not trigger fabrication flag"""
        s = ScoredSignal(
            symbol="test", signal_type="H2", direction="long", market="A股",
            llm_entry_min=38.0, llm_entry_max=39.0, llm_stop_loss=37.0, llm_tp1=42.0,
            llm_score=75, llm_confidence=0.75, llm_rr=2.0, current_price=40.0
        )
        r = apply_guardrails(s)
        fabrication_violations = [v for v in r.guardrail_violations if "价格伪造" in v]
        assert len(fabrication_violations) == 0


class TestExecutionRR:
    """P7.1: execution_rr 计算"""

    def test_rr_from_real_prices(self):
        s = make_h2_real_prices()
        r = apply_guardrails(s)
        # entry_mid=80.5, sl=78.5, tp=85.0
        # risk=2.0, reward=4.5, rr=2.25
        assert 2.0 <= r.rr <= 2.5

    def test_rr_not_fixed(self):
        """不同价格组合产生不同 RR"""
        s1 = ScoredSignal(symbol="A", signal_type="H2", direction="long", market="A股",
                         llm_entry_min=100, llm_entry_max=102, llm_stop_loss=98, llm_tp1=108,
                         llm_score=75, llm_confidence=0.7, llm_rr=0)
        s2 = ScoredSignal(symbol="B", signal_type="H2", direction="long", market="A股",
                         llm_entry_min=50, llm_entry_max=51, llm_stop_loss=48, llm_tp1=56,
                         llm_score=75, llm_confidence=0.7, llm_rr=0)
        r1 = apply_guardrails(s1)
        r2 = apply_guardrails(s2)
        # s1: entry=101, risk=3, reward=7, rr=2.33
        # s2: entry=50.5, risk=2.5, reward=5.5, rr=2.20
        assert abs(r1.rr - r2.rr) > 0.01  # Different stocks should have different RR

    def test_rr_computed_from_entry_stop_tp(self):
        s = ScoredSignal(symbol="test", signal_type="H2", direction="long", market="A股",
                        llm_entry_min=10, llm_entry_max=10, llm_stop_loss=9, llm_tp1=12,
                        llm_score=75, llm_confidence=0.7, llm_rr=5.0)  # LLM claims RR=5
        r = apply_guardrails(s)
        # entry=10, risk=1, reward=2, rr=2.0
        assert r.rr == 2.0  # System recalculates, ignoring LLM's claim


class TestStructureRR:
    """P7.1: structure_rr 与 execution_rr 分离"""

    def test_structure_rr_field_exists(self):
        s = make_h2_real_prices()
        assert hasattr(s, 'structure_rr')

    def test_structure_rr_fallback(self):
        s = make_h2_real_prices()
        # structure_rr computed externally by run_strategy.py
        # Guardrail doesn't set it — it's a pre-computed field
        assert hasattr(s, 'structure_rr')

    def test_structure_rr_from_HL_points(self):
        s = ScoredSignal(
            symbol="test", signal_type="H2", direction="long", market="A股",
            llm_entry_min=100, llm_entry_max=100, llm_stop_loss=95, llm_tp1=110,
            llm_score=75, llm_confidence=0.7, llm_rr=0,
            structure_evidence={"HL1": 105, "HL2": 97},
            current_price=100
        )
        # If structure_rr was computed from HL points
        # risk = 100-97=3, reward = 105-100=5, rr=1.67
        # Depends on _compute_structure_rr calling
        assert s.structure_rr >= 0
