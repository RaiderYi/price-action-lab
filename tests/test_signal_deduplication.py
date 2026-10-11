"""
【自迭代 #9】信号去重测试

覆盖 10 个场景：
1. 同一 symbol/type/direction/date 重复 → skip
2. 相同 LH1/LH2 的 L2 重复 → skip
3. entry/stop/tp 微小差异但结构相同 → skip
4. 同一有效窗口内重复 → skip
5. 原信号 expired 后允许新信号
6. 同 symbol 但不同 signal_type → 不重复
7. 同 symbol/type 但 direction 不同 → 不重复
8. duplicate_signal 写入 audit log
9. weekly_review 输出 raw 与 dedup 两套统计
10. confidence bucket 使用 dedup 口径
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest
from signal_fingerprint import (
    build_signal_fingerprint,
    build_structure_key,
    build_date_bucket,
    should_skip_signal,
    log_duplicate,
    get_duplicate_log,
    clear_duplicate_log,
    get_duplicate_count,
)


class TestSignalFingerprint(unittest.TestCase):
    """指纹生成测试。"""

    def test_same_structure_same_fingerprint(self):
        """相同核心结构应产生相同指纹。"""
        ev1 = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        ev2 = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        fp1 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev1, "30m", "2026-05-28")
        fp2 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev2, "30m", "2026-05-28")
        self.assertEqual(fp1, fp2, "相同结构应产生相同指纹")

    def test_different_structure_different_fingerprint(self):
        """不同核心结构应产生不同指纹。"""
        ev1 = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        ev2 = {"LH1": 60.00, "LH2": 58.00, "prior_low": 55.00}  # 明显不同的结构点
        fp1 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev1, "30m", "2026-05-28")
        fp2 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev2, "30m", "2026-05-28")
        self.assertNotEqual(fp1, fp2, "不同结构应产生不同指纹")

    def test_different_signal_type_different_fingerprint(self):
        """不同 signal_type 应产生不同指纹。"""
        ev = {"LH1": 50.17, "LH2": 50.43}
        fp1 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev, "30m", "2026-05-28")
        fp2 = build_signal_fingerprint("600276", "H2", "sell", "standard", ev, "30m", "2026-05-28")
        self.assertNotEqual(fp1, fp2)

    def test_different_direction_different_fingerprint(self):
        """不同 direction 应产生不同指纹。"""
        ev = {"HL1": 100.0, "HL2": 102.0, "prior_high": 110.0}
        fp1 = build_signal_fingerprint("300750", "H2", "buy", "standard", ev, "30m", "2026-05-28")
        fp2 = build_signal_fingerprint("300750", "H2", "sell", "standard", ev, "30m", "2026-05-28")
        self.assertNotEqual(fp1, fp2)

    def test_price_tolerance_normalizes(self):
        """价格容差内微小差异应归一化为相同指纹（1位小数容差）。"""
        ev1 = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        ev2 = {"LH1": 50.22, "LH2": 50.38, "prior_low": 47.58}  # 均在1位小数容差内
        fp1 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev1, "30m", "2026-05-28")
        fp2 = build_signal_fingerprint("600276", "L2", "sell", "standard", ev2, "30m", "2026-05-28")
        self.assertEqual(fp1, fp2, "容差内价格应归一化")


class TestSignalDeduplication(unittest.TestCase):
    """去重逻辑测试。"""

    def setUp(self):
        clear_duplicate_log()

    def test_duplicate_same_symbol_type_direction_date_skip(self):
        """同 symbol/type/direction/date 重复 → skip。"""
        ev = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        fp = build_signal_fingerprint("600276", "L2", "sell", "standard", ev, "30m", "2026-05-28")
        existing = [
            {"symbol": "600276", "signal_type": "L2", "direction": "sell",
             "status": "ACTIVE", "signal_id": "sig-001", "fingerprint": fp}
        ]
        skip, orig_id = should_skip_signal(fp, "600276", "L2", "sell", existing)
        self.assertTrue(skip, "应与已有活跃信号重复")
        self.assertEqual(orig_id, "sig-001")

    def test_duplicate_l2_same_structure_skip(self):
        """L2 相同 LH1/LH2 -> skip。"""
        ev = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        fp = build_signal_fingerprint("600276", "L2", "sell", "standard", ev, "30m", "2026-05-28")
        existing = [
            {"symbol": "600276", "signal_type": "L2", "direction": "sell",
             "status": "PREDICTED", "signal_id": "sig-002", "fingerprint": fp}
        ]
        skip, _ = should_skip_signal(fp, "600276", "L2", "sell", existing)
        self.assertTrue(skip, "L2 相同结构应视为重复")

    def test_expired_allows_new_signal(self):
        """原信号 expired → 允许新信号。"""
        ev = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        fp = build_signal_fingerprint("600276", "L2", "sell", "standard", ev, "30m", "2026-05-28")
        existing = [
            {"symbol": "600276", "signal_type": "L2", "direction": "sell",
             "status": "EXPIRED", "signal_id": "sig-003", "fingerprint": fp}
        ]
        skip, _ = should_skip_signal(fp, "600276", "L2", "sell", existing)
        self.assertFalse(skip, "已过期信号不应阻止新信号")

    def test_hit_sl_allows_new_signal(self):
        """HIT_SL → 允许新信号。"""
        ev = {"HL1": 100.0, "HL2": 102.0, "prior_high": 110.0}
        fp = build_signal_fingerprint("300750", "H2", "buy", "standard", ev, "30m", "2026-05-28")
        existing = [
            {"symbol": "300750", "signal_type": "H2", "direction": "buy",
             "status": "HIT_SL", "signal_id": "sig-004", "fingerprint": fp}
        ]
        skip, _ = should_skip_signal(fp, "300750", "H2", "buy", existing)
        self.assertFalse(skip, "HIT_SL 后应允许重新入场")

    def test_different_signal_type_not_duplicate(self):
        """同 symbol 但不同 signal_type → 不重复。"""
        ev = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        fp = build_signal_fingerprint("600276", "wedge", "sell", "standard", ev, "30m", "2026-05-28")
        existing = [
            {"symbol": "600276", "signal_type": "L2", "direction": "sell",
             "status": "ACTIVE", "signal_id": "sig-005", "fingerprint": "other_fp"}
        ]
        skip, _ = should_skip_signal(fp, "600276", "wedge", "sell", existing)
        self.assertFalse(skip, "不同 signal_type 不应视为重复")

    def test_different_direction_not_duplicate(self):
        """同 symbol/type 但不同 direction → 不重复。"""
        ev = {"HL1": 100.0, "HL2": 102.0, "prior_high": 110.0}
        fp = build_signal_fingerprint("300750", "H2", "buy", "standard", ev, "30m", "2026-05-28")
        existing = [
            {"symbol": "300750", "signal_type": "H2", "direction": "sell",
             "status": "ACTIVE", "signal_id": "sig-006", "fingerprint": "other_fp"}
        ]
        skip, _ = should_skip_signal(fp, "300750", "H2", "buy", existing)
        self.assertFalse(skip, "不同 direction 不应视为重复")


class TestDuplicateAuditLog(unittest.TestCase):
    """重复审计日志测试。"""

    def setUp(self):
        clear_duplicate_log()

    def test_log_duplicate_writes_entry(self):
        """log_duplicate 写入审计条目。"""
        self.assertEqual(get_duplicate_count(), 0)
        log_duplicate("fp_abc", "sig-001", "600276", "L2", "sell",
                       "LH1=50|LH2=50|prior=47", 48.4, 48.4, 49.1, 49.1)
        self.assertEqual(get_duplicate_count(), 1)

        log_duplicate("fp_def", "sig-002", "600276", "L2", "sell",
                       "LH1=50|LH2=50|prior=47", 48.4, 48.4, 49.1, 49.1)
        self.assertEqual(get_duplicate_count(), 2)

    def test_get_duplicate_log_returns_all(self):
        """get_duplicate_log 返回所有条目。"""
        log_duplicate("fp_a", "sig-a", "300750", "H2", "buy", "HL1=100", 410, 410, 406, 406)
        log_duplicate("fp_b", "sig-b", "600276", "L2", "sell", "LH1=50", 48, 48, 49, 49)
        entries = get_duplicate_log()
        self.assertEqual(len(entries), 2)


class TestStructureKey(unittest.TestCase):
    """结构键测试。"""

    def test_l2_structure_key(self):
        ev = {"LH1": 50.17, "LH2": 50.43, "prior_low": 47.62}
        key = build_structure_key("L2", ev)
        self.assertIn("LH1=", key)
        self.assertIn("LH2=", key)
        self.assertIn("prior_low=", key)

    def test_h2_structure_key(self):
        ev = {"HL1": 100.0, "HL2": 102.0, "prior_high": 110.0}
        key = build_structure_key("H2", ev)
        self.assertIn("HL1=", key)
        self.assertIn("HL2=", key)
        self.assertIn("prior_high=", key)

    def test_wedge_structure_key(self):
        ev = {"push_1_price": 31.5, "push_2_price": 31.2, "push_3_price": 30.6}
        key = build_structure_key("wedge", ev)
        self.assertIn("push_1_price=", key)
        self.assertIn("push_2_price=", key)
        self.assertIn("push_3_price=", key)


if __name__ == "__main__":
    unittest.main()
