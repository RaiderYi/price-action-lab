#!/usr/bin/env python3
"""测试 knowledge_card_index。"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from kb_rules.knowledge_card import KnowledgeCard, save_cards_json, load_cards_json
from kb_rules.knowledge_card_index import (
    filter_cards, rank_cards, cards_to_signal_context,
    cards_to_trap_context, cards_to_prompt_block,
    merge_knowledge_cards_into_pack, load_knowledge_cards,
)
from kb_rules.brooks_knowledge_distiller import generate_sample_cards


@pytest.fixture
def sample_cards():
    return generate_sample_cards()


class TestLoad:
    def test_nonexistent_file(self):
        cards = load_knowledge_cards("/nonexistent/path.json")
        assert cards == []


class TestFilter:
    def test_filter_by_signal_type(self, sample_cards):
        h2 = filter_cards(sample_cards, signal_types=["H2"])
        assert len(h2) >= 2

    def test_filter_by_direction(self, sample_cards):
        short_cards = filter_cards(sample_cards, directions=["short"])
        assert len(short_cards) >= 1

    def test_filter_by_phase(self, sample_cards):
        range_cards = filter_cards(sample_cards, phases=["trading_range"])
        assert len(range_cards) >= 1

    def test_filter_by_category(self, sample_cards):
        traps = filter_cards(sample_cards, categories=["trap"])
        for c in traps:
            assert c.category == "trap"

    def test_filter_empty(self, sample_cards):
        result = filter_cards(sample_cards, signal_types=["nonexistent"])
        assert result == []


class TestRank:
    def test_high_risk_favors_trap(self, sample_cards):
        ranked = rank_cards(sample_cards, risk_profile="high_risk", max_items=5)
        # trap/anti_pattern 应该靠前
        first_cats = [c.category for c in ranked[:3]]
        assert any(cat in ("trap", "anti_pattern") for cat in first_cats)

    def test_respects_max_items(self, sample_cards):
        ranked = rank_cards(sample_cards, max_items=3)
        assert len(ranked) <= 3


class TestSignalContext:
    def test_H2_context(self, sample_cards):
        sc = cards_to_signal_context(sample_cards, ["H2"])
        assert "H2" in sc
        assert len(sc["H2"]["definition"]) >= 1 or len(sc["H2"]["source_cards"]) >= 1


class TestTrapContext:
    def test_trap_context_nonempty(self, sample_cards):
        tc = cards_to_trap_context(sample_cards)
        total = sum(len(v) for v in tc.values())
        assert total >= 1


class TestPromptBlock:
    def test_renders(self, sample_cards):
        block = cards_to_prompt_block(sample_cards)
        assert "Knowledge Cards" in block

    def test_empty(self):
        assert cards_to_prompt_block([]) == ""


class TestMergeIntoPack:
    def test_merge_does_not_crash(self, sample_cards):
        pack = {
            "meta": {},
            "signal_context": {},
            "trap_context": {},
        }
        merged = merge_knowledge_cards_into_pack(pack, sample_cards, ["H2", "L2"])
        assert "signal_context" in merged

    def test_merge_trap_context_enhanced(self, sample_cards):
        pack = {"meta": {}, "trap_context": {"short_traps": []}}
        merged = merge_knowledge_cards_into_pack(pack, sample_cards, ["L2"])
        # 应该有 L2 的 trap 内容进入
        assert merged.get("meta", {}).get("knowledge_cards_count", 0) >= 1

    def test_source_cards_traceable(self, sample_cards):
        pack = {"meta": {}, "signal_context": {"L2": {}}}
        merged = merge_knowledge_cards_into_pack(pack, sample_cards, ["L2"])
        l2 = merged["signal_context"].get("L2", {})
        assert "source_cards" in l2 or l2.get("common_traps") or l2.get("definition")


class TestSystemIntegration:
    """集成测试：knowledge_card + index + structured_pack。"""

    def test_full_pipeline(self):
        from kb_rules.structured_knowledge_pack import build_structured_knowledge_pack

        cards = generate_sample_cards()
        pack = build_structured_knowledge_pack(
            wiki_context="sample context",
            diagnostics={"risk_profile": "high_risk"},
            phases=["trend", "breakout"],
            signal_types=["H2", "L2", "wedge"],
            directions=["long", "short"],
        )
        merged = merge_knowledge_cards_into_pack(
            pack, cards, ["H2", "L2", "wedge"]
        )
        assert "signal_context" in merged
        assert merged["meta"].get("knowledge_cards_count", 0) >= 1


class TestSaveLoadRoundtrip:
    def test_save_load_preserves_data(self, tmp_path):
        cards = generate_sample_cards()[:5]
        p = str(tmp_path / "test_cards.json")
        save_cards_json(cards, p)
        loaded = load_cards_json(p)
        assert len(loaded) == 5
        for orig, reloaded in zip(cards, loaded):
            assert orig.id == reloaded.id
            assert orig.category == reloaded.category
            assert orig.rule == reloaded.rule
