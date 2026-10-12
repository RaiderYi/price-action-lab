"""S0-05 回归夹具：突破极端收盘阈值 (F03)。

任务书 §2.1 最小复现：
  前高100；最后棒 high=107 low=97 close=101 (pos=40%) → buy 不应通过
  前低99；最后棒 high=102 low=92 close=98 (pos=60%) → sell 不应通过
边界：pos=70% 多头、pos=30% 空头应通过（顶部/底部30%定义，闭边界）。
本测试针对旧 legacy 路径 `_is_breakout_entry`；修复后语义为 legacy_proxy_breakout。
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from signal_predictor import _is_breakout_entry  # noqa: E402


def _make_df(prior_high, prior_low, last_high, last_low, last_close, lookback=20):
    """构造 lookback+2 根K线：前 lookback+1 根在 [prior_low, prior_high] 内，
    最后一根为指定参数（函数要求 n >= lookback+2）。"""
    rows = []
    for i in range(lookback + 1):
        px = prior_low + (prior_high - prior_low) * (0.5 if i == 0 else 0.3)
        rows.append({
            "open": px, "high": prior_high, "low": prior_low,
            "close": px, "volume": 1000.0,
        })
    rows.append({
        "open": (last_high + last_low) / 2, "high": last_high,
        "low": last_low, "close": last_close, "volume": 1000.0,
    })
    df = pd.DataFrame(rows)
    return df


def _atr_from_df(df):
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(14, min_periods=1).mean().iloc[-1])


class TestBreakoutExtremeCloseFix:
    # ── F03 反例：收于区间40%/60%不应通过 ─────────────────────
    def test_long_close_at_40pct_rejected(self):
        df = _make_df(100, 95, 107, 97, 101)  # pos=(101-97)/10=0.40
        atr = _atr_from_df(df)
        ok, direction, reason = _is_breakout_entry(df, "up", atr)
        assert not ok, f"收于40%的多头棒不应判为精选突破 (reason={reason})"

    def test_short_close_at_60pct_rejected(self):
        # 任务书§2.1: 前低99；最后 high=102 low=92 close=98 (pos=0.60)
        df = _make_df(101, 99, 102, 92, 98)
        atr = _atr_from_df(df)
        ok, direction, reason = _is_breakout_entry(df, "down", atr)
        assert not ok, f"收于60%的空头棒不应判为精选突破 (reason={reason})"

    # ── 边界：闭边界 0.7/0.3 通过 ─────────────────────────────
    def test_long_close_at_70pct_passes(self):
        df = _make_df(100, 95, 107, 97, 104)  # pos=(104-97)/10=0.70
        atr = _atr_from_df(df)
        ok, direction, _ = _is_breakout_entry(df, "up", atr)
        assert ok and direction == "buy"

    def test_short_close_at_30pct_passes(self):
        # 边界：前低99，pos=(95-92)/10=0.30 → sell 通过（闭边界）
        df = _make_df(101, 99, 102, 92, 95)
        atr = _atr_from_df(df)
        ok, direction, _ = _is_breakout_entry(df, "down", atr)
        assert ok and direction == "sell"

    # ── 方向性反例：多头突破但收盘弱 → 拒绝 ───────────────────
    def test_long_breakout_weak_close_rejected(self):
        df = _make_df(100, 95, 110, 97, 101.5)  # pos≈25% 收在上部四分位之外
        atr = _atr_from_df(df)
        ok, _, _ = _is_breakout_entry(df, "up", atr)
        assert not ok

    def test_no_range_expansion_rejected(self):
        # 无区间扩张（棒区间 < 1.2×ATR）即使收盘极端也拒绝
        df = _make_df(100, 95, 100.5, 99.5, 100.4)  # 窄棒但 pos=90%
        atr = _atr_from_df(df)
        if df["high"].iloc[-1] - df["low"].iloc[-1] >= 1.2 * atr:
            pytest.skip("fixture未构成窄棒反例，不影响验收")
        ok, _, _ = _is_breakout_entry(df, "up", atr)
        assert not ok
