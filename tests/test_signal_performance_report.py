"""
P5.1: signal_performance_report 口径校准测试
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from signal_performance_report import (
    compute_stats, is_closed_trade, is_non_trade, is_active,
    is_win, is_loss, safe_avg, safe_median,
    by_signal_type, by_direction, active_aging,
    CLOSED_TRADE_STATUSES, NON_TRADE_STATUSES, ACTIVE_STATUSES,
)


class TestStatusClassification(unittest.TestCase):

    def test_closed_trade_only_real_outcomes(self):
        self.assertIn("HIT_TP2", CLOSED_TRADE_STATUSES)
        self.assertIn("HIT_SL", CLOSED_TRADE_STATUSES)
        self.assertIn("EXPIRED", CLOSED_TRADE_STATUSES)
        self.assertNotIn("EXCLUDED_LEGACY_FAKE_PRICE", CLOSED_TRADE_STATUSES)
        self.assertNotIn("DUPLICATE_SUPPRESSED", CLOSED_TRADE_STATUSES)

    def test_non_trade_excluded_not_in_closed(self):
        for s in NON_TRADE_STATUSES:
            self.assertNotIn(s, CLOSED_TRADE_STATUSES)

    def test_active_not_in_closed(self):
        for s in ACTIVE_STATUSES:
            self.assertNotIn(s, CLOSED_TRADE_STATUSES)

    def test_is_closed_trade(self):
        self.assertTrue(is_closed_trade("HIT_TP2"))
        self.assertTrue(is_closed_trade("HIT_SL"))
        self.assertTrue(is_closed_trade("EXPIRED"))
        self.assertFalse(is_closed_trade("PREDICTED"))
        self.assertFalse(is_closed_trade("EXCLUDED_NON_TRADE_READY"))
        self.assertFalse(is_closed_trade("DUPLICATE_SUPPRESSED"))


class TestComputeStatsCalibrated(unittest.TestCase):

    def setUp(self):
        self.signals = [
            {"id": "1", "symbol": "A", "signal_type": "H2", "direction": "buy",
             "current_status": "HIT_TP2", "pnl_r": 2.0, "timestamp": "2026-01-01T00:00:00"},
            {"id": "2", "symbol": "B", "signal_type": "H2", "direction": "buy",
             "current_status": "HIT_SL", "pnl_r": -1.0, "timestamp": "2026-01-02T00:00:00"},
            {"id": "3", "symbol": "C", "signal_type": "L2", "direction": "sell",
             "current_status": "EXPIRED", "pnl_r": 0.0, "timestamp": "2026-01-03T00:00:00"},
            {"id": "4", "symbol": "D", "signal_type": "H2", "direction": "buy",
             "current_status": "PREDICTED", "pnl_r": None, "timestamp": "2026-01-04T00:00:00"},
            {"id": "5", "symbol": "E", "signal_type": "H2", "direction": "buy",
             "current_status": "EXCLUDED_NON_TRADE_READY", "pnl_r": 0.0, "timestamp": "2026-01-05T00:00:00"},
            {"id": "6", "symbol": "F", "signal_type": "L2", "direction": "sell",
             "current_status": "DUPLICATE_SUPPRESSED", "pnl_r": 0.0, "timestamp": "2026-01-06T00:00:00"},
            {"id": "7", "symbol": "G", "signal_type": "H2", "direction": "buy",
             "current_status": "ACTIVE", "pnl_r": None, "timestamp": "2026-01-07T00:00:00"},
        ]

    def test_excluded_not_in_closed_trade(self):
        s = compute_stats(self.signals)
        self.assertEqual(s["closed_trades"], 3)  # 1(HIT_TP2),2(HIT_SL),3(EXPIRED)
        self.assertEqual(s["non_trade_filtered"], 2)  # 5(EXCLUDED),6(DUPLICATE)
        self.assertEqual(s["active_open"], 2)  # 4(PREDICTED),7(ACTIVE)

    def test_win_rate_denominator_is_closed_trades(self):
        s = compute_stats(self.signals)
        self.assertEqual(s["hit_tp"], 1)
        self.assertEqual(s["hit_sl"], 1)
        self.assertEqual(s["expired"], 1)
        self.assertAlmostEqual(s["win_rate_closed"], 1/3, places=3)
        self.assertAlmostEqual(s["stop_rate_closed"], 1/3, places=3)
        self.assertAlmostEqual(s["expiry_rate_closed"], 1/3, places=3)

    def test_predicted_not_in_win_rate(self):
        signals = [
            {"id": "1", "symbol": "A", "signal_type": "H2", "direction": "buy",
             "current_status": "PREDICTED", "pnl_r": None, "timestamp": "2026-01-01T00:00:00"},
        ]
        s = compute_stats(signals)
        self.assertEqual(s["closed_trades"], 0)
        self.assertEqual(s["win_rate_closed"], 0)

    def test_only_excluded_signals(self):
        signals = [
            {"id": "1", "symbol": "A", "signal_type": "H2", "direction": "buy",
             "current_status": "EXCLUDED_NON_TRADE_READY", "pnl_r": 0.0, "timestamp": "2026-01-01T00:00:00"},
        ]
        s = compute_stats(signals)
        self.assertEqual(s["closed_trades"], 0)
        self.assertEqual(s["non_trade_filtered"], 1)

    def test_empty(self):
        s = compute_stats([])
        self.assertEqual(s["total_records"], 0)
        self.assertEqual(s["closed_trades"], 0)


if __name__ == "__main__":
    unittest.main()
