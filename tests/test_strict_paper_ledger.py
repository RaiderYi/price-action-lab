"""Phase 5.2: Paper ledger and multi-day tracking tests"""
import pytest
import json, os, tempfile
from strict_paper_tracker import (
    PaperSignal, build_dedup_key, merge_into_ledger, compute_ledger_stats,
    save_paper_signals, load_paper_signals, ledger_to_csv_rows,
    PAPER_PENDING, PAPER_ACTIVE, PAPER_HIT_TP1, PAPER_HIT_TP2,
    PAPER_HIT_SL, PAPER_EXPIRED, TERMINAL_STATUSES,
)


def make_ps(pid, symbol, sig_type, direction, bar_time, status=PAPER_PENDING, pnl=None):
    ps = PaperSignal()
    ps.paper_id = pid
    ps.symbol = symbol
    ps.signal_type = sig_type
    ps.direction = direction
    ps.signal_bar_time = bar_time
    ps.signal_bar_high = 10.5
    ps.signal_bar_low = 10.0
    ps.ideal_entry = 10.51 if direction == "long" else 9.99
    ps.stop_loss = 9.99 if direction == "long" else 10.51
    ps.tp1 = 11.03 if direction == "long" else 9.47
    ps.tp2 = 11.55 if direction == "long" else 8.95
    ps.risk_abs = 0.52
    ps.paper_status = status
    ps.pnl_r = pnl
    ps.execution_type = "paper_trade" if direction == "long" else "hedge_reference"
    ps.not_real_short_trade = (direction == "short")
    return ps


class TestDedup:
    def test_same_signal_same_key(self):
        """Same symbol+sig_type+direction+time+high+low → same key"""
        a = make_ps("A", "000400", "brooks_h2_strict", "long", "2026-06-03T10:00")
        b = make_ps("B", "000400", "brooks_h2_strict", "long", "2026-06-03T10:00")
        assert build_dedup_key(a) == build_dedup_key(b)

    def test_different_time_different_key(self):
        a = make_ps("A", "000400", "brooks_h2_strict", "long", "2026-06-03T10:00")
        b = make_ps("B", "000400", "brooks_h2_strict", "long", "2026-06-03T11:00")
        assert build_dedup_key(a) != build_dedup_key(b)


class TestMergeLedger:
    def test_new_signal_added(self):
        """T2: new signal added to empty ledger"""
        new = [make_ps("A", "TEST", "h2", "long", "T10:00")]
        merged, added, updated = merge_into_ledger([], new)
        assert added == 1
        assert updated == 0
        assert len(merged) == 1

    def test_duplicate_not_added(self):
        """T1/T2: same signal not duplicated"""
        old = [make_ps("A", "TEST", "h2", "long", "T10:00", PAPER_PENDING)]
        new = [make_ps("B", "TEST", "h2", "long", "T10:00", PAPER_PENDING)]
        merged, added, updated = merge_into_ledger(old, new)
        assert added == 0
        assert len(merged) == 1

    def test_status_updated_when_advanced(self):
        """T3: pending→active status update"""
        old = [make_ps("A", "TEST", "h2", "long", "T10:00", PAPER_PENDING)]
        new = [make_ps("B", "TEST", "h2", "long", "T10:00", PAPER_ACTIVE)]
        merged, added, updated = merge_into_ledger(old, new)
        assert updated == 1
        assert merged[0].paper_status == PAPER_ACTIVE


class TestLedgerStats:
    def make_terminal_signals(self):
        return [
            make_ps("1", "A", "h2", "long", "T1", PAPER_HIT_TP1, 1.0),
            make_ps("2", "A", "l2", "short", "T2", PAPER_HIT_SL, -1.0),
            make_ps("3", "B", "h2", "long", "T3", PAPER_HIT_TP2, 2.0),
            make_ps("4", "B", "l2", "short", "T4", PAPER_HIT_TP1, 1.0),
            make_ps("5", "C", "h1", "long", "T5", PAPER_EXPIRED, 0.0),
        ]

    def test_long_short_separate(self):
        """T5: long executable vs short hedge separated"""
        sigs = self.make_terminal_signals()
        stats = compute_ledger_stats(sigs)
        assert stats["long_executable"]["count"] == 3
        assert stats["short_hedge_reference"]["count"] == 2

    def test_avg_r_computed(self):
        """T6: avg_pnl_r correct"""
        sigs = self.make_terminal_signals()
        stats = compute_ledger_stats(sigs)
        assert stats["all_terminal"]["avg_r"] == 0.6  # (1 + -1 + 2 + 1 + 0)/5

    def test_wr_correct(self):
        sigs = self.make_terminal_signals()
        stats = compute_ledger_stats(sigs)
        assert stats["all_terminal"]["wr"] == 60.0  # 3 wins / 5

    def test_open_closed_counts(self):
        """T8: open/closed distribution"""
        sigs = self.make_terminal_signals() + [make_ps("6", "D", "h2", "long", "T6", PAPER_PENDING)]
        stats = compute_ledger_stats(sigs)
        assert stats["closed"] == 5
        assert stats["open"] == 1


class TestNoProductionImports:
    def test_ledger_no_forbidden(self):
        import strict_paper_tracker
        lines = open(strict_paper_tracker.__file__, 'r', encoding='utf-8').readlines()
        in_doc = False
        real = []
        for line in lines:
            s = line.strip()
            if s.startswith('"""') or s.startswith("'''"):
                in_doc = not in_doc; continue
            if in_doc or s.startswith('#'): continue
            real.append(s)
        code = "\n".join(real)
        for f in ["run_strategy", "candidate_pool", "rule_guardrail"]:
            assert f"import {f}" not in code
        assert "sqlite3" not in code


class TestCSVExport:
    def test_csv_rows_generated(self):
        sigs = [make_ps("1", "A", "h2", "long", "T1", PAPER_HIT_TP1, 1.0)]
        rows = ledger_to_csv_rows(sigs)
        assert len(rows) == 1
        assert rows[0]["paper_id"] == "1"
        assert rows[0]["pnl_r"] == 1.0
        assert rows[0]["is_closed"] == True


class TestSaveLoadRoundtrip:
    def test_save_load_ledger(self):
        sigs = [make_ps("A", "TEST", "h2", "long", "T10:00", PAPER_HIT_TP1, 1.0)]
        tmp = os.path.join(tempfile.gettempdir(), "test_ledger.json")
        save_paper_signals(sigs, tmp)
        loaded = load_paper_signals(tmp)
        assert len(loaded) == 1
        assert loaded[0].paper_id == "A"
        assert loaded[0].pnl_r == 1.0
        os.unlink(tmp)
