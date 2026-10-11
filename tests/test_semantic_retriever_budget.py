#!/usr/bin/env python3
"""
测试 semantic_retriever 动态预算分配 + 诊断模块。

运行: python -m pytest tests/test_semantic_retriever_budget.py -v
"""

import sys
from pathlib import Path

# 确保 strategy_engine/src 在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from kb_rules.retrieval_diagnostics import (
    RetrievalDiagnostics,
    determine_risk_profile,
    compute_dynamic_budget,
    get_trap_concepts,
    TRAP_BUDGET_FLOOR,
)

# ── 风险判定 ──

class TestRiskProfile:
    def test_high_risk_L2(self):
        assert determine_risk_profile(["L2"], []) == "high_risk"

    def test_high_risk_wedge(self):
        assert determine_risk_profile(["wedge"], []) == "high_risk"

    def test_high_risk_tr_fade(self):
        assert determine_risk_profile(["tr_fade"], []) == "high_risk"

    def test_medium_risk_H2(self):
        assert determine_risk_profile(["H2"], []) == "medium_risk"

    def test_low_risk_H1(self):
        assert determine_risk_profile(["H1"], []) == "low_risk"

    def test_short_boosts_risk(self):
        assert determine_risk_profile(["H2"], ["short"]) == "high_risk"

    def test_short_boosts_low_to_medium(self):
        assert determine_risk_profile(["H1"], ["short"]) == "medium_risk"

    def test_multi_signal_highest(self):
        assert determine_risk_profile(["H1", "L2"], []) == "high_risk"


# ── 动态预算 ──

class TestDynamicBudget:
    def test_total_budget_respected(self):
        b = compute_dynamic_budget(["trend"], ["H2"], total_budget=15000)
        total = b["phase"] + b["signal"] + b["trap"] + b["deep"]
        # working_budget = 15000 - 500(scene) = 14500
        assert 14490 <= total <= 14510

    def test_high_risk_gets_more_trap(self):
        b_low = compute_dynamic_budget(["trend"], ["H1"], total_budget=15000)
        b_high = compute_dynamic_budget(["trend"], ["L2"], total_budget=15000)
        assert b_high["trap"] > b_low["trap"]

    def test_short_gets_more_trap(self):
        b_long = compute_dynamic_budget(["trend"], ["H2"], directions=["long"], total_budget=15000)
        b_short = compute_dynamic_budget(["trend"], ["H2"], directions=["short"], total_budget=15000)
        assert b_short["trap"] > b_long["trap"]

    def test_complex_phase_gets_more_phase_budget(self):
        b_simple = compute_dynamic_budget(["trend"], ["H2"], total_budget=15000)
        b_complex = compute_dynamic_budget(["trend", "breakout", "transition"], ["H2"], total_budget=15000)
        assert b_complex["phase"] >= b_simple["phase"]

    def test_multi_signal_balanced(self):
        """多信号混合时预算不过度偏斜。"""
        b = compute_dynamic_budget(["trend", "range"], ["H1", "H2", "L1", "L2", "wedge"], total_budget=15000)
        assert b["signal"] > 1000
        assert b["deep"] > 200

    def test_single_signal_weighted(self):
        """单一信号时信号预算占比更高。"""
        b = compute_dynamic_budget(["trend"], ["H2"], total_budget=15000)
        assert b["signal"] > b["phase"]

    def test_minimum_budgets(self):
        """各层预算不低于最小值。"""
        b = compute_dynamic_budget(["trend"], ["H1"], total_budget=5000)
        assert b["phase"] >= 500
        assert b["signal"] >= 1000
        assert b["trap"] >= 200
        assert b["deep"] >= 200


# ── Trap 概念 ──

class TestTrapConcepts:
    def test_L2_gets_trap_concepts(self):
        traps = get_trap_concepts(["L2"])
        assert len(traps) > 0
        assert "failed-breakout-reversal" in traps

    def test_wedge_gets_trap_concepts(self):
        traps = get_trap_concepts(["wedge"])
        assert len(traps) > 0
        assert "three-push-wedge" in traps or "wedge-gravity-dual-core" in traps

    def test_tr_fade_gets_trap_concepts(self):
        traps = get_trap_concepts(["tr_fade"])
        assert len(traps) > 0
        assert "trading-range-characteristics" in traps

    def test_unknown_signal_empty(self):
        traps = get_trap_concepts(["nonexistent_signal"])
        assert traps == set()


# ── 诊断 ──

class TestDiagnostics:
    def test_to_dict_serializable(self):
        d = RetrievalDiagnostics(
            phases=["trend"], signal_types=["H2"],
            total_budget=15000, risk_profile="medium_risk",
            phase_budget=3000, signal_budget=6000,
            trap_budget=2000, deep_budget=3000, used_budget=14000,
            retrieved_signal_concepts=["h2-l2-signal"],
            retrieved_trap_concepts=["failed-breakout-reversal"],
            warnings=[]
        )
        dd = d.to_dict()
        assert dd["phases"] == ["trend"]
        assert dd["risk_profile"] == "medium_risk"
        assert dd["used_budget"] == 14000

    def test_summary(self):
        d = RetrievalDiagnostics(
            phases=["trend"], signal_types=["L2"],
            total_budget=15000, used_budget=13800,
            risk_profile="high_risk",
            retrieved_signal_concepts=["h2-l2-signal"],
            retrieved_trap_concepts=["failed-breakout-reversal"],
            trap_keywords_hit=["failed-breakout-reversal"],
        )
        s = d.summary()
        assert "high_risk" in s
        assert "trap_hits" in s

    def test_empty_diagnostics_still_valid(self):
        d = RetrievalDiagnostics()
        dd = d.to_dict()
        assert dd["phases"] == []
        assert dd["total_budget"] == 15000


# ── TRAP_BUDGET_FLOOR ──

def test_trap_floor_values():
    assert TRAP_BUDGET_FLOOR["high_risk"] == 0.20
    assert TRAP_BUDGET_FLOOR["medium_risk"] == 0.10
    assert TRAP_BUDGET_FLOOR["low_risk"] == 0.05
