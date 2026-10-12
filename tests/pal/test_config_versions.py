"""S1-04 测试：配置版本化与漂移守卫。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.config.versions import (
    ActiveConfigGuard,
    ConfigDriftError,
    ConfigSnapshot,
    GOVERNED_DOMAINS,
    frozen_config_from_focus,
)


class TestConfigSnapshot:
    def test_snapshot_deterministic(self):
        a = frozen_config_from_focus()
        b = frozen_config_from_focus()
        assert a.config_version == b.config_version

    def test_all_governed_domains_present(self):
        snap = frozen_config_from_focus()
        assert set(snap.domains) >= set(GOVERNED_DOMAINS)

    def test_missing_domain_rejected(self):
        with pytest.raises(Exception, match="缺域"):
            ConfigSnapshot(config_version="abc", domains={"channel_filter": {}})

    def test_extreme_pct_is_fixed_value(self):
        """F03 修复后的阈值进入版本管控。"""
        snap = frozen_config_from_focus()
        assert snap.domains["channel_filter"]["breakout_close_extreme_pct"] == 0.7


class TestDriftGuard:
    def test_verify_ok_without_change(self):
        snap = frozen_config_from_focus()
        guard = ActiveConfigGuard(snap)
        with guard:
            guard.verify()  # 无改动 → 通过

    def test_verify_fails_after_mutation(self):
        import focus_config as fc
        snap = frozen_config_from_focus()
        guard = ActiveConfigGuard(snap)
        with guard:
            original = fc.CHANNEL_FILTER["breakout_lookback_bars"]
            try:
                fc.CHANNEL_FILTER["breakout_lookback_bars"] = 999
                with pytest.raises(ConfigDriftError, match="漂移"):
                    guard.verify()
            finally:
                fc.CHANNEL_FILTER["breakout_lookback_bars"] = original
        # 恢复后重新校验通过
        assert frozen_config_from_focus().config_version == snap.config_version

    def test_verify_outside_with_block_rejected(self):
        snap = frozen_config_from_focus()
        guard = ActiveConfigGuard(snap)
        with pytest.raises(ConfigDriftError):
            guard.verify()
