"""P7.6: RR Precheck + No-Trade Day 测试"""
import pytest, sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from candidate_pool import Candidate, select_main_and_scan
from signal_maturity import SIGNAL_MATURITY


def make_candidate(symbol, st, dr, structure_status, price_build, exec_rr, tq, market="A股"):
    c = Candidate(symbol=symbol, signal_type=st, direction=dr, market=market)
    c.structure_status = structure_status
    c.price_build_type = price_build
    c.execution_rr = exec_rr
    c.trade_quality_after_penalty = tq
    return c


class TestRRPrecheck:
    def test_h2_rr_pass_enters_main(self):
        c = make_candidate("X", "H2", "long", "verified", "strong", 2.0, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert len(main) == 1

    def test_h2_rr_fail_goes_to_rr_insufficient(self):
        c = make_candidate("X", "H2", "long", "verified", "strong", 0.86, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert len(main) == 0
        assert len(rr_insuff) == 1
        assert len(pending) == 0

    def test_a_share_short_needs_1_8_rr(self):
        c = make_candidate("X", "L2", "short", "verified", "strong", 1.6, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert len(main) == 0  # 1.6 < 1.8
        assert len(rr_insuff) == 1

    def test_structure_ready_not_in_main(self):
        c = make_candidate("X", "wedge", "short", "verified", "strong", 3.0, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert len(main) == 0  # wedge is STRUCTURE_READY, not TRADE_READY

    def test_weak_structure_not_in_main(self):
        c = make_candidate("X", "H2", "long", "weak", "weak", 3.0, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert len(main) == 0

    def test_verified_but_rr_insufficient_not_in_main(self):
        c = make_candidate("600030", "L2", "short", "verified", "strong", 1.2, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert c in rr_insuff
        assert c not in main

    def test_no_trade_day_when_empty_main(self):
        c1 = make_candidate("A", "H2", "long", "verified", "strong", 0.5, 60)
        c2 = make_candidate("B", "L2", "short", "verified", "strong", 1.0, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c1, c2])
        assert len(main) == 0
        assert len(rr_insuff) == 2


class TestNoTradeDay:
    def test_no_trade_day_triggered(self):
        main, scan, pending, rr_insuff = select_main_and_scan([])
        assert len(main) == 0

    def test_rr_insufficient_has_reason(self):
        c = make_candidate("X", "H2", "long", "verified", "strong", 0.5, 60)
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert "RR不足" in c.not_selected_reason

    def test_disabled_not_in_candidates(self):
        c = make_candidate("Y", "BTC", "long", "verified", "strong", 2.0, 60)
        c.structure_status = "blocked_by_maturity"
        c.price_build_type = "none"
        main, scan, pending, rr_insuff = select_main_and_scan([c])
        assert len(main) == 0
