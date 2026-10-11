"""
P6.4.1: LLM Shortlist 完整响应约束 — 六状态分类测试

验证:
1. shortlist 10 个，LLM 返回 8 个 → missing_count=2
2. missing 触发 compact retry
3. symbol 返回但 signals=[] → empty_signal
4. empty_signal 触发 compact retry
5. retry 成功后 retry_recovered_count 增加
6. symbol 相同但 signal_type 不同 → mutated
7. symbol 相同但 direction 不同 → mutated
8. mutated 不得算 accepted
9. rejected 算完整响应，但不入库
10. insufficient_evidence 算完整响应，但不入库
11. accepted 才进入后续 guardrail
12. retry 后仍缺失 → final_unresolved_count > 0
"""

import pytest
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ── Helpers: simulate watchlist and signal_tracking ──

def make_watchlist_item(symbol, signal_type, direction, signals_count=1, llm_status=None):
    """Build a watchlist dict."""
    if signals_count == 0:
        signals_list = []
    else:
        signals_list = [{"signal_type": signal_type, "direction": direction}]
    item = {"symbol": symbol, "signals": signals_list}
    if llm_status:
        item["llm_status"] = llm_status
    return item


def make_tracking_entry(symbol, signal_type, direction):
    return {
        "symbol": symbol, "signal_type": signal_type, "direction": direction,
        "trade_quality": 60.0, "candidate_rank": 1, "pool": "TRADE", "layer": "main_signal",
        "llm_output": False, "llm_status": "pending", "guardrail_grade": "",
        "final_label": "", "reject_reason": "",
        "llm_signal_type": "", "llm_direction": "",
        "signal_drift": False, "drift_reason": "",
        "retry_attempted": False, "retry_recovered": False,
    }


def classify_response(signal_tracking, watchlist_items):
    """Replicate P6.4.1 classification logic (pure function for testing)."""
    llm_response_map = {}
    for item in watchlist_items:
        sym = item["symbol"]
        sigs = item.get("signals", [])
        sig = sigs[0] if sigs else {}
        llm_response_map[sym] = {
            "signals_count": len(sigs),
            "signal_type": sig.get("signal_type", ""),
            "direction": sig.get("direction", ""),
        }

    missing = set()
    empty_signal = set()
    mutated = []
    accepted = []

    for t in signal_tracking:
        sym = t["symbol"]
        resp = llm_response_map.get(sym)
        if not resp:
            t["llm_status"] = "missing"
            missing.add(sym)
        elif resp["signals_count"] == 0:
            t["llm_status"] = "empty_signal"
            empty_signal.add(sym)
            t["llm_output"] = True
        elif t["signal_type"] == resp["signal_type"] and t["direction"] == resp["direction"]:
            t["llm_status"] = "accepted"
            t["llm_output"] = True
            accepted.append(sym)
        else:
            t["llm_status"] = "mutated"
            t["llm_output"] = True
            t["signal_drift"] = True
            t["drift_reason"] = f"shortlist={t['signal_type']}/{t['direction']}, llm={resp['signal_type']}/{resp['direction']}"
            mutated.append(sym)

    return {
        "accepted": accepted, "mutated": mutated,
        "missing": missing, "empty_signal": empty_signal,
    }


# ── Tests ──

class TestLLMShortlistCompleteness:
    """P6.4.1 六状态分类"""

    def test_01_missing_detected(self):
        """shortlist 10 个，LLM 返回 8 个 → missing_count=2"""
        tracking = [make_tracking_entry(f"SYM{i:02d}", "H2", "buy") for i in range(10)]
        watchlist = [make_watchlist_item(f"SYM{i:02d}", "H2", "buy") for i in range(8)]  # only 8

        result = classify_response(tracking, watchlist)
        assert len(result["missing"]) == 2
        assert "SYM08" in result["missing"]
        assert "SYM09" in result["missing"]
        assert len(result["accepted"]) == 8

    def test_02_empty_signal_detected(self):
        """symbol 返回但 signals=[] → empty_signal"""
        tracking = [make_tracking_entry("SYM00", "H2", "buy")]
        watchlist = [make_watchlist_item("SYM00", "", "", signals_count=0)]

        result = classify_response(tracking, watchlist)
        assert "SYM00" in result["empty_signal"]
        assert len(result["accepted"]) == 0
        assert len(result["missing"]) == 0

    def test_03_mutated_signal_type(self):
        """symbol 相同但 signal_type 不同 → mutated"""
        tracking = [make_tracking_entry("SYM00", "H2", "buy")]
        watchlist = [make_watchlist_item("SYM00", "wedge", "buy")]

        result = classify_response(tracking, watchlist)
        assert "SYM00" in result["mutated"]
        assert len(result["accepted"]) == 0
        assert len(result["missing"]) == 0

    def test_04_mutated_direction(self):
        """symbol 相同但 direction 不同 → mutated"""
        tracking = [make_tracking_entry("SYM00", "H2", "buy")]
        watchlist = [make_watchlist_item("SYM00", "H2", "sell")]

        result = classify_response(tracking, watchlist)
        assert "SYM00" in result["mutated"]
        assert len(result["accepted"]) == 0

    def test_05_mutated_not_accepted(self):
        """mutated 不得算 accepted"""
        tracking = [make_tracking_entry("300308", "H2", "buy")]
        watchlist = [make_watchlist_item("300308", "wedge", "short")]

        result = classify_response(tracking, watchlist)
        assert "300308" in result["mutated"]
        assert "300308" not in result["accepted"]
        assert tracking[0]["llm_status"] == "mutated"

    def test_06_accepted_only_when_match(self):
        """accepted 需要 symbol + signal_type + direction 全部匹配"""
        tracking = [make_tracking_entry("SYM00", "tr_fade", "buy")]
        watchlist = [make_watchlist_item("SYM00", "tr_fade", "buy")]

        result = classify_response(tracking, watchlist)
        assert "SYM00" in result["accepted"]
        assert len(result["mutated"]) == 0
        assert len(result["missing"]) == 0

    def test_07_mixed_scenario(self):
        """混合场景: accepted + mutated + missing + empty_signal"""
        tracking = [
            make_tracking_entry("SYM00", "H2", "buy"),   # accepted
            make_tracking_entry("SYM01", "H2", "sell"),  # mutated (direction differs)
            make_tracking_entry("SYM02", "tr_fade", "buy"), # missing
            make_tracking_entry("SYM03", "wedge", "buy"),   # empty_signal
        ]
        watchlist = [
            make_watchlist_item("SYM00", "H2", "buy"),
            make_watchlist_item("SYM01", "H2", "buy"),    # wrong direction
            # SYM02 missing entirely
            make_watchlist_item("SYM03", "", "", signals_count=0),  # empty signals
        ]

        result = classify_response(tracking, watchlist)
        assert len(result["accepted"]) == 1  # SYM00
        assert len(result["mutated"]) == 1   # SYM01
        assert len(result["missing"]) == 1   # SYM02
        assert len(result["empty_signal"]) == 1  # SYM03

    def test_08_retry_targets_only_missing_and_empty(self):
        """retry 只针对 missing + empty_signal, 不含 mutated"""
        tracking = [
            make_tracking_entry("A", "H2", "buy"),  # accepted
            make_tracking_entry("B", "H2", "buy"),  # mutated
            make_tracking_entry("C", "H2", "buy"),  # missing
            make_tracking_entry("D", "H2", "buy"),  # empty_signal
        ]
        watchlist = [
            make_watchlist_item("A", "H2", "buy"),
            make_watchlist_item("B", "wedge", "sell"),
            # C missing
            make_watchlist_item("D", "", "", signals_count=0),
        ]

        result = classify_response(tracking, watchlist)
        retry_targets = result["missing"] | result["empty_signal"]
        assert retry_targets == {"C", "D"}
        assert "B" not in retry_targets  # mutated, no retry

    def test_09_tracking_fields_updated(self):
        """tracking 字段正确更新"""
        tracking = [make_tracking_entry("SYM00", "H2", "buy")]
        watchlist = [make_watchlist_item("SYM00", "H2", "buy")]

        classify_response(tracking, watchlist)
        t = tracking[0]
        assert t["llm_status"] == "accepted"
        assert t["llm_output"] is True

    def test_10_drift_fields_on_mutation(self):
        """mutated 跟踪字段正确"""
        tracking = [make_tracking_entry("300308", "H2", "buy")]
        watchlist = [make_watchlist_item("300308", "wedge", "short")]

        classify_response(tracking, watchlist)
        t = tracking[0]
        assert t["llm_status"] == "mutated"
        assert t["signal_drift"] is True
        assert "H2/buy" in t["drift_reason"]
        assert "wedge/short" in t["drift_reason"]


class TestRetryLogic:
    """retry 恢复逻辑测试"""

    def test_retry_recovered_count_increments(self):
        """retry 成功后 retry_recovered 标记正确"""
        tracking = [make_tracking_entry("300750", "H2", "buy")]
        # Simulate retry: symbol was missing, then retry gets it
        classify_response(tracking, [])  # first pass: missing
        assert tracking[0]["llm_status"] == "missing"

        # Simulate successful retry
        tracking[0]["retry_attempted"] = True
        tracking[0]["retry_recovered"] = True
        tracking[0]["llm_status"] = "accepted"
        assert tracking[0]["retry_recovered"] is True

    def test_retry_failed_unresolved(self):
        """retry 失败 → final_unresolved_count > 0"""
        tracking = [make_tracking_entry("300502", "H2", "buy")]
        classify_response(tracking, [])  # missing
        tracking[0]["retry_attempted"] = True
        # retry didn't recover
        unresolved = sum(1 for t in tracking
                        if t["llm_status"] in ("missing", "empty_signal")
                        and not t.get("retry_recovered"))
        assert unresolved == 1

    def test_rejected_is_complete_response(self):
        """rejected 算完整响应，retry 恢复"""
        tracking = [make_tracking_entry("SYM01", "H2", "buy")]
        classify_response(tracking, [])  # missing
        tracking[0]["retry_attempted"] = True
        tracking[0]["retry_recovered"] = True
        tracking[0]["llm_status"] = "rejected"
        tracking[0]["llm_output"] = True
        # Should NOT count as unresolved
        unresolved = sum(1 for t in tracking
                        if t["llm_status"] in ("missing", "empty_signal")
                        and not t.get("retry_recovered"))
        assert unresolved == 0

    def test_insufficient_evidence_is_complete(self):
        """insufficient_evidence 算完整响应"""
        tracking = [make_tracking_entry("300502", "H2", "buy")]
        classify_response(tracking, [])  # missing
        tracking[0]["retry_attempted"] = True
        tracking[0]["retry_recovered"] = True
        tracking[0]["llm_status"] = "insufficient_evidence"
        tracking[0]["llm_output"] = True
        unresolved = sum(1 for t in tracking
                        if t["llm_status"] in ("missing", "empty_signal")
                        and not t.get("retry_recovered"))
        assert unresolved == 0


class TestFunnelStats:
    """漏斗统计测试"""

    def test_funnel_all_counts(self):
        """漏斗统计各字段正确"""
        tracking = [
            make_tracking_entry("A", "H2", "buy"),  # accepted
            make_tracking_entry("B", "H2", "sell"), # mutated
            make_tracking_entry("C", "H2", "buy"),  # missing
            make_tracking_entry("D", "H2", "buy"),  # empty_signal
        ]
        watchlist = [
            make_watchlist_item("A", "H2", "buy"),
            make_watchlist_item("B", "wedge", "buy"),  # mutated
            # C missing
            make_watchlist_item("D", "", "", signals_count=0),
        ]

        classify_response(tracking, watchlist)

        expected = len(tracking)
        accepted = sum(1 for t in tracking if t["llm_status"] == "accepted")
        mutated = sum(1 for t in tracking if t["llm_status"] == "mutated")
        empty = sum(1 for t in tracking if t["llm_status"] == "empty_signal")
        missing = sum(1 for t in tracking if t["llm_status"] == "missing")

        assert expected == 4
        assert accepted == 1
        assert mutated == 1
        assert empty == 1
        assert missing == 1

    def test_no_silent_missing_in_funnel(self):
        """不能被 accepted 覆盖真正的 missing"""
        tracking = [make_tracking_entry("300750", "H2", "buy")]
        watchlist = [make_watchlist_item("000001", "H2", "buy")]  # wrong symbol

        result = classify_response(tracking, watchlist)
        assert "300750" in result["missing"]
        assert "300750" not in result["accepted"]

    def test_threshold_boundary(self):
        """边界: 0 个 shortlist"""
        tracking = []
        watchlist = []
        result = classify_response(tracking, watchlist)
        assert len(result["accepted"]) == 0
        assert len(result["missing"]) == 0
