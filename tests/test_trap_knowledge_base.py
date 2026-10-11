#!/usr/bin/env python3
"""测试 trap_knowledge_base。"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from kb_rules.brooks_knowledge_distiller import generate_sample_cards
from kb_rules.knowledge_card import save_cards_json, load_cards_json
from kb_rules.trap_knowledge_base import (
    TrapRule, validate_trap_rule, normalize_trap_rule,
    build_trap_rules_from_cards, load_trap_rules,
    filter_traps, rank_traps,
    traps_to_prompt_block, traps_to_pack_context,
    merge_trap_rules_into_pack, write_trap_rules_json,
)


@pytest.fixture
def sample_trap_rules():
    cards = generate_sample_cards()
    rules = build_trap_rules_from_cards(cards)
    return [r for r in rules if validate_trap_rule(r)[0]]


class TestBuild:
    def test_build_from_cards(self, sample_trap_rules):
        assert len(sample_trap_rules) >= 5

    def test_trap_cards_become_trap_rules(self, sample_trap_rules):
        assert any(r.category == "trap" for r in sample_trap_rules)

    def test_anti_pattern_creates_rule(self, sample_trap_rules):
        assert any(r.category == "anti_pattern" for r in sample_trap_rules)

    def test_failure_with_trap_warning(self, sample_trap_rules):
        assert any(r.category == "failure_condition" for r in sample_trap_rules)


class TestValidation:
    def test_valid_rule_passes(self, sample_trap_rules):
        for r in sample_trap_rules:
            ok, errs = validate_trap_rule(r)
            assert ok, f"{r.id}: {errs}"

    def test_missing_id(self):
        r = TrapRule(trap_type="test", warning="w", llm_checklist=["c"],
                      source_cards=["s"])
        ok, _ = validate_trap_rule(r)
        assert not ok

    def test_missing_warning(self):
        r = TrapRule(id="x", trap_type="test", llm_checklist=["c"],
                      source_cards=["s"])
        ok, _ = validate_trap_rule(r)
        assert not ok

    def test_missing_checklist(self):
        r = TrapRule(id="x", trap_type="test", warning="w",
                      source_cards=["s"])
        ok, _ = validate_trap_rule(r)
        assert not ok

    def test_reject_safe_hint_ok(self):
        r = TrapRule(id="x", trap_type="test", warning="w",
                      llm_checklist=["c"], source_cards=["s"],
                      signal_types=["H2"],  # 必须至少有一个适用条件
                      guardrail_hint="不直接 REJECT 信号，仅作风险提示")
        ok, errs = validate_trap_rule(r)
        assert ok, str(errs)

    def test_hard_reject_hint_blocked(self):
        r = TrapRule(id="x", trap_type="test", warning="w",
                      llm_checklist=["c"], source_cards=["s"],
                      signal_types=["H2"],
                      guardrail_hint="直接 REJECT 该信号")
        ok, errs = validate_trap_rule(r)
        assert not ok


class TestLoad:
    def test_nonexistent_file(self):
        rules, skipped = load_trap_rules("/nonexistent/path.json")
        assert rules == []

    def test_roundtrip(self, sample_trap_rules, tmp_path):
        p = str(tmp_path / "traps.json")
        write_trap_rules_json(sample_trap_rules, p)
        loaded, skipped = load_trap_rules(p)
        assert len(loaded) == len(sample_trap_rules)
        assert skipped == []

    def test_malformed_skipped(self, tmp_path):
        p = str(tmp_path / "bad.json")
        Path(p).write_text('{"rules":[{"id":"x","bad":"data"}]}')
        loaded, skipped = load_trap_rules(p)
        assert len(skipped) >= 1


class TestFilter:
    def test_filter_by_signal(self, sample_trap_rules):
        f = filter_traps(sample_trap_rules, signal_types=["L2"])
        assert all("L2" in r.signal_types for r in f)

    def test_filter_by_direction(self, sample_trap_rules):
        f = filter_traps(sample_trap_rules, directions=["short"])
        assert len(f) >= 1

    def test_filter_by_phase(self, sample_trap_rules):
        f = filter_traps(sample_trap_rules, phases=["trading_range"])
        assert len(f) >= 1

    def test_filter_empty(self, sample_trap_rules):
        f = filter_traps(sample_trap_rules, signal_types=["nonexistent"])
        assert f == []


class TestRank:
    def test_high_risk_favors_short(self, sample_trap_rules):
        ranked = rank_traps(sample_trap_rules, risk_profile="high_risk", max_items=3)
        # short traps should be prioritized
        short_count = sum(1 for r in ranked if "short" in r.directions)
        assert short_count >= 1

    def test_respects_max(self, sample_trap_rules):
        ranked = rank_traps(sample_trap_rules, max_items=2)
        assert len(ranked) <= 2


class TestRender:
    def test_prompt_block(self, sample_trap_rules):
        block = traps_to_prompt_block(sample_trap_rules)
        assert "陷阱知识库" in block or "Trap Knowledge Base" in block

    def test_prompt_block_empty(self):
        assert traps_to_prompt_block([]) == ""


class TestPackContext:
    def test_produces_dict(self, sample_trap_rules):
        tc = traps_to_pack_context(sample_trap_rules)
        assert isinstance(tc, dict)
        total = sum(len(v) for v in tc.values())
        assert total >= 1

    def test_source_cards_preserved(self, sample_trap_rules):
        for r in sample_trap_rules:
            assert r.source_cards, f"{r.id} missing source_cards"


class TestMerge:
    def test_merge_enhances_pack(self, sample_trap_rules):
        pack = {"meta": {}, "trap_context": {}}
        merged = merge_trap_rules_into_pack(pack, sample_trap_rules)
        assert merged["meta"].get("trap_rules_count", 0) >= 1

    def test_source_traps_traceable(self, sample_trap_rules):
        pack = {"meta": {}, "trap_context": {}}
        merged = merge_trap_rules_into_pack(pack, sample_trap_rules)
        assert "source_traps" in merged.get("meta", {})

    def test_no_rules_unchanged(self):
        pack = {"meta": {"original": True}, "trap_context": {"x": ["y"]}}
        merged = merge_trap_rules_into_pack(pack, [])
        assert merged["meta"].get("original") is True
        assert merged["trap_context"]["x"] == ["y"]
