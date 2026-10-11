import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from system_price_builder import build_system_prices
from system_structure_builder import build_structure_points


def _df(highs, lows, closes=None):
    if closes is None:
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({"high": highs, "low": lows, "close": closes})


def test_measured_move_outputs_target_engine_fields_long():
    n = 55
    highs = [100.0] * n
    lows = [95.0] * n
    closes = [98.0] * n
    lows[10] = 90.0
    highs[25] = 110.0
    closes[-1] = 112.0

    result = build_structure_points("X", "measured_move", "long", _df(highs, lows, closes), 112.0)

    assert result["structure_status"] == "verified"
    pts = result["structure_points"]
    assert pts["measure_start"] == 90.0
    assert pts["measure_end"] == 110.0
    assert pts["breakout_point"] == 110.0
    assert pts["measured_distance"] == 20.0
    assert pts["projected_target"] == 130.0


def test_measured_move_price_builder_uses_projected_target():
    prices = build_system_prices(
        "X",
        "measured_move",
        "long",
        112.0,
        {
            "measure_start": 90.0,
            "measure_end": 110.0,
            "breakout_point": 110.0,
            "measured_distance": 20.0,
            "projected_target": 130.0,
        },
    )

    assert prices["price_builder_status"] == "success"
    assert prices["tp2"] == 130.0
    assert prices["source_points"]["projected_target"] == 130.0
    assert "measured_move_target_engine" in prices["price_source"]


def test_h1_l1_reuse_h2_l2_detectors():
    n = 60
    highs = [100.0] * n
    lows = [98.0] * n
    highs[20] = 110.0
    lows[40] = 94.0

    h1 = build_structure_points("X", "H1", "long", _df(highs, lows), 101.0)
    assert h1["structure_source"] == "system:kline_swing_H1", f"got {h1['structure_source']}"
    assert "HL2" in h1["structure_points"], f"points: {h1['structure_points']}"

    highs = [100.0] * n
    lows = [98.0] * n
    highs[20] = 110.0
    highs[40] = 104.0
    l1 = build_structure_points("X", "L1", "short", _df(highs, lows), 99.0)
    assert "reuse:L1->L2" in l1["structure_source"]
