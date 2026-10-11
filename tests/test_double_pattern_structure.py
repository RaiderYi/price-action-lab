import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from signal_maturity import can_enter_main_shortlist, get_maturity
from system_price_builder import build_system_prices
from system_structure_builder import build_structure_points


def _df(highs, lows, closes=None):
    if closes is None:
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({"high": highs, "low": lows, "close": closes})


def make_double_bottom():
    n = 60
    highs = [100.0] * n
    lows = [95.0] * n
    closes = [98.0] * n
    lows[10] = 90.0
    highs[20] = 105.0
    lows[30] = 91.0
    highs[-1] = 107.0
    lows[-1] = 104.0
    closes[-1] = 106.0
    return _df(highs, lows, closes)


def make_double_top():
    n = 60
    highs = [105.0] * n
    lows = [100.0] * n
    closes = [102.0] * n
    highs[10] = 110.0
    lows[20] = 95.0
    highs[30] = 109.0
    highs[-1] = 96.0
    lows[-1] = 93.0
    closes[-1] = 94.0
    return _df(highs, lows, closes)


def test_double_bottom_structure_fields_and_target():
    result = build_structure_points("X", "double_bottom", "long", make_double_bottom(), 106.0)

    assert result["structure_status"] == "verified"
    pts = result["structure_points"]
    assert pts["bottom_1"] == 90.0
    assert pts["bottom_2"] == 91.0
    assert pts["neckline"] == 105.0
    assert pts["breakout_point"] == 105.0
    assert pts["pattern_height"] == 15.0
    assert pts["projected_target"] == 120.0


def test_double_bottom_price_builder():
    prices = build_system_prices(
        "X",
        "double_bottom",
        "long",
        106.0,
        {
            "bottom_1": 90.0,
            "bottom_2": 91.0,
            "neckline": 105.0,
            "breakout_point": 105.0,
            "pattern_height": 15.0,
            "projected_target": 120.0,
        },
    )

    assert prices["price_builder_status"] == "success"
    assert prices["tp1"] == 120.0
    assert "double_bottom" in prices["price_source"]


def test_double_top_structure_fields_and_target():
    result = build_structure_points("X", "double_top", "short", make_double_top(), 94.0)

    assert result["structure_status"] == "verified"
    pts = result["structure_points"]
    assert pts["top_1"] == 110.0
    assert pts["top_2"] == 109.0
    assert pts["neckline"] == 95.0
    assert pts["breakdown_point"] == 95.0
    assert pts["pattern_height"] == 15.0
    assert pts["projected_target"] == 80.0


def test_double_top_price_builder():
    prices = build_system_prices(
        "X",
        "double_top",
        "short",
        94.0,
        {
            "top_1": 110.0,
            "top_2": 109.0,
            "neckline": 95.0,
            "breakdown_point": 95.0,
            "pattern_height": 15.0,
            "projected_target": 80.0,
        },
    )

    assert prices["price_builder_status"] == "success"
    assert prices["tp1"] == 80.0
    assert "double_top" in prices["price_source"]


def test_double_patterns_stay_structure_ready_not_entries():
    for signal_type in ["double_bottom", "double_top"]:
        assert get_maturity(signal_type) == "STRUCTURE_READY"
        assert not can_enter_main_shortlist(signal_type)
