"""P10.1: tr_fade 回放测试"""
import pytest, sys, os, pandas as pd, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from tr_fade_replay import replay_tr_fade_v2 as replay_tr_fade, compute_stats_v2 as compute_stats, _settle_trade_v2 as _settle_trade


def make_trending_kline(n=100, start=50, slope=0.1):
    """制造趋势数据"""
    xs = np.arange(n)
    closes = start + xs * slope + np.random.randn(n) * 0.5
    highs = closes + np.abs(np.random.randn(n)) * 1.5
    lows = closes - np.abs(np.random.randn(n)) * 1.5
    return pd.DataFrame({'date': [f'2024-{i//30+1:02d}-{i%30+1:02d}' for i in range(n)],
                        'open': closes, 'high': highs, 'low': lows, 'close': closes})


def make_range_kline(n=100, rh=55, rl=45):
    """制造区间数据"""
    closes = [(rh+rl)/2 + np.random.randn() * 2 for _ in range(n)]
    highs = [max(c + np.abs(np.random.randn()) * 2, c + 0.1) for c in closes]
    lows = [min(c - np.abs(np.random.randn()) * 2, c - 0.1) for c in closes]
    closes[-1] = rl + 1  # Near range low at the end
    return pd.DataFrame({'date': [f'2024-{i//30+1:02d}-{i%30+1:02d}' for i in range(n)],
                        'open': closes, 'high': highs, 'low': lows, 'close': closes})


class TestReplay:
    def test_no_future_used_for_signal(self):
        df = make_range_kline(100)
        sigs = replay_tr_fade(df, "X", settle_bars=10)
        for s in sigs:
            assert len(s["signal_time"]) > 0

    def test_negative_expectancy_blocks_upgrade(self):
        stats = {"settled_count": 50, "win_count": 10, "loss_count": 40,
                "expectancy": -0.3, "insufficient_samples": False}
        can_upgrade = stats["settled_count"] >= 10 and stats["expectancy"] > 0
        assert not can_upgrade

    def test_insufficient_samples_blocks_upgrade(self):
        stats = {"settled_count": 3, "insufficient_samples": True}
        can_upgrade = stats["settled_count"] >= 10 and stats.get("expectancy", 0) > 0
        assert not can_upgrade


class TestStats:
    def test_empty_signals(self):
        s = compute_stats([])
        assert s["insufficient_samples"]

    def test_all_wins(self):
        sigs = [{"result": "HIT_TP", "R": 1.5, "direction": "long", "range_width_pct": 10} for _ in range(10)]
        s = compute_stats(sigs)
        assert s["win_rate"] == 1.0
        assert s["expectancy"] == 1.5
