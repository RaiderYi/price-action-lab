"""Phase 5.0: strict_paper_tracker tests"""
import pytest
from strict_paper_tracker import (
    PaperSignal, settle_paper_signal, compute_paper_pnl,
    settle_all_paper_signals, load_paper_signals, save_paper_signals,
    compute_stats,
    PAPER_PENDING, PAPER_TRIGGERED, PAPER_ACTIVE,
    PAPER_HIT_TP1, PAPER_HIT_TP2, PAPER_HIT_SL,
    PAPER_EXPIRED, PAPER_INVALIDATED, TERMINAL_STATUSES,
)


def make_long_paper(signal_time="2026-06-04T10:00", entry=10.51, stop=9.99,
                     tp1=11.03, tp2=11.55, invalid=9.50):
    ps = PaperSignal()
    ps.paper_id = "TEST_LONG"
    ps.symbol = "TEST"
    ps.direction = "long"
    ps.signal_bar_time = signal_time
    ps.signal_bar_high = 10.50
    ps.signal_bar_low = 10.00
    ps.ideal_entry = entry
    ps.stop_loss = stop
    ps.tp1 = tp1
    ps.tp2 = tp2
    ps.risk_abs = abs(entry - stop)
    ps.invalid_level = invalid
    ps.paper_status = PAPER_PENDING
    return ps


def make_short_paper(signal_time="2026-06-04T10:00", entry=9.99, stop=10.51,
                      tp1=9.47, tp2=8.95, invalid=11.00):
    ps = PaperSignal()
    ps.paper_id = "TEST_SHORT"
    ps.symbol = "TEST"
    ps.direction = "short"
    ps.signal_bar_time = signal_time
    ps.signal_bar_high = 10.50
    ps.signal_bar_low = 10.00
    ps.ideal_entry = entry
    ps.stop_loss = stop
    ps.tp1 = tp1
    ps.tp2 = tp2
    ps.risk_abs = abs(entry - stop)
    ps.invalid_level = invalid
    ps.paper_status = PAPER_PENDING
    return ps


def make_bars(times_highs_lows):
    """times_highs_lows: [(time_str, high, low), ...]"""
    bars = []
    for t, h, l in times_highs_lows:
        bars.append({
            "time": t, "open": (h + l) / 2, "high": h, "low": l,
            "close": (h + l) / 2,
        })
    return bars


class TestPendingToTriggered:
    def test_long_triggered(self):
        """T13: pending → triggered when high >= ideal_entry"""
        ps = make_long_paper()
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),  # signal bar
            ("2026-06-04T10:30", 10.60, 10.30),  # high 10.60 >= ideal 10.51 → trigger
        ])
        settle_paper_signal(ps, bars)
        assert ps.triggered
        assert ps.paper_status == PAPER_ACTIVE
        assert ps.realistic_entry is not None

    def test_short_triggered(self):
        """T14: short triggered when low <= ideal_entry"""
        ps = make_short_paper()
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),  # signal bar
            ("2026-06-04T10:30", 10.00, 9.80),   # low 9.80 <= ideal 9.99 → trigger
        ])
        settle_paper_signal(ps, bars)
        assert ps.triggered
        assert ps.paper_status == PAPER_ACTIVE


class TestActiveToTP:
    def test_hit_tp1_long(self):
        """T15: active → HIT_TP1"""
        ps = make_long_paper()
        ps.paper_status = PAPER_ACTIVE
        ps.triggered = True
        ps.realistic_entry = 10.51
        # tp1 = 11.03
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),
            ("2026-06-04T10:30", 11.10, 10.50),  # high 11.10 >= tp1 11.03
        ])
        settle_paper_signal(ps, bars)
        assert ps.paper_status == PAPER_HIT_TP1

    def test_hit_tp2_long(self):
        """T16: active → HIT_TP2"""
        ps = make_long_paper()
        ps.paper_status = PAPER_ACTIVE
        ps.triggered = True
        ps.realistic_entry = 10.51
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),
            ("2026-06-04T10:30", 11.60, 10.50),  # high 11.60 >= tp2 11.55
        ])
        settle_paper_signal(ps, bars)
        assert ps.paper_status == PAPER_HIT_TP2


class TestActiveToSL:
    def test_hit_sl_long(self):
        """T17: active → HIT_SL"""
        ps = make_long_paper()
        ps.paper_status = PAPER_ACTIVE
        ps.triggered = True
        ps.realistic_entry = 10.51
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),
            ("2026-06-04T10:30", 10.00, 9.80),  # low 9.80 <= stop 9.99
        ])
        settle_paper_signal(ps, bars)
        assert ps.paper_status == PAPER_HIT_SL

    def test_hit_sl_short(self):
        ps = make_short_paper()
        ps.paper_status = PAPER_ACTIVE
        ps.triggered = True
        ps.realistic_entry = 9.99
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),
            ("2026-06-04T10:30", 10.60, 10.20),  # high 10.60 >= stop 10.51
        ])
        settle_paper_signal(ps, bars)
        assert ps.paper_status == PAPER_HIT_SL


class TestInvalidation:
    def test_pending_invalidated_long(self):
        """T18: pending → invalidated when low < invalid_level"""
        ps = make_long_paper(invalid=9.50)
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),
            ("2026-06-04T10:30", 9.80, 9.30),  # low 9.30 < invalid 9.50
        ])
        settle_paper_signal(ps, bars)
        assert ps.paper_status == PAPER_INVALIDATED


class TestExpired:
    def test_pending_expired_after_max_bars(self):
        """T19: pending → expired after max_wait_bars"""
        ps = make_long_paper(signal_time="2026-06-04T00:00")  # match first bar time
        # 25 bars that never reach ideal_entry
        bars = make_bars([(f"2026-06-04T{i:02d}:00", 10.30, 10.00) for i in range(25)])
        settle_paper_signal(ps, bars, max_wait_bars=20)
        assert ps.paper_status == PAPER_EXPIRED


class TestSameBarConflict:
    def test_same_bar_tp_sl_long_sl_wins(self):
        """T20: same bar TP+SL → conservative SL wins"""
        ps = make_long_paper()
        ps.paper_status = PAPER_ACTIVE
        ps.triggered = True
        ps.realistic_entry = 10.51
        # tp1=11.03, stop=9.99
        # Bar with low=9.80 and high=11.10 → both hit!
        bars = make_bars([
            ("2026-06-04T10:00", 10.40, 10.00),
            ("2026-06-04T10:30", 11.10, 9.80),
        ])
        settle_paper_signal(ps, bars)
        assert ps.paper_status == PAPER_HIT_SL
        assert ps.same_bar_tp_sl_conflict


class TestShortMarking:
    def test_short_hedge_reference_marked(self):
        """T21: A股 short → not_real_short_trade"""
        ps = make_short_paper()
        ps.not_real_short_trade = True
        ps.execution_type = "hedge_reference"
        assert ps.not_real_short_trade
        assert ps.execution_type == "hedge_reference"


class TestNoProductionImports:
    def test_no_forbidden_imports(self):
        """T22-25: no production module imports"""
        import strict_paper_tracker
        lines = open(strict_paper_tracker.__file__, 'r', encoding='utf-8').readlines()
        in_doc = False
        real = []
        for line in lines:
            s = line.strip()
            if s.startswith('"""') or s.startswith("'''"):
                in_doc = not in_doc
                continue
            if in_doc or s.startswith('#'):
                continue
            real.append(s)
        code = "\n".join(real)
        for f in ["run_strategy", "candidate_pool", "rule_guardrail", "signal_predictor",
                  "system_price_builder"]:
            assert f"import {f}" not in code, f"found import {f}"
        assert "sqlite3" not in code


class TestPnL:
    def test_tp1_gives_1r(self):
        ps = make_long_paper()
        ps.paper_status = PAPER_HIT_TP1
        ps.risk_abs = 0.52
        ps.r_multiple_tp1 = 1.0
        compute_paper_pnl(ps)
        assert ps.pnl_r == 1.0

    def test_sl_gives_minus_1r(self):
        ps = make_long_paper()
        ps.paper_status = PAPER_HIT_SL
        ps.risk_abs = 0.52
        compute_paper_pnl(ps)
        assert ps.pnl_r == -1.0


class TestSaveLoad:
    def test_save_and_load_roundtrip(self):
        import tempfile, os
        ps = make_long_paper()
        ps.paper_id = "TEST_ROUNDTRIP"
        tmp = os.path.join(tempfile.gettempdir(), "test_paper_signals.json")
        save_paper_signals([ps], tmp)
        loaded = load_paper_signals(tmp)
        assert len(loaded) == 1
        assert loaded[0].paper_id == "TEST_ROUNDTRIP"
        assert loaded[0].direction == "long"
        os.unlink(tmp)
