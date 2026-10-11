#!/usr/bin/env python3
"""测试 brooks_knowledge_distiller。"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from kb_rules.brooks_knowledge_distiller import (
    split_into_segments,
    classify_segment,
    detect_signal_types,
    detect_directions,
    detect_phases,
    extract_candidate_cards,
    deduplicate_cards,
    generate_sample_cards,
)
from kb_rules.knowledge_card import (
    KnowledgeCard, validate_card, normalize_card, save_cards_json, load_cards_json,
)


class TestSplitSegments:
    def test_empty(self):
        assert split_into_segments("") == []

    def test_single_section(self):
        text = "## 定义\nH2是趋势中的第二次回踩入场信号。" + "额外内容" * 10
        segs = split_into_segments(text)
        assert len(segs) >= 1

    def test_small_text_filtered(self):
        segs = split_into_segments("hi", min_chars=50)
        assert segs == []


class TestClassify:
    def test_definition_heading(self):
        assert classify_segment("## 定义", "H2是指...") == "definition"

    def test_trap_content(self):
        assert classify_segment("## 注意事项", "常见陷阱是假突破") == "trap"

    def test_valid_condition(self):
        assert classify_segment("## 有效条件", "必须满足趋势方向") == "valid_condition"

    def test_fallback(self):
        assert classify_segment("## 其他", "一些内容") == "market_context"


class TestDetectSignalTypes:
    def test_H2(self):
        assert "H2" in detect_signal_types("H2 做多信号在趋势中有效")

    def test_L2_short(self):
        types = detect_signal_types("L2 做空需要确认LH2 < LH1")
        assert "L2" in types

    def test_wedge(self):
        assert "wedge" in detect_signal_types("楔形末端反转是高级信号")

    def test_no_match(self):
        assert detect_signal_types("价格波动在正常范围") == []


class TestDetectDirections:
    def test_long(self):
        assert "long" in detect_directions("做多入场需要确认支撑")

    def test_short(self):
        assert "short" in detect_directions("做空信号在顶部出现")

    def test_default(self):
        assert detect_directions("价格在波动") == ["both"]


class TestDetectPhases:
    def test_trend(self):
        assert "trend" in detect_phases("趋势延续时入场")

    def test_breakout(self):
        assert "breakout" in detect_phases("突破后回踩确认")

    def test_failed_breakout(self):
        assert "failed_breakout" in detect_phases("假突破是陷阱")


# ── 卡片验证 ──

class TestCardValidation:
    def test_valid_card(self):
        card = KnowledgeCard(
            id="test_001", category="definition",
            signal_types=["H2"], rule="test rule",
            source={"type": "test", "file": "test.md"},
        )
        ok, errs = validate_card(card)
        assert ok, str(errs)

    def test_missing_id(self):
        card = KnowledgeCard(category="definition", rule="x", source={"type": "t"})
        ok, errs = validate_card(card)
        assert not ok

    def test_missing_category(self):
        card = KnowledgeCard(id="x", rule="x", source={"type": "t"})
        ok, _ = validate_card(card)
        assert not ok

    def test_missing_source(self):
        card = KnowledgeCard(id="x", category="definition", rule="x")
        ok, _ = validate_card(card)
        assert not ok

    def test_missing_rule_and_definition(self):
        card = KnowledgeCard(id="x", category="definition", source={"type": "t"})
        ok, _ = validate_card(card)
        assert not ok

    def test_trap_missing_warning(self):
        card = KnowledgeCard(
            id="x", category="trap", rule="小心", source={"type": "t"},
        )
        ok, errs = validate_card(card)
        assert not ok
        assert any("trap_warning" in e for e in errs)

    def test_normalize_sorts_tags(self):
        card = KnowledgeCard(
            id="x", category="definition", rule="x",
            source={"type": "t"},
            tags=["b", "a", "c"],
        )
        card = normalize_card(card)
        assert card.tags == ["a", "b", "c"]


# ── 样例卡片 ──

class TestSampleCards:
    def test_at_least_12(self):
        cards = generate_sample_cards()
        assert len(cards) >= 12

    def test_all_valid(self):
        cards = generate_sample_cards()
        for card in cards:
            ok, errs = validate_card(card)
            assert ok, f"{card.id}: {errs}"

    def test_trap_cards_have_warning(self):
        cards = generate_sample_cards()
        for card in cards:
            if card.category == "trap":
                assert card.trap_warning, f"{card.id} missing trap_warning"

    def test_all_have_source(self):
        cards = generate_sample_cards()
        for card in cards:
            assert card.source, f"{card.id} missing source"

    def test_has_H2_definition(self):
        cards = generate_sample_cards()
        h2_defs = [c for c in cards if "H2" in c.signal_types and c.category == "definition"]
        assert len(h2_defs) >= 1

    def test_has_L2_trap(self):
        cards = generate_sample_cards()
        l2_traps = [c for c in cards if "L2" in c.signal_types and c.category == "trap"]
        assert len(l2_traps) >= 1

    def test_has_wedge(self):
        cards = generate_sample_cards()
        wedges = [c for c in cards if "wedge" in c.signal_types]
        assert len(wedges) >= 1

    def test_has_tr_fade(self):
        cards = generate_sample_cards()
        tr_cards = [c for c in cards if "tr_fade" in c.signal_types]
        assert len(tr_cards) >= 1


# ── 去重 ──

class TestDedup:
    def test_identical_removed(self):
        c1 = KnowledgeCard(id="a", category="trap", signal_types=["L2"], rule="same",
                            source={"t": "x"}, trap_warning="w")
        c2 = KnowledgeCard(id="b", category="trap", signal_types=["L2"], rule="same",
                            source={"t": "x"}, trap_warning="w")
        result = deduplicate_cards([c1, c2])
        assert len(result) == 1

    def test_different_rule_kept(self):
        c1 = KnowledgeCard(id="a", category="trap", signal_types=["L2"], rule="a",
                            source={"t": "x"}, trap_warning="w")
        c2 = KnowledgeCard(id="b", category="trap", signal_types=["L2"], rule="b",
                            source={"t": "x"}, trap_warning="w")
        result = deduplicate_cards([c1, c2])
        assert len(result) == 2


# ── JSON 保存/加载 ──

class TestSaveLoad:
    def test_roundtrip(self, tmp_path):
        cards = [KnowledgeCard(
            id="rt_001", category="definition", signal_types=["H2"],
            rule="test", source={"type": "test", "file": "x.md"},
            tags=["H2", "trend"],
        )]
        p = str(tmp_path / "cards.json")
        save_cards_json(cards, p)
        assert Path(p).exists()
        loaded = load_cards_json(p)
        assert len(loaded) == 1
        assert loaded[0].id == "rt_001"

    def test_chinese_preserved(self, tmp_path):
        cards = [KnowledgeCard(
            id="cn_001", category="trap", signal_types=["L2"],
            directions=["short"],
            rule="不要追空", trap_warning="区间下沿陷阱",
            source={"type": "test", "file": "x.md"},
        )]
        p = str(tmp_path / "cards_cn.json")
        save_cards_json(cards, p)
        with open(p, encoding='utf-8') as f:
            data = json.load(f)
        assert "不要追空" in json.dumps(data, ensure_ascii=False)
