"""M11: brooks_ontology_registry tests"""
import pytest
from brooks_ontology_registry import (
    BROOKS_ENTRY_SIGNAL_REGISTRY, BROOKS_LEGACY_PROXY_REGISTRY,
    BROOKS_PATTERN_REGISTRY, BROOKS_CONTEXT_REGISTRY,
    BROOKS_TARGET_REGISTRY, BROOKS_RISK_REGISTRY, BROOKS_ALIAS_REGISTRY,
    get_brooks_category, is_brooks_entry_signal, is_legacy_proxy_signal,
    get_ontology_record, get_proxy_display_label, get_registry_destination,
    list_entry_signals, list_legacy_proxies,
)


class TestEntrySignals:
    def test_bar_counting_signals_present(self):
        for s in ("brooks_h1_strict", "brooks_h2_strict", "brooks_l1_strict", "brooks_l2_strict"):
            assert s in BROOKS_ENTRY_SIGNAL_REGISTRY, f"{s} missing from EntrySignal registry"

    def test_climax_reversal_in_entry(self):
        assert "climax_reversal" in BROOKS_ENTRY_SIGNAL_REGISTRY

    def test_mtr_signals_present(self):
        for s in ("major_trend_reversal", "higher_low_mtr", "lower_high_mtr"):
            assert s in BROOKS_ENTRY_SIGNAL_REGISTRY, f"{s} missing"

    def test_mtr_not_implemented(self):
        for s in ("major_trend_reversal", "higher_low_mtr", "lower_high_mtr"):
            assert BROOKS_ENTRY_SIGNAL_REGISTRY[s]["maturity"] == "NOT_IMPLEMENTED"

    def test_h2_l2_are_second_entries(self):
        assert BROOKS_ENTRY_SIGNAL_REGISTRY["brooks_h2_strict"]["is_second_entry"]
        assert BROOKS_ENTRY_SIGNAL_REGISTRY["brooks_l2_strict"]["is_second_entry"]

    def test_entry_signals_have_trigger(self):
        for name, d in BROOKS_ENTRY_SIGNAL_REGISTRY.items():
            assert d.get("trigger_rule"), f"{name} missing trigger_rule"

    def test_h1_h2_not_in_entry_registry(self):
        assert "H1" not in BROOKS_ENTRY_SIGNAL_REGISTRY
        assert "H2" not in BROOKS_ENTRY_SIGNAL_REGISTRY
        assert "L1" not in BROOKS_ENTRY_SIGNAL_REGISTRY
        assert "L2" not in BROOKS_ENTRY_SIGNAL_REGISTRY


class TestLegacyProxies:
    def test_legacy_proxy_names(self):
        for s in ("higher_low_proxy_h1", "higher_low_proxy_h2",
                  "lower_high_proxy_l1", "lower_high_proxy_l2"):
            assert s in BROOKS_LEGACY_PROXY_REGISTRY

    def test_legacy_name_mapping(self):
        assert BROOKS_LEGACY_PROXY_REGISTRY["higher_low_proxy_h1"]["legacy_name"] == "H1"
        assert BROOKS_LEGACY_PROXY_REGISTRY["higher_low_proxy_h2"]["legacy_name"] == "H2"
        assert BROOKS_LEGACY_PROXY_REGISTRY["lower_high_proxy_l1"]["legacy_name"] == "L1"
        assert BROOKS_LEGACY_PROXY_REGISTRY["lower_high_proxy_l2"]["legacy_name"] == "L2"

    def test_proxy_not_brooks_standard(self):
        for d in BROOKS_LEGACY_PROXY_REGISTRY.values():
            assert d["is_brooks_standard"] == False
            assert d["is_legacy_proxy"] == True

    def test_proxy_for_strict_signal(self):
        assert BROOKS_LEGACY_PROXY_REGISTRY["higher_low_proxy_h2"]["proxy_for"] == "brooks_h2_strict"
        assert BROOKS_LEGACY_PROXY_REGISTRY["lower_high_proxy_l2"]["proxy_for"] == "brooks_l2_strict"

    def test_proxy_display_label(self):
        assert "代理" in get_proxy_display_label("H2")
        assert "代理" in get_proxy_display_label("higher_low_proxy_h2")


class TestPatterns:
    def test_patterns_not_entry_signals(self):
        for d in BROOKS_PATTERN_REGISTRY.values():
            assert d["produces_entry_signal"] == False

    def test_wedge_in_pattern(self):
        assert "wedge" in BROOKS_PATTERN_REGISTRY

    def test_double_bottom_top_in_pattern(self):
        assert "double_bottom" in BROOKS_PATTERN_REGISTRY
        assert "double_top" in BROOKS_PATTERN_REGISTRY

    def test_final_flag_in_pattern(self):
        assert "final_flag" in BROOKS_PATTERN_REGISTRY


class TestContext:
    def test_context_not_signals(self):
        for d in BROOKS_CONTEXT_REGISTRY.values():
            assert d["produces_entry_signal"] == False

    def test_eighty_twenty_in_context(self):
        assert "eighty_twenty_rule" in BROOKS_CONTEXT_REGISTRY

    def test_tr_fade_in_context(self):
        assert "trading_range_reversal_context" in BROOKS_CONTEXT_REGISTRY


class TestTarget:
    def test_measured_move_in_target(self):
        assert "measured_move" in BROOKS_TARGET_REGISTRY
        assert BROOKS_TARGET_REGISTRY["measured_move"]["produces_entry_signal"] == False


class TestRisk:
    def test_failed_breakout_in_risk(self):
        assert "failed_breakout" in BROOKS_RISK_REGISTRY
        assert BROOKS_RISK_REGISTRY["failed_breakout"]["produces_entry_signal"] == False


class TestAccessors:
    def test_category_entry(self):
        assert get_brooks_category("brooks_h2_strict") == "EntrySignal"
        assert get_brooks_category("climax_reversal") == "EntrySignal"

    def test_category_proxy(self):
        assert get_brooks_category("H2") == "LegacyProxy"
        assert get_brooks_category("higher_low_proxy_h2") == "LegacyProxy"

    def test_category_pattern(self):
        assert get_brooks_category("wedge") == "PatternExpression"
        assert get_brooks_category("final_flag") == "PatternExpression"

    def test_category_context(self):
        assert get_brooks_category("eighty_twenty_rule") == "ContextFactor"

    def test_category_target(self):
        assert get_brooks_category("measured_move") == "TargetTool"

    def test_category_risk(self):
        assert get_brooks_category("failed_breakout") == "RiskWarning"

    def test_is_entry_signal(self):
        assert is_brooks_entry_signal("brooks_h2_strict") == True
        assert is_brooks_entry_signal("H2") == False
        assert is_brooks_entry_signal("wedge") == False

    def test_is_legacy_proxy(self):
        assert is_legacy_proxy_signal("H2") == True
        assert is_legacy_proxy_signal("H1") == True
        assert is_legacy_proxy_signal("brooks_h2_strict") == False

    def test_ontology_record(self):
        r = get_ontology_record("brooks_h2_strict")
        assert r["family"] == "bar_counting"
        r2 = get_ontology_record("H2")
        assert r2["is_legacy_proxy"] == True

    def test_registry_destination(self):
        assert "ENTRY" in get_registry_destination("brooks_h2_strict")
        assert "PROXY" in get_registry_destination("H2")
        assert "PATTERN" in get_registry_destination("wedge")

    def test_list_entry_signals(self):
        signals = list_entry_signals()
        assert "brooks_h2_strict" in signals
        assert "H2" not in signals

    def test_list_legacy_proxies(self):
        proxies = list_legacy_proxies()
        assert len(proxies) == 4


class TestAliases:
    def test_second_entry_alias(self):
        assert "second_entry" in BROOKS_ALIAS_REGISTRY
        aliases = BROOKS_ALIAS_REGISTRY["second_entry"]["aliases"]
        assert "brooks_h2_strict" in aliases
        assert "brooks_l2_strict" in aliases


class TestNoProductionImports:
    def test_no_forbidden_imports(self):
        import brooks_ontology_registry
        lines = open(brooks_ontology_registry.__file__, 'r', encoding='utf-8').readlines()
        in_doc = False
        real = []
        for line in lines:
            s = line.strip()
            if '"""' in s or "'''" in s: in_doc = not in_doc; continue
            if in_doc or s.startswith('#'): continue
            real.append(s)
        code = "\n".join(real)
        for f in ["signal_predictor", "candidate_pool", "rule_guardrail", "sqlite3"]:
            assert f"import {f}" not in code, f"forbidden import: {f}"
        assert "signals.db" not in code
