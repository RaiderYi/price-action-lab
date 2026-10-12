import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wedge_replay import _settle_trade, compute_stats, replay_wedge


def make_replay_wedge_df(n=90):
    highs = np.full(n, 100.0)
    lows = np.full(n, 97.0)
    closes = np.full(n, 99.0)

    for idx, price in [(10, 102), (30, 106), (50, 110)]:
        highs[idx] = price
        lows[idx] = price - 3
        closes[idx] = price - 1
        for off in range(1, 4):
            if idx - off >= 0:
                highs[idx - off] = min(highs[idx - off], price - 1 - off * 0.1)
            if idx + off < n:
                highs[idx + off] = min(highs[idx + off], price - 1 - off * 0.1)

    closes[60:] = 109
    highs[60:] = 109.5
    lows[60:] = 108.5
    lows[66] = 101.0
    lows[67] = 99.5
    dates = [f"2024-01-{i + 1:02d}" for i in range(n)]
    return pd.DataFrame({
        "date": dates,
        "open": closes,
        "high": highs,
        "low": lows,
        "close": closes,
    })


def test_settle_long_hits_tp():
    future = pd.DataFrame({"high": [103, 111], "low": [99, 101], "close": [102, 110]})
    result, r_value, bars = _settle_trade(future, "long", 100, 95, 110)

    assert result == "HIT_TP"
    assert r_value == 2.0
    assert bars == 2


def test_settle_short_hits_sl_before_tp_on_same_bar():
    future = pd.DataFrame({"high": [106], "low": [89], "close": [95]})
    result, r_value, bars = _settle_trade(future, "short", 100, 105, 90)

    assert result == "HIT_SL"
    assert r_value == -1.0
    assert bars == 1


def test_replay_records_no_future_signal_window():
    signals = replay_wedge(make_replay_wedge_df(), "X", settle_bars=10, min_bars=60)

    assert signals
    for signal in signals:
        assert signal["source_window_end_index"] == signal["signal_index"] - 1
        assert signal["settle_start_index"] == signal["signal_index"] + 1
        assert signal["push_3_index"] <= signal["source_window_end_index"] - 3
        assert signal["price_source"] == "system:wedge_push_based"


def test_compute_stats_has_required_wedge_metrics():
    signals = [
        {"result": "HIT_TP", "R": 2.0, "direction": "long"},
        {"result": "HIT_SL", "R": -1.0, "direction": "long"},
        {"result": "HIT_TP", "R": 3.0, "direction": "short"},
        {"result": "EXPIRED", "R": 0, "direction": "short"},
    ]

    stats = compute_stats(signals)

    assert stats["win_rate"] == 0.667
    assert stats["expectancy"] == 1.333
    assert "trimmed_expectancy_95" in stats
    assert "max_drawdown" in stats
    assert stats["long"]["count"] == 2
    assert stats["short"]["count"] == 1
