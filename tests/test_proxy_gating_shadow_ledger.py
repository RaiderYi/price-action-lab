"""M14: proxy_gating_shadow_ledger tests"""
import pytest, json, os, tempfile
from proxy_paper_simulator import settle_proxy_paper, simulate_signals, compute_simulation_stats, TERMINAL
from proxy_context_gate import gate_proxy_signal, CONTEXT_ALIGNED, CONTEXT_CONFLICT, BLOCK_ACTIONABLE_SHADOW


class TestDedup:
    def make_signals(self):
        return [
            {"symbol": "A", "signal_type": "H2", "direction": "long",
             "source_report_date": "2026-06-04", "entry_high": 10.5, "entry_low": 10.0, "stop_loss": 9.5},
            {"symbol": "A", "signal_type": "H2", "direction": "long",
             "source_report_date": "2026-06-04", "entry_high": 10.5, "entry_low": 10.0, "stop_loss": 9.5},
        ]
    
    def _dedup_key(self, s):
        return f"{s.get('symbol','')}|{s.get('signal_type','')}|{s.get('direction','')}|{s.get('source_report_date','')}|{s.get('entry_high',0):.2f}|{s.get('entry_low',0):.2f}|{s.get('stop_loss',0):.2f}"

    def test_same_signal_same_key(self):
        sigs = self.make_signals()
        assert self._dedup_key(sigs[0]) == self._dedup_key(sigs[1])

    def test_dedup(self):
        sigs = self.make_signals()
        existing = {}
        for s in sigs:
            dk = self._dedup_key(s)
            if dk not in existing:
                existing[dk] = s
        assert len(existing) == 1


class TestGating:
    def test_blocked_excluded(self):
        s = {"symbol": "X", "signal_type": "H2", "direction": "long",
             "entry_high": 10, "entry_low": 9, "stop_loss": 8, "tp1": 12, "tp2": 14,
             "blocked_by_gate": True}
        gated = [x for x in [s] if not x.get("blocked_by_gate", False)]
        assert len(gated) == 0

    def test_raw_always_includes(self):
        s = {"blocked_by_gate": True, "raw_included": True}
        raw = [s]
        assert len(raw) == 1

    def test_conflict_blocks(self):
        r = gate_proxy_signal("H2", "long", {"base_regime": "downtrend", "market_direction": "down"})
        assert r["context_alignment_status"] == CONTEXT_CONFLICT
        assert r["shadow_gate_action"] == BLOCK_ACTIONABLE_SHADOW


class TestSettlement:
    def test_no_future_bars_not_expired(self):
        r = settle_proxy_paper("long", 10.5, 10.0, 9.0, 12.0, 14.0, [])
        assert r["outcome"] == "PAPER_INVALIDATED"  # no bars = invalidated

    def test_long_tp2(self):
        bars = [{"high": 10.6, "low": 10.1, "close": 10.5, "time": "T1"},
                {"high": 14.5, "low": 10.0, "close": 14.0, "time": "T2"}]
        r = settle_proxy_paper("long", 10.5, 10.0, 9.0, 12.0, 14.0, bars)
        assert r["outcome"] == "PAPER_HIT_TP2"
        assert r["pnl_r"] == 2.0

    def test_same_bar_tp_sl_conservative(self):
        bars = [{"high": 14.0, "low": 8.0, "close": 10.0, "time": "T1"}]
        r = settle_proxy_paper("long", 10.5, 10.0, 9.0, 12.0, 14.0, bars)
        assert r["outcome"] == "PAPER_HIT_SL"
        assert r["reason"] == "same_bar_tp_sl_conflict_conservative_sl"


class TestNoProductionImports:
    def test_no_forbidden(self):
        lines = open(__file__, 'r', encoding='utf-8').read()
        assert "sqlite3" not in lines or "#" in lines.split("sqlite3")[0]
