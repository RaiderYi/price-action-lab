import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from candidate_pool import Candidate, select_main_and_scan
from signal_maturity import (
    can_enter_main_shortlist,
    get_maturity,
    is_context_feature_allowed,
    is_disabled,
    is_production_entry_allowed,
)


def _candidate(signal_type):
    c = Candidate(symbol=f"X_{signal_type}", signal_type=signal_type, direction="long")
    c.structure_status = "verified"
    c.price_build_type = "strong"
    c.execution_rr = 5.0
    c.trade_quality_after_penalty = 100
    return c


def test_research_only_signals_cannot_enter_main_shortlist():
    for signal_type in [
        "climax_reversal",
        "final_flag",
        "eighty_twenty",
        "buy_the_close",
        "sell_the_close",
    ]:
        assert get_maturity(signal_type) == "RESEARCH_ONLY"
        assert not can_enter_main_shortlist(signal_type)
        assert not is_production_entry_allowed(signal_type)


def test_context_features_are_explicitly_non_entry():
    assert is_context_feature_allowed("tr_fade")
    assert is_context_feature_allowed("buy_the_close")
    assert is_context_feature_allowed("sell_the_close")

    for signal_type in ["tr_fade", "buy_the_close", "sell_the_close"]:
        assert not is_production_entry_allowed(signal_type)


def test_maturity_gate_blocks_non_trade_ready_even_if_verified():
    candidates = [
        _candidate("wedge"),
        _candidate("tr_fade"),
        _candidate("measured_move"),
        _candidate("double_bottom"),
        _candidate("double_top"),
        _candidate("climax_reversal"),
        _candidate("final_flag"),
        _candidate("eighty_twenty"),
        _candidate("buy_the_close"),
        _candidate("sell_the_close"),
    ]

    main, _scan, _pending, _rr_insufficient = select_main_and_scan(candidates)

    assert main == []


def test_disabled_aliases_remain_disabled():
    assert is_disabled("BTC")
    assert is_disabled("STC")
    assert not can_enter_main_shortlist("BTC")
    assert not can_enter_main_shortlist("STC")
