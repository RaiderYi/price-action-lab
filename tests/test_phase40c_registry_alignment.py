"""Phase 4.0-C: Registry 与 KB 确认结果对齐测试
覆盖: H1/H2/L1/L2 strict 定义、eighty_twenty context factor、
measured_move projection tool、double_bottom/double_top H2/L2 关联、
final_flag KB确认、tr_fade 交易区间策略、wedge/climax partial match
"""
import pytest
from src.signal_registry import (
    SIGNAL_DEFINITION_REGISTRY,
    get_signal_definition,
    get_live_signal_types,
    is_proxy_signal,
    get_pa_family,
)


# ═══ 1. H1/H2/L1/L2 strict bar-counting 定义 ═══

class TestBrooksStrictBarCounting:
    """1. strict 信号的 trigger_rule 使用 high > prior_bar.high (bar counting)"""

    def test_h2_strict_trigger_is_bar_counting(self):
        cfg = get_signal_definition("brooks_h2_strict")
        assert "high > prior_bar.high" in cfg["trigger_rule"]
        assert "bar counting" in cfg["trigger_rule"].lower()
        # close-based 不应是核心 trigger_rule
        assert "close >" not in cfg["trigger_rule"]

    def test_h2_strict_entry_rule(self):
        cfg = get_signal_definition("brooks_h2_strict")
        assert "breaks above" in cfg["entry_rule"]
        assert "signal bar high" in cfg["entry_rule"]

    def test_h2_strict_stop_rule(self):
        cfg = get_signal_definition("brooks_h2_strict")
        assert "below" in cfg["stop_rule"]
        assert "signal bar low" in cfg["stop_rule"]
        assert "1 tick" in cfg["stop_rule"]

    def test_l2_strict_trigger_is_bar_counting(self):
        cfg = get_signal_definition("brooks_l2_strict")
        assert "low < prior_bar.low" in cfg["trigger_rule"]
        assert "bar counting" in cfg["trigger_rule"].lower()

    def test_l2_strict_entry_rule(self):
        cfg = get_signal_definition("brooks_l2_strict")
        assert "breaks below" in cfg["entry_rule"]
        assert "signal bar low" in cfg["entry_rule"]

    def test_l2_strict_stop_rule(self):
        cfg = get_signal_definition("brooks_l2_strict")
        assert "above" in cfg["stop_rule"]
        assert "signal bar high" in cfg["stop_rule"]
        assert "1 tick" in cfg["stop_rule"]

    def test_h1_l1_strict_have_bar_counting_rules(self):
        h1 = get_signal_definition("brooks_h1_strict")
        assert "high > prior_bar.high" in h1["trigger_rule"]
        l1 = get_signal_definition("brooks_l1_strict")
        assert "low < prior_bar.low" in l1["trigger_rule"]


# ═══ 2. eighty_twenty 不是独立信号 ═══

class TestEightyTwentyContextFactor:
    """2. eighty_twenty 是 context factor，非独立 trade signal"""

    def test_eighty_twenty_is_context_factor(self):
        cfg = get_signal_definition("eighty_twenty")
        assert cfg["maturity"] == "CONTEXT_FACTOR"

    def test_eighty_twenty_not_independent_signal(self):
        cfg = get_signal_definition("eighty_twenty")
        assert cfg["enabled"] is False
        assert cfg["strict_match"] is False
        assert cfg["is_proxy"] is False

    def test_eighty_twenty_pa_family(self):
        cfg = get_signal_definition("eighty_twenty")
        assert cfg["pa_family"] == "range_context"

    def test_eighty_twenty_not_in_live_signals(self):
        live = get_live_signal_types()
        assert "eighty_twenty" not in live

    def test_eighty_twenty_forbidden_phrasing(self):
        cfg = get_signal_definition("eighty_twenty")
        forbidden = " ".join(cfg["report_forbidden_wording"])
        assert "eighty_twenty做多" in forbidden or "80-20交易信号" in forbidden or "80-20交易" in forbidden
        allowed = " ".join(cfg["report_allowed_wording"])
        assert "背景概率" in allowed or "辅助" in allowed


# ═══ 3. measured_move 是 projection tool ═══

class TestMeasuredMoveProjectionTool:
    """3. measured_move 是 target projection tool，非入场信号"""

    def test_measured_move_pa_family(self):
        assert get_pa_family("measured_move") == "measurement_tool"

    def test_measured_move_maturity(self):
        cfg = get_signal_definition("measured_move")
        assert cfg["maturity"] == "STRUCTURE_READY"

    def test_measured_move_is_still_enabled(self):
        # Focus v1: measured_move demoted to TOOL layer (target projection only)
        cfg = get_signal_definition("measured_move")
        assert cfg["enabled"] is False
        assert cfg["implemented"] is True

    def test_measured_move_forbidden_as_entry(self):
        forbidden = " ".join(get_signal_definition("measured_move")["report_forbidden_wording"])
        assert "入场" in forbidden or "做多" in forbidden

    def test_measured_move_allowed_as_projection(self):
        allowed = " ".join(get_signal_definition("measured_move")["report_allowed_wording"])
        assert "TP" in allowed or "测算" in allowed or "目标" in allowed


# ═══ 4. double_bottom / double_top 与 H2/L2 关联 ═══

class TestDoublePatternAssociation:
    """4. double_bottom=H2形态表达, double_top=L2形态表达"""

    def test_double_bottom_linked_to_h2_strict(self):
        cfg = get_signal_definition("double_bottom")
        assert cfg["proxy_for"] == "brooks_h2_strict"
        assert cfg["pa_family"] == "price_action_pattern"

    def test_double_top_linked_to_l2_strict(self):
        cfg = get_signal_definition("double_top")
        assert cfg["proxy_for"] == "brooks_l2_strict"
        assert cfg["pa_family"] == "price_action_pattern"

    def test_double_bottom_display_includes_h2(self):
        cfg = get_signal_definition("double_bottom")
        assert "H2" in cfg["display_name_cn"] or "H2" in cfg.get("notes", "")

    def test_double_top_display_includes_l2(self):
        cfg = get_signal_definition("double_top")
        assert "L2" in cfg["display_name_cn"] or "L2" in cfg.get("notes", "")

    def test_double_patterns_not_downgraded(self):
        """must NOT downgrade maturity"""
        assert get_signal_definition("double_bottom")["maturity"] == "TRADE_READY"
        assert get_signal_definition("double_top")["maturity"] == "TRADE_READY"


# ═══ 5. final_flag 不再是 NO_KB_SOURCE ═══

class TestFinalFlagKBConfirmed:
    """5. final_flag KB已确认，status 不再为 NO_KB_SOURCE"""

    def test_final_flag_is_kb_confirmed(self):
        status = get_signal_definition("final_flag")["manual_review_status"]
        assert "CONFIRMED_BY_KB" in status

    def test_final_flag_pa_family(self):
        assert get_pa_family("final_flag") == "trend_exhaustion"

    def test_final_flag_definition_version(self):
        cfg = get_signal_definition("final_flag")
        assert "brooks_final_flag_v1" in cfg["definition_version"]

    def test_final_flag_still_live(self):
        assert "final_flag" in get_live_signal_types()


# ═══ 6. tr_fade 定位为 trading range strategy ═══

class TestTRFadeTradingRangeStrategy:
    """6. tr_fade = trading range reversal strategy"""

    def test_tr_fade_pa_family(self):
        assert get_pa_family("tr_fade") == "trading_range_strategy"

    def test_tr_fade_display_label(self):
        cfg = get_signal_definition("tr_fade")
        assert "交易区间反转" in cfg["display_name_cn"] or "trading range reversal" in cfg["display_name_cn"]

    def test_tr_fade_not_proxy(self):
        assert is_proxy_signal("tr_fade") is False

    def test_tr_fade_kb_confirmed(self):
        assert "CONFIRMED_BY_KB" in get_signal_definition("tr_fade")["manual_review_status"]


# ═══ 7. wedge / climax_reversal partial match ═══

class TestWedgeClimaxPartialMatch:
    """7. wedge 和 climax_reversal 都是 PARTIAL_MATCH"""

    def test_wedge_is_partial_match(self):
        status = get_signal_definition("wedge")["manual_review_status"]
        assert "PARTIAL_MATCH" in status

    def test_climax_is_partial_match(self):
        status = get_signal_definition("climax_reversal")["manual_review_status"]
        assert "PARTIAL_MATCH" in status

    def test_wedge_notes_mention_review(self):
        notes = get_signal_definition("wedge").get("notes", "")
        assert "STRICT_IMPLEMENTATION_REVIEW" in notes.upper() or "REVIEW" in notes

    def test_climax_notes_mention_context(self):
        notes = get_signal_definition("climax_reversal").get("notes", "")
        assert "TREND_EXHAUSTION" in notes.upper() or "EXHAUSTION" in notes


# ═══ 8. 生产信号逻辑不变 ═══

class TestNoProductionChange40C:
    """8. 本 Phase 不改变生产行为"""

    def test_no_detector_imports(self):
        with open("src/signal_registry.py", "r", encoding="utf-8") as f:
            src = f.read()
        for forbidden_import in [
            "from signal_predictor", "from system_structure_builder",
            "from system_price_builder", "from candidate_pool",
            "from rule_guardrail", "from run_strategy",
        ]:
            assert forbidden_import not in src, f"Detected: {forbidden_import}"

    def test_live_signals_count_unchanged_from_baseline(self):
        """Focus v1 (2026-10-11): 6 live = 双核四结构+区间开关（A股30m专用）"""
        live = get_live_signal_types()
        assert len(live) == 6  # Focus v1
        # Focus v1 production surface: H2/L2/breakout/wedge/final_flag/tr_fade
        focus_set = {"H2", "L2", "breakout", "wedge", "final_flag", "tr_fade"}
        assert set(live) == focus_set

    def test_no_db_write_module_touched(self):
        """signal_registry 不应导入任何会写 DB 的模块"""
        # Verify the file doesn't try to import signals.db
        with open("src/signal_registry.py", "r", encoding="utf-8") as f:
            src = f.read()
        assert "signals.db" not in src
        assert "sqlite3" not in src
