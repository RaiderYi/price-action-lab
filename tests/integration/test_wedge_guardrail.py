import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rule_guardrail import ScoredSignal, apply_guardrails
from system_price_builder import build_system_prices


def valid_top_evidence():
    return {
        "push_1": 100,
        "push_2": 105,
        "push_3": 108,
        "push_1_price": 100,
        "push_2_price": 105,
        "push_3_price": 108,
        "push_1_index": 10,
        "push_2_index": 28,
        "push_3_index": 46,
        "push_spacing_bars": 18,
        "wedge_duration_bars": 36,
        "push_3_confirmed": True,
        "post_push_3_acceleration": False,
        "wedge_type": "wedge_top_reversal",
        "wedge_direction": "up",
        "reversal_direction": "short",
        "wedge_extreme": 108,
        "wedge_start": 100,
        "push_1_amplitude": 5,
        "push_2_amplitude": 5,
        "push_3_amplitude": 3,
        "momentum_change": "decelerating",
        "trend_context": "trend_extension",
        "counter_evidence": "opposite structure above 108",
    }


def make_signal(evidence=None, prices=None):
    evidence = evidence or valid_top_evidence()
    prices = prices or build_system_prices("X", "wedge", "short", 108, evidence)
    return ScoredSignal(
        symbol="X",
        signal_type="wedge",
        direction="short",
        market="crypto",
        llm_entry_min=prices["entry_min"],
        llm_entry_max=prices["entry_max"],
        llm_stop_loss=prices["stop_loss"],
        llm_tp1=prices["tp1"],
        llm_tp2=prices["tp2"],
        llm_score=60,
        llm_confidence=0.6,
        llm_rr=prices["execution_rr"],
        current_price=108,
        structure_evidence=evidence,
        invalid_condition="push_3 acceleration or break above stop",
    )


def valid_prices():
    return build_system_prices("X", "wedge", "short", 108, valid_top_evidence())


def wedge_violations(result):
    return [v for v in result.guardrail_violations if "wedge" in v]


def test_valid_wedge_guardrail_has_no_wedge_specific_violations():
    result = apply_guardrails(make_signal())

    assert result.final_grade != "REJECT"
    assert wedge_violations(result) == []


def test_missing_push_rejected_by_wedge_guardrail():
    evidence = valid_top_evidence()
    evidence.pop("push_3")
    evidence.pop("push_3_price")
    result = apply_guardrails(make_signal(evidence=evidence, prices=valid_prices()))

    assert any("wedge缺少三推" in v for v in result.guardrail_violations)


def test_spacing_and_duration_are_checked():
    evidence = valid_top_evidence()
    evidence["push_2_index"] = 12
    evidence["push_3_index"] = 20
    evidence["push_spacing_bars"] = 2
    evidence["wedge_duration_bars"] = 10
    result = apply_guardrails(make_signal(evidence=evidence, prices=valid_prices()))

    assert any("push spacing" in v for v in result.guardrail_violations)
    assert any("duration" in v for v in result.guardrail_violations)


def test_push_3_must_be_confirmed():
    evidence = valid_top_evidence()
    evidence["push_3_confirmed"] = False
    result = apply_guardrails(make_signal(evidence=evidence, prices=valid_prices()))

    assert any("push_3未确认" in v for v in result.guardrail_violations)


def test_acceleration_after_push_3_is_blocked():
    evidence = valid_top_evidence()
    evidence["post_push_3_acceleration"] = True
    result = apply_guardrails(make_signal(evidence=evidence, prices=valid_prices()))

    assert any("同向加速" in v for v in result.guardrail_violations)


def test_wedge_rr_must_pass_reversal_minimum():
    prices = {
        "entry_min": 107.8,
        "entry_max": 108.0,
        "stop_loss": 109.0,
        "tp1": 106.5,
        "tp2": 105.0,
        "execution_rr": 1.27,
    }
    result = apply_guardrails(make_signal(prices=prices))

    assert any("wedge RR不足" in v for v in result.guardrail_violations)
