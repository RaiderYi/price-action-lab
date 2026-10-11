"""P0-fix: L1/L2 short TP1 方向修复测试

验证:
1. _detect_l2() short 方向输出 prior_low
2. _l2() short TP1 来自 prior_low 而非 LH1
3. _l2() short 无 prior_low 时 fallback 到 cp*0.94
4. L1 short 路由到 _l2() 且方向正确
5. 修复后的 short 信号通过 direction consistency
"""
import pytest, sys, os, numpy as np, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from system_price_builder import build_system_prices, _l2
from system_structure_builder import build_structure_points, _detect_swings


def _make_kline(highs, lows, closes=None):
    if closes is None:
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({"high": highs, "low": lows, "close": closes})


def _build_l2_short_kline():
    # deterministic kline: price falling, cp=100
    # swing highs at ~108(LH1), 104(LH2), swing low at ~92(prior_low)
    n = 60
    highs = [105.0] * n
    lows = [100.0] * n
    # make two swing highs above cp
    highs[15] = 108.0  # LH1 (highest)
    highs[35] = 104.0  # LH2 (lower than LH1)
    # make one swing low below cp
    lows[25] = 92.0    # prior_low
    # another swing low for swing detection
    lows[45] = 95.0
    return _make_kline(highs, lows)


class TestDetectL2ShortOutputsPriorLow:
    """_detect_l2() 在 K 线存在下方 swing low 时输出 prior_low"""

    def test_short_detects_prior_low_below_cp(self):
        df = _build_l2_short_kline()
        highs = df["high"].values.astype(float)
        lows_arr = df["low"].values.astype(float)
        closes = df["close"].values.astype(float)
        sh, sl = _detect_swings(highs, lows_arr, window=4)
        from system_structure_builder import _detect_l2
        result = _detect_l2("TEST", highs, lows_arr, closes, 100.0, "short")
        assert result["structure_status"] in ("verified", "weak")
        pts = result["structure_points"]
        assert "prior_low" in pts, f"missing prior_low, points={pts}"
        assert pts["prior_low"] < 100.0, (
            f"prior_low({pts['prior_low']}) should be < cp(100)"
        )

    def test_short_no_prior_low_when_none_below_cp(self):
        # all swing lows >= cp
        n = 50
        highs = [105.0] * n
        lows = [102.0] * n
        # swing highs
        highs[15] = 108.0
        highs[35] = 104.0
        # no swing low below cp=100 (all lows are 102)
        df = _make_kline(highs, lows)
        highs_arr = df["high"].values.astype(float)
        lows_arr = df["low"].values.astype(float)
        closes = df["close"].values.astype(float)
        from system_structure_builder import _detect_l2
        result = _detect_l2("TEST", highs_arr, lows_arr, closes, 100.0, "short")
        pts = result["structure_points"]
        assert "prior_low" not in pts, (
            f"prior_low should not exist when no swing low below cp, got {pts}"
        )


class TestL2ShortTP1FromPriorLowNotLH1:
    """L2 short: tp1 来自 prior_low，不来自 LH1"""

    def test_tp1_uses_prior_low(self):
        # cp=100, LH1=108, LH2=104, prior_low=92
        result = _l2(100.0, "short", {"LH1": 108.0, "LH2": 104.0, "prior_low": 92.0})
        assert result["tp1"] == 92.0, f"tp1 should be prior_low=92, got {result['tp1']}"
        entry_mid = (result["entry_min"] + result["entry_max"]) / 2
        assert result["tp1"] < entry_mid, (
            f"tp1({result['tp1']}) must be < entry_mid({entry_mid}) for short"
        )
        assert result["stop_loss"] > entry_mid, (
            f"stop_loss({result['stop_loss']}) must be > entry_mid({entry_mid}) for short"
        )

    def test_tp1_not_lh1(self):
        # cp=100, LH1=108, prior_low=92
        result = _l2(100.0, "short", {"LH1": 108.0, "LH2": 104.0, "prior_low": 92.0})
        assert result["tp1"] != 108.0, (
            f"tp1 must NOT be LH1=108, got {result['tp1']}"
        )


class TestL2ShortFallbackWhenNoPriorLow:
    """L2 short: 无 prior_low 时 fallback 到 cp*0.94"""

    def test_fallback_cp_094(self):
        # cp=100, LH1=108, LH2=104, no prior_low
        result = _l2(100.0, "short", {"LH1": 108.0, "LH2": 104.0})
        expected = round(100.0 * 0.94, 2)
        assert result["tp1"] == expected, f"tp1 should be {expected}, got {result['tp1']}"

    def test_fallback_prior_low_above_cp_ignored(self):
        # cp=100, prior_low=105 (above cp, should be ignored)
        result = _l2(100.0, "short", {"LH1": 108.0, "LH2": 104.0, "prior_low": 105.0})
        expected = round(100.0 * 0.94, 2)
        assert result["tp1"] == expected, (
            f"prior_low above cp should be ignored, expected {expected}, got {result['tp1']}"
        )

    def test_fallback_direction_valid(self):
        result = _l2(100.0, "short", {"LH1": 108.0, "LH2": 104.0})
        entry_mid = (result["entry_min"] + result["entry_max"]) / 2
        assert result["tp1"] < entry_mid, (
            f"fallback tp1({result['tp1']}) must be < entry_mid({entry_mid})"
        )
        assert result["stop_loss"] > entry_mid, (
            f"stop_loss({result['stop_loss']}) must be > entry_mid({entry_mid})"
        )


class TestL1ShortUsesL2BuilderAndDirectionValid:
    """L1 short 路由到 _l2()，方向应正确"""

    def test_l1_routes_to_l2_builder(self):
        # build_system_prices with L1 short
        result = build_system_prices(
            "TEST", "L1", "short", 100.0,
            {"LH1": 108.0, "LH2": 104.0, "prior_low": 92.0}
        )
        entry_mid = (result["entry_min"] + result["entry_max"]) / 2
        assert result["stop_loss"] > entry_mid, (
            f"L1 short: stop_loss({result['stop_loss']}) must be > entry_mid({entry_mid})"
        )
        assert result["tp1"] < entry_mid, (
            f"L1 short: tp1({result['tp1']}) must be < entry_mid({entry_mid})"
        )

    def test_l1_uses_prior_low_as_tp1(self):
        result = build_system_prices(
            "TEST", "L1", "short", 100.0,
            {"LH1": 108.0, "LH2": 104.0, "prior_low": 92.0}
        )
        assert result["tp1"] == 92.0, f"L1 tp1 should be prior_low=92, got {result['tp1']}"


class TestL2ShortDirectionConsistencyPasses:
    """修复后的 short 信号应通过 direction consistency 检查"""

    def test_direction_consistency_short_pass(self):
        # simulate what run_strategy does: build prices, then check direction
        result = build_system_prices(
            "TEST", "L2", "short", 100.0,
            {"LH1": 108.0, "LH2": 104.0, "prior_low": 92.0}
        )
        entry = (result["entry_min"] + result["entry_max"]) / 2
        stop = result["stop_loss"]
        tp1 = result["tp1"]
        # short: stop > entry, tp1 < entry
        assert stop > entry, f"stop({stop}) must be > entry({entry})"
        assert tp1 < entry, f"tp1({tp1}) must be < entry({entry})"

    def test_rr_positive_without_abs_masking(self):
        # verify RR is genuinely positive (reward in correct direction)
        result = build_system_prices(
            "TEST", "L2", "short", 100.0,
            {"LH1": 108.0, "LH2": 104.0, "prior_low": 92.0}
        )
        entry = (result["entry_min"] + result["entry_max"]) / 2
        risk = stop - entry if (stop := result["stop_loss"]) > entry else entry - stop
        reward = entry - result["tp1"]  # short: reward = entry - tp1
        assert risk > 0, f"risk must be > 0"
        assert reward > 0, f"reward must be > 0 (short: entry - tp1)"
        assert result["execution_rr"] > 0, f"RR must be > 0"


class TestL2LongNotBrokenByFix:
    """回归: L2 long 不受本次修复影响（仅验证 short patch 不破坏 long 编译/运行）"""

    def test_l2_long_still_produces_output(self):
        # cp=100, LH1=92 (swing low for long), LH2=95
        result = _l2(100.0, "long", {"LH1": 92.0, "LH2": 95.0})
        assert result["entry_min"] > 0
        assert result["stop_loss"] > 0
        assert result["tp1"] > 0
        assert result["execution_rr"] > 0
        # NOTE: _l2 long 分支也有方向语义问题 (TP1=LH1 在 entry 下方)
        # 但本轮只修 short，long 问题留给后续 T7

    def test_l2_long_stop_loss_below_entry(self):
        # long: SL 应在 entry 下方
        result = _l2(100.0, "long", {"LH1": 92.0, "LH2": 95.0})
        entry_mid = (result["entry_min"] + result["entry_max"]) / 2
        assert result["stop_loss"] < entry_mid, (
            f"L2 long: stop_loss({result['stop_loss']}) must be < entry_mid({entry_mid})"
        )
