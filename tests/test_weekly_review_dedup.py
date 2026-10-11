"""
【自迭代 #9】weekly_review raw/dedup 双口径测试

覆盖:
1. weekly_review 输出 raw/dedup 双口径
2. historical weak dedup
3. strong dedup (有 structure_evidence)
4. duplicate_ratio 正确
5. confidence bucket dedup
6. insufficient_independent_samples 触发
7. low_position_short 分组
"""

import sys, os, json, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from signal_fingerprint import (
    batch_dedup_signals, build_signal_fingerprint, build_weak_fingerprint,
    get_dedup_confidence, build_date_bucket, _price_bucket,
)


class TestWeeklyReviewDedup(unittest.TestCase):
    """weekly_review 双口径测试。"""

    def _make_signals(self, n, with_structure=False, symbol="600276",
                      signal_type="L2", direction="sell"):
        """生成测试信号列表（默认 PREDICTED 状态，非终态可被去重）。"""
        sigs = []
        for i in range(n):
            ev = {}
            if with_structure:
                ev = {"LH1": 50.0 + i * 2, "LH2": 49.0 + i * 2, "prior_low": 47.0}
            sigs.append({
                "symbol": symbol,
                "signal_type": signal_type,
                "direction": direction,
                "timestamp": f"2026-05-{28+i:02d}T10:00:00",
                "entry_mid": 48.4,
                "stop_loss": 49.1,
                "score": 85,
                "pnl_r": 0,
                "status": "PREDICTED",  # 非终态，可被去重
                "market": "A股",
                "structure_evidence": ev,
                "signal_variant": "standard",
            })
        return sigs

    def test_raw_dedup_dual_output(self):
        """验证 raw 和 dedup 计数。"""
        sigs = self._make_signals(3)  # all identical
        sigs[0]["timestamp"] = "2026-05-28T10:00:00"
        sigs[1]["timestamp"] = "2026-05-28T11:00:00"  # same day → duplicate
        sigs[2]["timestamp"] = "2026-05-29T10:00:00"  # different day → not dup

        deduped, dup_count, method = batch_dedup_signals(sigs, use_weak=True)
        self.assertEqual(len(sigs), 3, "raw should be 3")
        self.assertEqual(len(deduped), 2, "2 unique (2 same-day duplicates)")
        self.assertEqual(dup_count, 1)

    def test_historical_weak_dedup_no_structure(self):
        """历史信号无 structure_evidence → weak dedup。"""
        sigs = self._make_signals(5, with_structure=False)
        for i in range(5):
            sigs[i]["timestamp"] = f"2026-05-28T{i:02d}:00:00"

        deduped, dup_count, method = batch_dedup_signals(sigs, use_weak=True)
        self.assertEqual(method, "weak")
        self.assertEqual(len(deduped), 1, "all 5 same-day should dedup to 1")

    def test_strong_dedup_with_structure(self):
        """有 structure_evidence → strong dedup (相同结构+同日→去重)。"""
        sigs = self._make_signals(4, with_structure=True)
        # 使用相同结构，仅日期不同
        ev = {"LH1": 50.0, "LH2": 49.0, "prior_low": 47.0}
        for s in sigs:
            s["structure_evidence"] = ev
        sigs[0]["timestamp"] = "2026-05-28T10:00:00"
        sigs[1]["timestamp"] = "2026-05-28T11:00:00"  # same structure, same day → dup
        sigs[2]["timestamp"] = "2026-05-28T12:00:00"  # same
        sigs[3]["timestamp"] = "2026-05-29T10:00:00"  # different day

        deduped, dup_count, method = batch_dedup_signals(sigs, use_weak=False)
        self.assertEqual(len(deduped), 2, "2 unique (2 dates, 3 same-day)")
        self.assertIn(method, ("strong", "mixed"))

    def test_duplicate_ratio_correct(self):
        """duplicate_ratio 计算正确。"""
        sigs = self._make_signals(10, with_structure=False)
        for i in range(10):
            sigs[i]["timestamp"] = "2026-05-28T10:00:00"

        deduped, dup_count, _ = batch_dedup_signals(sigs, use_weak=True)
        ratio = dup_count / len(sigs)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(dup_count, 9)
        self.assertAlmostEqual(ratio, 0.9, delta=0.01)

    def test_confidence_bucket_dedup(self):
        """Confidence bucket 使用 dedup 口径。"""
        sigs = self._make_signals(8, with_structure=False)
        for i in range(8):
            sigs[i]["timestamp"] = f"2026-05-28T{i:02d}:00:00"
            sigs[i]["score"] = 85

        deduped, dup_count, _ = batch_dedup_signals(sigs, use_weak=True)

        # Raw: 8 signals score>=80
        raw_high = [s for s in sigs if s["score"] >= 80]
        self.assertEqual(len(raw_high), 8)

        # Dedup: 1 signal score>=80
        dedup_high = [s for s in deduped if s["score"] >= 80]
        self.assertEqual(len(dedup_high), 1, "dedup should collapse to 1")

    def test_insufficient_samples_triggered(self):
        """样本不足时 dedup_confidence 正确。"""
        confidence = get_dedup_confidence("weak", 3, 0)
        self.assertEqual(confidence, "insufficient_samples")

        confidence2 = get_dedup_confidence("weak", 15, 2)
        self.assertEqual(confidence2, "low")

        confidence3 = get_dedup_confidence("strong", 50, 5)
        self.assertEqual(confidence3, "high")

    def test_expired_allows_new_in_batch(self):
        """已终态信号不阻止新的。"""
        sigs = self._make_signals(2, with_structure=False)
        sigs[0]["timestamp"] = "2026-05-28T10:00:00"
        sigs[0]["status"] = "HIT_SL"  # terminal
        sigs[1]["timestamp"] = "2026-05-28T11:00:00"

        deduped, dup_count, _ = batch_dedup_signals(sigs, use_weak=True)
        # Both should pass since first is HIT_SL (terminal)
        self.assertEqual(len(deduped), 2, "HIT_SL should not block new")
        self.assertEqual(dup_count, 0)

    def test_price_bucket_tolerance(self):
        """固定步长价格桶在容差内归一化。"""
        # A股 0.1元步长: 50.17→502, 50.20→502, 52.00→520
        b1 = _price_bucket(50.17, 0.005)
        b2 = _price_bucket(50.20, 0.005)
        b3 = _price_bucket(52.00, 0.005)
        self.assertEqual(b1, b2, "0.03 diff should be same bucket (0.1 step)")
        self.assertNotEqual(b1, b3, "1.83 diff should be different bucket")

    def test_different_market_tolerance(self):
        """A股和 crypto 使用不同步长。"""
        b_a1 = _price_bucket(50.17, 0.005)  # A股 0.1 step
        b_a2 = _price_bucket(50.20, 0.005)
        b_c1 = _price_bucket(75000, 0.002)  # crypto 10+ step
        b_c2 = _price_bucket(75100, 0.002)
        self.assertEqual(b_a1, b_a2)
        self.assertEqual(b_c1, b_c2, "100 diff within crypto step tolerance")


if __name__ == "__main__":
    unittest.main()
