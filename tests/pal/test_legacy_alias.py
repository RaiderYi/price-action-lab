"""S1-03 测试：legacy 别名与统计分离。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.signals.legacy import ALIAS_MAP, canonical_signal_id


class TestAliasMap:
    def test_all_live_families_mapped(self):
        for fam in ("H2", "L2", "breakout", "wedge", "final_flag", "tr_fade"):
            assert fam in ALIAS_MAP

    def test_unknown_key_rejected(self):
        with pytest.raises(KeyError, match="未知 legacy"):
            canonical_signal_id("h2_typo", "SSE.600519", "2026-10-12T10:00+08:00")


class TestStatisticalSeparation:
    def test_legacy_h2_never_equals_strict_h2(self):
        """F01/F02 验收核心：同一票同一时刻，两种血统 ID 必须不同。"""
        from pal.domain.identity import make_setup_id
        iid, ts = "SSE.600519", "2026-10-12T10:00+08:00"
        legacy_id = canonical_signal_id("H2", iid, ts)
        strict_id = make_setup_id(iid, "H2", "strict", ts)
        # legacy_id 是 setup_id 加血统后缀；其前段（内容hash）与 strict 不同
        legacy_hash_part = legacy_id.split("|")[0]
        assert legacy_hash_part != str(strict_id)

    def test_legacy_id_deterministic(self):
        a = canonical_signal_id("H2", "SSE.600519", "2026-10-12T10:00+08:00")
        b = canonical_signal_id("H2", "SSE.600519", "2026-10-12T10:00+08:00")
        assert a == b

    def test_different_instruments_different_id(self):
        a = canonical_signal_id("H2", "SSE.600519", "2026-10-12T10:00+08:00")
        b = canonical_signal_id("H2", "SZSE.000001", "2026-10-12T10:00+08:00")
        assert a != b
