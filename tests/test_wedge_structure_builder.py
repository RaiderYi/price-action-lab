import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from system_structure_builder import build_structure_points


def _df(highs, lows):
    closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({"high": highs, "low": lows, "close": closes})


def make_top_wedge(indices=(10, 27, 45), prices=(103, 106, 109), n=60):
    highs = np.full(n, 100.0)
    lows = np.full(n, 97.0)
    for idx, price in zip(indices, prices):
        highs[idx] = price
        lows[idx] = price - 3
        for off in range(1, 4):
            if idx - off >= 0:
                highs[idx - off] = min(highs[idx - off], price - 1 - off * 0.1)
            if idx + off < n:
                highs[idx + off] = min(highs[idx + off], price - 1 - off * 0.1)
    return _df(highs, lows)


def make_bottom_wedge(indices=(10, 27, 45), prices=(97, 94, 91), n=60):
    highs = np.full(n, 103.0)
    lows = np.full(n, 100.0)
    for idx, price in zip(indices, prices):
        lows[idx] = price
        highs[idx] = price + 3
        for off in range(1, 4):
            if idx - off >= 0:
                lows[idx - off] = max(lows[idx - off], price + 1 + off * 0.1)
            if idx + off < n:
                lows[idx + off] = max(lows[idx + off], price + 1 + off * 0.1)
    return _df(highs, lows)


def test_detects_confirmed_wedge_top_from_higher_highs():
    result = build_structure_points("X", "wedge", "short", make_top_wedge(), 108)

    assert result["structure_status"] == "verified"
    pts = result["structure_points"]
    assert pts["push_1_price"] == 103
    assert pts["push_2_price"] == 106
    assert pts["push_3_price"] == 109
    assert pts["wedge_type"] == "wedge_top_reversal"
    assert pts["wedge_direction"] == "up"
    assert pts["reversal_direction"] == "short"
    assert pts["wedge_extreme"] == 109
    assert pts["wedge_start"] == 103
    assert pts["push_spacing_bars"] >= 3
    assert pts["wedge_duration_bars"] >= 15
    assert pts["push_3_confirmed"] is True


def test_detects_confirmed_wedge_bottom_from_lower_lows():
    result = build_structure_points("X", "wedge", "long", make_bottom_wedge(), 92)

    assert result["structure_status"] == "verified"
    pts = result["structure_points"]
    assert pts["push_1_price"] == 97
    assert pts["push_2_price"] == 94
    assert pts["push_3_price"] == 91
    assert pts["wedge_type"] == "wedge_bottom_reversal"
    assert pts["wedge_direction"] == "down"
    assert pts["reversal_direction"] == "long"
    assert pts["wedge_extreme"] == 91
    assert pts["wedge_start"] == 97


def test_wrong_direction_is_insufficient():
    result = build_structure_points("X", "wedge", "long", make_top_wedge(), 108)

    assert result["structure_status"] == "insufficient"


def test_insufficient_when_duration_too_short():
    df = make_top_wedge(indices=(8, 14, 22), prices=(103, 106, 109), n=35)
    result = build_structure_points("X", "wedge", "short", df, 108)

    assert result["structure_status"] == "insufficient"
    assert any("three-push" in reason or "wedge" in reason for reason in result["missing_points"])
