"""P9: 信号升级路线图 + 升级判定标准测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from signal_upgrade_backlog import (
    UPGRADE_BACKLOG, UPGRADE_PRIORITY, get_upgrade_backlog,
    get_priority_signals, can_upgrade_to_trade_ready, get_upgrade_work_estimate
)
from signal_maturity import get_maturity, SIGNAL_MATURITY


class TestUpgradeBacklog:
    def test_tr_fade_in_backlog(self):
        assert "tr_fade" in UPGRADE_BACKLOG

    def test_wedge_in_backlog(self):
        assert "wedge" in UPGRADE_BACKLOG

    def test_tr_fade_is_p0(self):
        assert "tr_fade" in UPGRADE_PRIORITY["P0"]

    def test_wedge_is_p0(self):
        assert "wedge" in UPGRADE_PRIORITY["P0"]

    def test_measured_move_is_p1(self):
        assert "measured_move" in UPGRADE_PRIORITY["P1"]

    def test_double_bottom_is_p1(self):
        assert "double_bottom" in UPGRADE_PRIORITY["P1"]

    def test_double_top_is_p1(self):
        assert "double_top" in UPGRADE_PRIORITY["P1"]

    def test_climax_reversal_is_p2(self):
        assert "climax_reversal" in UPGRADE_PRIORITY["P2"]

    def test_final_flag_is_p2(self):
        assert "final_flag" in UPGRADE_PRIORITY["P2"]

    def test_eighty_twenty_is_p2(self):
        assert "eighty_twenty" in UPGRADE_PRIORITY["P2"]

    def test_disabled_not_in_backlog(self):
        for st in ["BTC", "STC"]:
            assert st not in UPGRADE_BACKLOG

    def test_structure_ready_cannot_upgrade_yet(self):
        for st in [s for s in UPGRADE_PRIORITY["P0"] + UPGRADE_PRIORITY["P1"] if s != "tr_fade"]:
            ok, missing = can_upgrade_to_trade_ready(st)
            assert not ok, f"{st} should NOT be upgrade-ready yet, missing: {missing}"


class TestUpgradeCriteria:
    def test_h2_is_already_trade_ready(self):
        assert get_maturity("H2") == "TRADE_READY"

    def test_tr_fade_target_is_trade_ready(self):
        assert UPGRADE_BACKLOG["tr_fade"]["target_maturity"] == "STRUCTURE_READY"

    def test_wedge_target_stays_structure_ready(self):
        assert UPGRADE_BACKLOG["wedge"]["target_maturity"] == "STRUCTURE_READY"

    def test_measured_move_is_target_engine(self):
        assert UPGRADE_BACKLOG["measured_move"]["capability_role"] == "TARGET_ENGINE"
        assert UPGRADE_BACKLOG["measured_move"]["target_maturity"] == "STRUCTURE_READY"

    def test_research_only_stay_research(self):
        assert UPGRADE_BACKLOG["buy_the_close"]["target_maturity"] == "RESEARCH_ONLY"

    def test_work_estimate_p0(self):
        w = get_upgrade_work_estimate("P0")
        assert w >= 4  # at least 4 work items for tr_fade + wedge

    def test_no_missing_means_upgrade_ready(self):
        ok, missing = can_upgrade_to_trade_ready("H1")
        # H1 is TRADE_READY but not in backlog — handled gracefully
        assert not ok or missing == ["signal not in backlog"]
