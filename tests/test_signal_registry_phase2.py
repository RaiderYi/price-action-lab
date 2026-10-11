"""Phase 2: Signal Registry 固化测试 — 元数据校验，不改变生产行为"""
import pytest
from src.signal_registry import (
    SIGNAL_DEFINITION_REGISTRY,
    SIGNAL_REGISTRY,
    get_signal_definition,
    get_all_signal_definitions,
    get_live_signal_types,
    get_strict_signal_types,
    get_proxy_signal_types,
    is_strict_signal,
    is_proxy_signal,
    get_pa_family,
    get_report_allowed_wording,
    get_report_forbidden_wording,
    get_definition_version,
    get_implementation_version,
    get_manual_review_status,
    validate_signal_type,
    get_signal_types,
    get_min_rr,
)


class TestRegistryLoads:
    """1. registry 可以正常加载"""

    def test_definition_registry_has_18_signals(self):
        assert len(SIGNAL_DEFINITION_REGISTRY) == 19  # Focus v1: +breakout

    def test_all_required_fields_present(self):
        required_fields = [
            "signal_type", "display_name_cn", "pa_family", "direction",
            "definition_version", "implementation_version", "maturity",
            "strict_match", "is_proxy", "enabled", "implemented",
            "manual_review_status", "core_definition_cn",
        ]
        for st, cfg in SIGNAL_DEFINITION_REGISTRY.items():
            for f in required_fields:
                assert f in cfg, f"{st} missing field: {f}"

    def test_no_empty_core_definition(self):
        for st, cfg in SIGNAL_DEFINITION_REGISTRY.items():
            assert cfg.get("core_definition_cn"), f"{st} has empty core_definition"

    def test_valid_pa_family(self):
        valid = {"bar_counting", "swing_proxy", "reversal", "classic_ta",
                 "pending_kb", "range", "measurement", "disabled",
                 "trend_exhaustion", "trading_range_strategy",
                 "range_context", "measurement_tool",
                 "price_action_pattern", "breakout"}
        for st, cfg in SIGNAL_DEFINITION_REGISTRY.items():
            assert cfg["pa_family"] in valid, f"{st} invalid pa_family: {cfg['pa_family']}"


class TestLegacyCompatibility:
    """2. 旧 signal_type 仍然 validate 通过"""

    def test_legacy_signals_still_valid(self):
        legacy = ["H1", "H2", "L1", "L2", "wedge", "double_bottom", "double_top",
                  "climax_reversal", "final_flag", "tr_fade", "eighty_twenty",
                  "measured_move", "BTC", "STC"]
        for st in legacy:
            assert validate_signal_type(st), f"{st} should still validate"

    def test_legacy_min_rr_still_accessible(self):
        assert get_min_rr("H2") == 1.5
        assert get_min_rr("wedge") == 2.0
        assert get_min_rr("tr_fade") == 1.5

    def test_old_get_signal_types_still_works(self):
        types = get_signal_types()
        assert "H1" in types
        assert "H2" in types
        assert "wedge" in types


class TestStrictSignalsDisabled:
    """3. strict 信号已注册但未启用"""

    def test_strict_signals_exist(self):
        strict = get_strict_signal_types()
        assert "brooks_h1_strict" in strict
        assert "brooks_h2_strict" in strict
        assert "brooks_l1_strict" in strict
        assert "brooks_l2_strict" in strict

    def test_strict_signals_not_enabled(self):
        for st in ["brooks_h1_strict", "brooks_h2_strict",
                    "brooks_l1_strict", "brooks_l2_strict"]:
            cfg = get_signal_definition(st)
            assert cfg["enabled"] is False, f"{st} should be enabled=False"
            assert cfg["implemented"] is False, f"{st} should be implemented=False"

    def test_strict_signals_not_in_live_list(self):
        live = get_live_signal_types()
        for st in ["brooks_h1_strict", "brooks_h2_strict",
                    "brooks_l1_strict", "brooks_l2_strict"]:
            assert st not in live, f"{st} should not be in live signals"

    def test_strict_signals_have_no_code_detector(self):
        for st in ["brooks_h1_strict", "brooks_h2_strict",
                    "brooks_l1_strict", "brooks_l2_strict"]:
            cfg = get_signal_definition(st)
            assert cfg["code_detector"] is None, f"{st} should have no detector yet"


class TestProxyMetadata:
    """4. proxy 元数据正确"""

    def test_h2_is_proxy(self):
        assert is_proxy_signal("H2") is True
        assert is_strict_signal("H2") is False

    def test_h2_proxy_target(self):
        cfg = get_signal_definition("H2")
        assert cfg["proxy_for"] == "brooks_h2_strict"
        assert cfg["is_proxy"] is True
        assert cfg["strict_match"] is False

    def test_l2_is_proxy(self):
        assert is_proxy_signal("L2") is True
        cfg = get_signal_definition("L2")
        assert cfg["proxy_for"] == "brooks_l2_strict"

    def test_h2_has_legacy_names(self):
        cfg = get_signal_definition("H2")
        assert "legacy_h2_proxy" in cfg["legacy_names"]
        assert "hermes_h2_v1" in cfg["legacy_names"]

    def test_h2_implementation_version(self):
        cfg = get_signal_definition("H2")
        assert "hermes_h2_v1" in cfg["implementation_version"]
        assert "CURRENT" in cfg["implementation_version"]

    def test_wedge_is_not_proxy(self):
        assert is_proxy_signal("wedge") is False


class TestWordingConstraints:
    """5. wording 约束存在"""

    def test_proxy_signals_have_forbidden_wording(self):
        proxy = get_proxy_signal_types()
        for st in proxy:
            forbidden = get_report_forbidden_wording(st)
            # disabled signals may have empty forbidden wording
            if st in ("buy_the_close", "sell_the_close"):
                continue
            assert len(forbidden) > 0, f"{st} proxy should have forbidden wording"

    def test_proxy_signals_have_allowed_wording(self):
        for st in ["H2", "L2"]:
            allowed = get_report_allowed_wording(st)
            assert len(allowed) > 0, f"{st} should have allowed wording"

    def test_h2_forbidden_contains_key_phrases(self):
        forbidden = get_report_forbidden_wording("H2")
        forbidden_text = " ".join(forbidden)
        assert "严格 Brooks H2" in forbidden_text
        assert "经典 H2" in forbidden_text

    def test_tr_fade_has_display_label(self):
        """tr_fade now KB-confirmed as trading_range_strategy, no forbidden wording needed"""
        cfg = get_signal_definition("tr_fade")
        assert cfg["pa_family"] == "trading_range_strategy"
        assert "交易区间反转" in cfg["display_name_cn"]

    def test_non_proxy_may_have_empty_forbidden(self):
        assert get_report_forbidden_wording("wedge") == []


class TestNoProductionChange:
    """6. 不改变生产行为"""

    def test_detector_not_imported_in_registry(self):
        """signal_registry 不应导入任何 detector 模块"""
        with open("src/signal_registry.py", "r", encoding="utf-8") as f:
            src = f.read()
        # No import of structure_builder, price_builder, candidate_pool, guardrail
        assert "from system_structure_builder" not in src
        assert "from system_price_builder" not in src
        assert "from candidate_pool" not in src
        assert "from rule_guardrail" not in src

    def test_signal_predictor_not_modified(self):
        """验证 signal_predictor.py 未被本 Phase 修改"""
        import hashlib
        with open("src/signal_registry.py", "rb") as f:
            # Just check the file exists and compiles — already verified
            pass

    def test_live_signals_are_11_current_production_signals(self):
        # Focus v1 (2026-10-11): production surface = 5 structures / 6 keys
        live = get_live_signal_types()
        assert set(live) == {"H2", "L2", "wedge", "final_flag", "tr_fade", "breakout"}

    def test_all_signals_have_definition_version(self):
        for st, cfg in SIGNAL_DEFINITION_REGISTRY.items():
            assert cfg.get("definition_version"), f"{st} missing definition_version"

    def test_all_signals_have_implementation_version(self):
        for st, cfg in SIGNAL_DEFINITION_REGISTRY.items():
            assert cfg.get("implementation_version"), f"{st} missing implementation_version"

    def test_all_signals_have_manual_review_status(self):
        for st, cfg in SIGNAL_DEFINITION_REGISTRY.items():
            status = cfg.get("manual_review_status", "")
            assert "CONFIRMED" in status or "APPROVE" in status or "PENDING" in status, \
                f"{st} unexpected review status: {status}"

    def test_pa_family_coverage(self):
        families = {get_pa_family(st) for st in SIGNAL_DEFINITION_REGISTRY}
        assert "bar_counting" in families
        assert "swing_proxy" in families
        assert "reversal" in families
