"""S1-02/S1-03 测试：统一注册表 + legacy/strict 分立。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.domain.models import Implementation, Maturity
from pal.signals.registry import (
    REGISTRY,
    consistency_check,
    get_enabled_entries,
    get_entry,
    get_families,
)


class TestUniqueSource:
    def test_unknown_family_rejected(self):
        with pytest.raises(KeyError, match="未注册信号"):
            get_entry("dragon_fly", Implementation.LEGACY_PROXY)

    def test_breakout_now_registered_in_old_missing(self):
        """F15：旧 14 类注册表不含 breakout，新表必须含。"""
        e = get_entry("breakout", Implementation.LEGACY_PROXY)
        assert e.enabled and e.family == "breakout"

    def test_every_enabled_has_detector(self):
        for e in get_enabled_entries():
            assert e.detector, f"{e.family} enabled 但无检测器"

    def test_breakout_pricing_none_until_builder_exists(self):
        """F05：breakout/final_flag 无专用定价 builder → pricing=None（禁止 _generic 兜底）。"""
        for fam in ("breakout", "final_flag"):
            e = get_entry(fam, Implementation.LEGACY_PROXY)
            assert e.pricing_builder is None, (
                f"{fam} 在补齐结构定价 builder 前不得声明定价能力")


class TestLegacyStrictSeparation:
    def test_same_family_two_implementations_distinct(self):
        legacy = get_entry("H2", Implementation.LEGACY_PROXY)
        strict = get_entry("H2", Implementation.STRICT)
        assert legacy is not strict
        assert legacy.maturity == Maturity.PRODUCTION
        assert strict.maturity == Maturity.RESEARCH_ONLY   # F01：strict 未进交易路径

    def test_no_implementation_merging(self):
        combos = [k for k in REGISTRY if k[0] == "H2"]
        assert len(combos) == 2
        assert {k[1] for k in combos} == {Implementation.LEGACY_PROXY, Implementation.STRICT}

    def test_strict_families_present(self):
        fams = get_families(Implementation.STRICT)
        assert {"H1", "H2", "L1", "L2"} <= set(fams)

    def test_live_families_are_legacy_proxy_blood(self):
        for e in get_enabled_entries():
            assert e.implementation == Implementation.LEGACY_PROXY


class TestConsistencyAudit:
    def test_registry_matches_focus_config(self):
        rep = consistency_check()
        assert rep["consistent"], rep
        assert rep["diff_cfg_not_registry"] == []
        assert rep["diff_registry_not_cfg"] == []

    def test_enabled_matches_taskbook_live_set(self):
        fams = {e.family for e in get_enabled_entries()}
        assert fams == {"H2", "L2", "breakout", "wedge", "final_flag", "tr_fade"}
