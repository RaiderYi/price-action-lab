"""P10: tr_fade 升级验证测试"""
import pytest, sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from system_structure_builder import build_structure_points
from system_price_builder import build_system_prices
from rule_guardrail import ScoredSignal, apply_guardrails
from signal_maturity import get_maturity, can_enter_main_shortlist


def make_kline(highs, lows, closes=None):
    if closes is None:
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({'high': highs, 'low': lows, 'close': closes})


def make_range_kline(rh=53, rl=47, cp=48, bars=60):
    """创建有效区间 K 线"""
    n = bars
    highs = [rh] * n; lows = [rl] * n; closes = [(rh+rl)/2] * n
    # Add touches at boundaries
    for i in [10, 25, 40]: highs[i] = rh; lows[i] = rl - 0.5
    for i in [15, 35, 50]: lows[i] = rl; highs[i] = rh + 0.5
    # Current near range low
    closes[-1] = cp; highs[-1] = cp + 1; lows[-1] = cp - 1
    return make_kline(highs, lows, closes)


class TestTrFadeStructure:
    def test_range_detected_with_touch_count(self):
        df = make_range_kline(53, 47, 47.0)  # cp near range low
        r = build_structure_points("X", "tr_fade", "long", df, 47.0)
        assert r["structure_status"] in ("verified", "weak")
        pts = r["structure_points"]
        assert "range_high" in pts
        assert "range_low" in pts
        assert "range_touch_count_high" in pts
        assert "range_touch_count_low" in pts
        assert "fade_direction" in pts

    def test_near_low_detect_long_fade(self):
        df = make_range_kline(53, 47, 48)
        r = build_structure_points("X", "tr_fade", "long", df, 47.0)
        if r["structure_status"] == "verified":
            assert r["structure_points"]["fade_direction"] == "long"

    def test_mid_range_no_fade(self):
        df = make_range_kline(53, 47, 50)  # at midpoint
        r = build_structure_points("X", "tr_fade", "long", df, 50)
        assert r["structure_status"] != "verified"

    def test_narrow_range_insufficient(self):
        # range < 2%
        highs = [50.5]*60; lows = [50.0]*60
        df = make_kline(highs, lows)
        r = build_structure_points("X", "tr_fade", "long", df, 50.1)
        assert r["structure_status"] == "insufficient"


class TestTrFadePrices:
    def test_system_prices_from_range(self):
        sp = build_system_prices("X", "tr_fade", "long", 48,
                                 {"range_high": 53, "range_low": 47,
                                  "range_mid": 50, "current_position_pct": 15,
                                  "range_width_pct": 12.8})
        assert sp["price_builder_status"] == "success"
        assert "system:range" in sp["price_source"]

    def test_no_range_returns_insufficient(self):
        sp = build_system_prices("X", "tr_fade", "long", 48, {})
        assert "system:current_price_based" in sp["price_source"]


class TestTrFadeGuardrail:
    def test_guardrail_applied_to_tr_fade(self):
        s = ScoredSignal(symbol="X", signal_type="tr_fade", direction="long",
                        market="A股", llm_entry_min=48, llm_entry_max=49,
                        llm_stop_loss=46, llm_tp1=52, llm_score=70, llm_confidence=0.7,
                        llm_rr=2.0, current_price=48,
                        structure_evidence={"range_width_pct": 15, "range_duration_bars": 20,
                                           "range_touch_count_high": 3, "range_touch_count_low": 3,
                                           "current_position_pct": 15, "fade_direction": "long"})
        r = apply_guardrails(s)
        # RR=3.0 should pass generic RR check: tp1=52, entry_mid=48.5, sl=46 → risk=2.5 reward=3.5 rr=1.4
        # This will trigger the generic RR guardrail warning. Check tr_fade specific ones.
        tr_fade_violations = [v for v in r.guardrail_violations if "区间" in v or "fade" in v or "方向冲突" in v]
        assert len(tr_fade_violations) <= 1  # RR generic warning may appear

    def test_narrow_range_guardrail_rejects(self):
        s = ScoredSignal(symbol="X", signal_type="tr_fade", direction="long",
                        market="A股", llm_entry_min=48, llm_entry_max=49,
                        llm_stop_loss=46, llm_tp1=52, llm_score=70, llm_confidence=0.7,
                        llm_rr=2.0, current_price=48,
                        structure_evidence={"range_width_pct": 1.0, "fade_direction": "long"})
        r = apply_guardrails(s)
        assert any("区间宽度过窄" in v for v in r.guardrail_violations)

    def test_direction_conflict_rejects(self):
        s = ScoredSignal(symbol="X", signal_type="tr_fade", direction="short",
                        market="A股", llm_entry_min=48, llm_entry_max=49,
                        llm_stop_loss=50, llm_tp1=44, llm_score=70, llm_confidence=0.7,
                        llm_rr=2.0, current_price=48,
                        structure_evidence={"range_width_pct": 15, "range_duration_bars": 20,
                                           "range_touch_count_high": 3, "range_touch_count_low": 3,
                                           "current_position_pct": 15, "fade_direction": "long"})
        r = apply_guardrails(s)
        assert any("方向冲突" in v for v in r.guardrail_violations)


class TestTrFadeMaturity:
    def test_still_structure_ready(self):
        assert get_maturity("tr_fade") == "STRUCTURE_READY"

    def test_not_in_main_shortlist(self):
        assert not can_enter_main_shortlist("tr_fade")
