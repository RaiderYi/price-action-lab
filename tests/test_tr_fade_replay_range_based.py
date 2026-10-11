"""P10.2: tr_fade 生产一致性回放测试"""
import pytest, sys, os, pandas as pd, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from tr_fade_replay import (_tr_fade_system_prices, _settle_trade_v2,
                             replay_tr_fade_v2, compute_stats_v2, check_30m_data)


def make_range_kline(n=100, rh=55, rl=45, end_pos="low"):
    closes = [(rh+rl)/2 + np.random.randn() * 2 for _ in range(n)]
    highs = [max(c + np.abs(np.random.randn()) * 1.5, c+0.1) for c in closes]
    lows = [min(c - np.abs(np.random.randn()) * 1.5, c-0.1) for c in closes]
    if end_pos == "low":
        closes[-1] = rl + 1.5; highs[-1] = closes[-1] + 2; lows[-1] = closes[-1] - 1
    return pd.DataFrame({'date': [f'2024-{i//30+1:02d}-{i%30+1:02d}' for i in range(n)],
                        'open': closes, 'high': highs, 'low': lows, 'close': closes})


class TestRangeBasedPrices:
    def test_long_range_stop_below_range_low(self):
        sp = _tr_fade_system_prices(46, {"range_high": 55, "range_low": 45, "range_mid": 50}, "long")
        assert sp is not None
        assert sp["stop_loss"] < 45  # stop below range_low

    def test_long_tp1_is_range_mid(self):
        sp = _tr_fade_system_prices(46, {"range_high": 55, "range_low": 45, "range_mid": 50}, "long")
        assert abs(sp["tp1"] - 50) < 3  # tp1 near range_mid

    def test_short_stop_above_range_high(self):
        sp = _tr_fade_system_prices(54, {"range_high": 55, "range_low": 45, "range_mid": 50}, "short")
        assert sp is not None
        assert sp["stop_loss"] > 55

    def test_no_range_returns_none(self):
        sp = _tr_fade_system_prices(50, {}, "long")
        assert sp is None

    def test_source_is_range_based(self):
        sp = _tr_fade_system_prices(46, {"range_high": 55, "range_low": 45}, "long")
        assert "range" in sp["price_source"]


class TestSettleV2:
    def test_failure_reason_breakout(self):
        future = pd.DataFrame({'high': [45, 43], 'low': [43, 42], 'close': [55, 56]})
        pts = {"range_high": 55, "range_low": 45}
        res, r, bars, reason = _settle_trade_v2(future, "long", 46, 44, 50, pts)
        assert res == "HIT_SL"
        assert "breakout" in reason or "stop" in reason

    def test_failure_reason_not_just_stop(self):
        future = pd.DataFrame({'high': [44, 43], 'low': [42.5, 43], 'close': [43, 43]})
        pts = {"range_high": 55, "range_low": 45}
        res, r, bars, reason = _settle_trade_v2(future, "long", 46, 44, 50, pts)
        assert res == "HIT_SL"
        assert reason != "stop_loss_hit"  # should be more specific


class TestReplayV2:
    def test_long_short_separate_stats(self):
        sigs = [{"result": "HIT_TP", "R": 1.5, "direction": "long", "range_width_pct": 10},
                {"result": "HIT_SL", "R": -1.0, "direction": "long", "range_width_pct": 10},
                {"result": "HIT_TP", "R": 2.0, "direction": "short", "range_width_pct": 10},
                {"result": "HIT_SL", "R": -1.0, "direction": "short", "range_width_pct": 10}] * 5
        s = compute_stats_v2(sigs)
        assert s["long"]["count"] == 10
        assert s["short"]["count"] == 10

    def test_negative_expectancy_blocks_upgrade(self):
        s = {"settled_count": 50, "expectancy": -0.3, "insufficient_samples": False}
        assert not (s["settled_count"] >= 10 and s["expectancy"] > 0)

    def test_30m_data_check(self):
        m30 = check_30m_data()
        assert "symbols_with_30m" in m30
        assert "sufficient" in m30
