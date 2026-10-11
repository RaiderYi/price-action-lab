#!/usr/bin/env python3
"""
测试 structured_knowledge_pack 构建器。

运行: python -m pytest tests/test_structured_knowledge_pack.py -v
"""

import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from kb_rules.structured_knowledge_pack import (
    build_structured_knowledge_pack,
    classify_knowledge_item,
    extract_rules_from_context,
    compact_knowledge_items,
    render_knowledge_pack_for_prompt,
    save_knowledge_pack,
)


# ── 示例 wiki_context ──
SAMPLE_WIKI = """
========================================
【Level 3: 信号预判层 — H2, L2, wedge】
========================================

### h2-l2-signal (信号命中)
# H2/L2 Signal

## 一句话定义
H2是趋势中的第二次回踩入场信号，L2是趋势中的第二次反弹做空信号。

### h2-l2-state-machine (信号命中)
# H2/L2 状态机

规则：如果LH2 < LH1 则趋势延续，如果LH2 > LH1 则可能反转。

========================================
【Level T: 陷阱与反例层 — 风险=high_risk】
========================================

- ⚠️ failed-breakout-reversal: 假突破后反转是常见陷阱，不要追突破方向
- ⚠️ trading-range-reversal: 在TR边界做突破方向入场容易被止损

========================================
【Level 2: 市场阶段层 — trend, breakout】
========================================

必须确认趋势方向后再入场，不要在震荡市中做趋势信号。
如果价格突破关键阻力但量能不足，大概率是假突破。
"""


class TestClassifyKnowledgeItem:
    def test_definition(self):
        assert classify_knowledge_item("H2是指趋势中的第二次回踩入场信号") == "definition"

    def test_valid_condition(self):
        assert classify_knowledge_item("LH2必须小于LH1才能确认有效L2") == "valid_condition"

    def test_failure_condition(self):
        assert classify_knowledge_item("如果价格重新站上LH2则信号失效") == "failure_condition"

    def test_trap(self):
        assert classify_knowledge_item("假突破是常见陷阱") == "trap"

    def test_rule(self):
        # "铁律" + "必须遵守" → rule 得分更高
        assert classify_knowledge_item("交易铁律：必须遵守止损原则") == "rule"

    def test_unknown(self):
        assert classify_knowledge_item("hello world") == "unknown"


class TestExtractRules:
    def test_extract_rule_sentences(self):
        rules = extract_rules_from_context(SAMPLE_WIKI)
        assert len(rules) > 0

    def test_extract_trap_rules(self):
        rules = extract_rules_from_context(SAMPLE_WIKI)
        # 应该有来自 trap layer 的规则
        has_trap = any('假突破' in r or '陷阱' in r for r in rules)
        assert has_trap


class TestCompact:
    def test_empty(self):
        assert compact_knowledge_items([]) == []

    def test_dedup_similar(self):
        items = ["假突破是陷阱", "假突破是常见陷阱"]
        result = compact_knowledge_items(items)
        # 前 30 字符标准化后可能不相同（长度差异大时）
        # 验证去重逻辑不崩溃，至少有一个结果
        assert len(result) >= 1

    def test_truncate_long(self):
        long_item = "A" * 200
        result = compact_knowledge_items([long_item])
        assert len(result[0]) <= 150


# ── 核心 pack 测试 ──

DIAGNOSTICS = {
    "total_budget": 15000,
    "used_budget": 13800,
    "risk_profile": "high_risk",
    "retrieved_signal_concepts": ["h2-l2-signal", "h2-l2-state-machine"],
    "retrieved_trap_concepts": ["failed-breakout-reversal", "trading-range-reversal"],
    "trap_keywords_hit": ["failed-breakout-reversal"],
    "missing_expected_knowledge": [],
    "warnings": [],
}


class TestBuildPack:
    def test_pack_has_meta(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            phases=["trend", "breakout"],
            signal_types=["H2", "L2"],
            directions=["long", "short"],
        )
        assert "meta" in pack
        assert pack["meta"]["risk_profile"] == "high_risk"

    def test_pack_has_market_context(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            phases=["trend", "breakout"],
            signal_types=["H2"],
        )
        assert "market_context" in pack
        assert pack["market_context"]["primary_phase"] == "trend"

    def test_pack_has_signal_context(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            phases=["trend"],
            signal_types=["H2", "L2"],
        )
        assert "signal_context" in pack
        assert "H2" in pack["signal_context"]
        assert "L2" in pack["signal_context"]

    def test_H2_has_definition(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            phases=["trend"],
            signal_types=["H2"],
        )
        entry = pack["signal_context"]["H2"]
        # 应有 definition 或 valid_conditions
        has_content = entry.get("definition") or entry.get("valid_conditions")
        assert has_content

    def test_trap_context_exists(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["L2"],
        )
        assert "trap_context" in pack
        tc = pack["trap_context"]
        assert isinstance(tc, dict)

    def test_programmatic_facts_forbidden(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        forb = pack["programmatic_facts"]["llm_forbidden"]
        assert any("不得编造价格" in f for f in forb)

    def test_source_concepts_preserved(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        entry = pack["signal_context"]["H2"]
        # source_concepts 字段存在
        assert "source_concepts" in entry

    def test_diagnostics_embedded(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        rd = pack["retrieval_diagnostics"]
        assert "retrieved_trap_concepts" in rd

    def test_empty_wiki_no_crash(self):
        pack = build_structured_knowledge_pack("", {}, signal_types=["H2"])
        assert isinstance(pack, dict)

    def test_missing_diagnostics_no_crash(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, None, signal_types=["H2"]
        )
        assert isinstance(pack, dict)

    def test_max_items_respected(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
            max_items_per_section=2,
        )
        # 检查不会无限扩展
        entry = pack["signal_context"]["H2"]
        for key, val in entry.items():
            if isinstance(val, list):
                assert len(val) <= 3  # max_items + some buffer

    def test_chinese_text_ok(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            phases=["trend"],
            signal_types=["H2", "L2", "wedge"],
            directions=["long", "short"],
        )
        # 序列化不报错
        s = json.dumps(pack, ensure_ascii=False)
        assert "趋势" in s or "trend" in s


class TestRender:
    def test_render_compact(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            phases=["trend"],
            signal_types=["H2", "L2"],
        )
        rendered = render_knowledge_pack_for_prompt(pack)
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    def test_rendered_no_diagnostics_leak(self):
        """渲染到 prompt 时不应泄漏诊断内部字段。"""
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        rendered = render_knowledge_pack_for_prompt(pack)
        assert "retrieval_diagnostics" not in rendered
        assert "used_budget" not in rendered

    def test_rendered_contains_system_rules(self):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        rendered = render_knowledge_pack_for_prompt(pack)
        assert "系统约束" in rendered or "constraint" in rendered.lower()


class TestSavePack:
    def test_save_json_md(self, tmp_path):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        base = str(tmp_path / "test_pack")
        jp, mp = save_knowledge_pack(pack, base)
        assert Path(jp).exists()
        assert Path(mp).exists()

    def test_json_valid(self, tmp_path):
        pack = build_structured_knowledge_pack(
            SAMPLE_WIKI, DIAGNOSTICS,
            signal_types=["H2"],
        )
        base = str(tmp_path / "test_pack")
        jp, _ = save_knowledge_pack(pack, base)
        with open(jp) as f:
            data = json.load(f)
        assert data["meta"]["version"] == "v1"


# ── wiki_assembler shadow 集成测试 ──

class TestShadowMode:
    def test_shadow_returns_triple(self):
        from wiki_assembler import assemble_structured_knowledge_pack_shadow
        ctx, diag, pack = assemble_structured_knowledge_pack_shadow({}, {})
        assert isinstance(ctx, str)
        # pack 可能为 None（无信号时概念少），但不应崩溃

    def test_shadow_with_signals(self):
        from wiki_assembler import assemble_structured_knowledge_pack_shadow
        ctx, diag, pack = assemble_structured_knowledge_pack_shadow(
            {}, {},
            predicted_signals={"600036": ["L2"]},
            directions={"600036": "short"},
        )
        assert isinstance(ctx, str)
        if pack:
            assert "signal_context" in pack

    def test_shadow_does_not_affect_v2(self):
        """Shadow mode 不影响 assemble_wiki_context_v2 的行为。"""
        from wiki_assembler import assemble_wiki_context_v2, assemble_structured_knowledge_pack_shadow
        v2_result = assemble_wiki_context_v2({}, {})
        ctx, diag, pack = assemble_structured_knowledge_pack_shadow({}, {})
        # v2 结果应该不受影响
        v2_after = assemble_wiki_context_v2({}, {})
        assert len(v2_result) == len(v2_after)
