"""
P7: epoch (pre/post-fix) 分割测试
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from signal_performance_report import (
    split_by_epoch, epoch_stats, compute_stats,
    CLOSED_TRADE_STATUSES, NON_TRADE_STATUSES, ACTIVE_STATUSES,
)


class TestEpochSplit(unittest.TestCase):

    def setUp(self):
        self.signals = [
            {"id": "1", "symbol": "A", "signal_type": "H2", "direction": "buy",
             "current_status": "HIT_TP2", "pnl_r": 2.0, "timestamp": "2026-05-01T00:00:00"},
            {"id": "2", "symbol": "B", "signal_type": "L2", "direction": "sell",
             "current_status": "HIT_SL", "pnl_r": -1.0, "timestamp": "2026-06-01T00:00:00"},
            {"id": "3", "symbol": "C", "signal_type": "H2", "direction": "buy",
             "current_status": "PREDICTED", "pnl_r": None, "timestamp": "2026-06-03T00:00:00"},
            {"id": "4", "symbol": "D", "signal_type": "L2", "direction": "sell",
             "current_status": "HIT_TP2", "pnl_r": 3.0, "timestamp": "2026-06-05T00:00:00"},
            {"id": "5", "symbol": "E", "signal_type": "H2", "direction": "buy",
             "current_status": "EXPIRED", "pnl_r": 0.0, "timestamp": "2026-06-10T00:00:00"},
        ]

    def test_split_by_epoch(self):
        pre, post = split_by_epoch(self.signals, "2026-06-02")
        self.assertEqual(len(pre), 2)   # signals 1(May), 2(June 1 < June 2)
        self.assertEqual(len(post), 3)  # signals 3-5

    def test_post_fix_closed_trades(self):
        pre, post = split_by_epoch(self.signals, "2026-06-02")
        post_stats = compute_stats(post, "post-fix")
        # post closed: 4(HIT_TP2)+5(EXPIRED)=2, 3 is PREDICTED
        self.assertEqual(post_stats["closed_trades"], 2)

    def test_post_fix_zero_closed_no_crash(self):
        signals = [
            {"id": "1", "symbol": "A", "signal_type": "H2", "direction": "buy",
             "current_status": "PREDICTED", "pnl_r": None, "timestamp": "2026-06-03T00:00:00"},
        ]
        pre, post = split_by_epoch(signals, "2026-06-02")
        post_stats = compute_stats(post, "post-fix")
        self.assertEqual(post_stats["closed_trades"], 0)
        self.assertEqual(post_stats["win_rate_closed"], 0)

    def test_epoch_stats_structure(self):
        ed = epoch_stats(self.signals, "2026-06-02")
        self.assertIn("fix_date", ed)
        self.assertIn("pre_fix", ed)
        self.assertIn("post_fix", ed)
        self.assertEqual(ed["pre_fix"]["closed_trades"], 2)
        self.assertEqual(ed["post_fix"]["closed_trades"], 2)

    def test_excluded_still_excluded_in_epoch(self):
        signals = self.signals + [
            {"id": "6", "symbol": "F", "signal_type": "H2", "direction": "buy",
             "current_status": "EXCLUDED_NON_TRADE_READY", "pnl_r": 0.0, "timestamp": "2026-06-03T00:00:00"},
        ]
        pre, post = split_by_epoch(signals, "2026-06-02")
        post_stats = compute_stats(post, "post-fix")
        self.assertEqual(post_stats["non_trade_filtered"], 1)
        self.assertEqual(post_stats["closed_trades"], 2)  # unchanged (4+5, 2 went to pre)

    def test_active_open_by_epoch(self):
        pre, post = split_by_epoch(self.signals, "2026-06-02")
        post_stats = compute_stats(post, "post-fix")
        self.assertEqual(post_stats["active_open"], 1)  # signal 3 PREDICTED


if __name__ == "__main__":
    unittest.main()
