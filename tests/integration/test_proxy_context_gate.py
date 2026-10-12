"""M12: proxy_context_gate tests"""
import pytest
from proxy_context_gate import (
    gate_proxy_signal, CONTEXT_ALIGNED, CONTEXT_WEAK, CONTEXT_CONFLICT,
    NEEDS_MANUAL_REVIEW, NOT_ENTRY_SIGNAL, KEEP_CURRENT, DOWNGRADE_OBSERVE,
    MANUAL_REVIEW_SHADOW, BLOCK_ACTIONABLE_SHADOW, STRICT_CONFIRMED, RESEARCH_ONLY,
)
from brooks_ontology_registry import is_brooks_entry_signal, is_legacy_proxy_signal


class TestH2ProxyGating:
    def test_h2_bull_pullback_aligned(self):
        r = gate_proxy_signal("H2", "long", {"base_regime": "uptrend", "context_for_signal": ["bull_pullback"]})
        assert r["context_alignment_status"] == CONTEXT_ALIGNED
        assert r["shadow_gate_action"] == KEEP_CURRENT

    def test_h2_range_lower_third_aligned(self):
        r = gate_proxy_signal("H2", "long", {"base_regime": "trading_range", "range_position": "lower_third",
            "context_for_signal": ["range_boundary_reversal"]})
        assert r["context_alignment_status"] == CONTEXT_ALIGNED

    def test_h2_range_middle_weak(self):
        r = gate_proxy_signal("H2", "long", {"base_regime": "trading_range", "range_position": "middle"})
        assert r["context_alignment_status"] in (CONTEXT_WEAK, NEEDS_MANUAL_REVIEW)

    def test_h2_downtrend_conflict(self):
        r = gate_proxy_signal("H2", "long", {"base_regime": "downtrend", "market_direction": "down"})
        assert r["context_alignment_status"] == CONTEXT_CONFLICT
        assert r["shadow_gate_action"] == BLOCK_ACTIONABLE_SHADOW

    def test_h2_transition_manual_review(self):
        r = gate_proxy_signal("H2", "long", {"base_regime": "transition", "manual_review_flag": True})
        assert r["context_alignment_status"] == NEEDS_MANUAL_REVIEW


class TestL2ProxyGating:
    def test_l2_bear_rally_aligned(self):
        r = gate_proxy_signal("L2", "short", {"base_regime": "downtrend", "context_for_signal": ["bear_rally"]})
        assert r["context_alignment_status"] == CONTEXT_ALIGNED

    def test_l2_range_upper_third_aligned(self):
        r = gate_proxy_signal("L2", "short", {"base_regime": "trading_range", "range_position": "upper_third",
            "context_for_signal": ["range_boundary_reversal"]})
        assert r["context_alignment_status"] == CONTEXT_ALIGNED

    def test_l2_uptrend_conflict(self):
        r = gate_proxy_signal("L2", "short", {"base_regime": "uptrend", "market_direction": "up"})
        assert r["context_alignment_status"] == CONTEXT_CONFLICT


class TestOntologyCategorization:
    def test_h2_not_entry_signal(self):
        assert not is_brooks_entry_signal("H2")

    def test_h2_is_legacy_proxy(self):
        assert is_legacy_proxy_signal("H2")

    def test_brooks_h2_is_entry_signal(self):
        assert is_brooks_entry_signal("brooks_h2_strict")

    def test_wedge_not_entry(self):
        r = gate_proxy_signal("wedge", "long")
        assert r["context_alignment_status"] == NOT_ENTRY_SIGNAL
        assert r["shadow_gate_action"] == RESEARCH_ONLY

    def test_measured_move_not_entry(self):
        r = gate_proxy_signal("measured_move", "long")
        assert r["context_alignment_status"] == NOT_ENTRY_SIGNAL


class TestNoProductionImpact:
    def test_no_forbidden_imports(self):
        import proxy_context_gate
        lines = open(proxy_context_gate.__file__, 'r', encoding='utf-8').readlines()
        in_doc = False; real = []
        for line in lines:
            s = line.strip()
            if '"""' in s or "'''" in s: in_doc = not in_doc; continue
            if in_doc or s.startswith('#'): continue
            real.append(s)
        code = "\n".join(real)
        for f in ["candidate_pool", "rule_guardrail", "sqlite3", "signal_predictor"]:
            assert f"import {f}" not in code
        assert "signals.db" not in code
