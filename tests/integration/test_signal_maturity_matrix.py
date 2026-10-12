"""P8: 信号成熟度矩阵 + 准入门禁测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from signal_maturity import (
    SIGNAL_MATURITY, get_maturity, can_enter_main_shortlist,
    is_disabled, get_max_grade, get_aliases,
    is_context_feature_allowed, is_production_entry_allowed, is_target_engine
)


class TestSignalMaturityMatrix:
    """P8: 成熟度分级"""

    def test_trade_ready_can_enter_main(self):
        for st in ["H1", "H2", "L1", "L2"]:
            assert can_enter_main_shortlist(st), f"{st} should be TRADE_READY"

    def test_structure_ready_not_in_main(self):
        for st in ["wedge", "tr_fade", "measured_move", "double_bottom", "double_top"]:
            assert not can_enter_main_shortlist(st), f"{st} should NOT enter main"

    def test_research_only_not_in_main(self):
        for st in ["buy_the_close", "sell_the_close", "climax_reversal", "final_flag", "eighty_twenty"]:
            assert not can_enter_main_shortlist(st), f"{st} should NOT enter main"

    def test_disabled_signals(self):
        for st in ["BTC", "STC"]:
            assert is_disabled(st), f"{st} should be DISABLED"

    def test_all_signals_have_maturity(self):
        for st, info in SIGNAL_MATURITY.items():
            assert info.get("maturity") in ("TRADE_READY", "STRUCTURE_READY", "RESEARCH_ONLY", "DISABLED"), \
                f"{st}: missing or invalid maturity"

    def test_trade_ready_has_kb(self):
        for st, info in SIGNAL_MATURITY.items():
            if info["maturity"] == "TRADE_READY":
                assert info.get("kb_complete"), f"{st}: TRADE_READY but KB incomplete"

    def test_aliases_map_btc_stc(self):
        aliases = get_aliases()
        assert aliases["BTC"] == "buy_the_close"
        assert aliases["STC"] == "sell_the_close"

    def test_h2_max_grade_is_a(self):
        assert get_max_grade("H2") == "A"

    def test_wedge_max_grade_is_observe(self):
        assert get_max_grade("wedge") in ("OBSERVE", "C")

    def test_research_only_returns_research(self):
        assert get_maturity("climax_reversal") == "RESEARCH_ONLY"

    def test_measured_move_target_engine(self):
        assert get_maturity("measured_move") == "STRUCTURE_READY"
        assert is_target_engine("measured_move")
        assert not is_production_entry_allowed("measured_move")

    def test_context_features_are_not_entries(self):
        for st in ["tr_fade", "buy_the_close", "sell_the_close"]:
            assert is_context_feature_allowed(st)
            assert not is_production_entry_allowed(st)


class TestMaturityGate:
    """P8: 成熟度准入门禁"""

    def test_trade_ready_passes(self):
        assert can_enter_main_shortlist("H2")
        assert can_enter_main_shortlist("L2")

    def test_disabled_blocked(self):
        assert is_disabled("BTC")
        assert is_disabled("STC")
        assert not can_enter_main_shortlist("BTC")

    def test_unknown_signal_defaults_research(self):
        assert get_maturity("nonexistent_signal") == "RESEARCH_ONLY"
        assert not can_enter_main_shortlist("nonexistent_signal")
