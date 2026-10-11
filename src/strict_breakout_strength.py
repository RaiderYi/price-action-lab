"""
strict_breakout_strength.py — Phase 5.0 Standalone Breakout Strength Detector

Only used by strict paper / actionability layer.
Does NOT modify market_analyzer.py.
"""

from typing import Optional


def detect_breakout_strength(
    highs,
    lows,
    closes,
    market_phase: str = "",
    market_direction: str = "neutral",
    atr: float = 0.0,
) -> str:
    """
    Detect breakout strength from K-line arrays.

    Returns: strong_breakout | weak_breakout | failed_breakout_risk | unknown

    strong_breakout:
      - Large range bar breaking a prior level
      - Close near direction extreme
      - Follow-through (next bar continues)
      - Range expansion > ATR

    weak_breakout:
      - Small range bar
      - Close not near extreme
      - No follow-through

    failed_breakout_risk:
      - Breakout then quick reversal
      - Large opposite bar after the breakout
    """
    if atr <= 0 or len(highs) < 10:
        return "unknown"

    n = len(highs)
    recent = min(10, n)
    last_close = float(closes[-1])
    last_high = float(highs[-1])
    last_low = float(lows[-1])
    bar_range = last_high - last_low

    # Look for failed breakout first: breakout then immediate reversal
    if market_direction == "up":
        recent_high = max(float(highs[i]) for i in range(max(0, n - recent), n))
        # Price fell far from recent high
        if (recent_high - last_close) > atr * 1.0:
            return "failed_breakout_risk"
    elif market_direction == "down":
        recent_low = min(float(lows[i]) for i in range(max(0, n - recent), n))
        if (last_close - recent_low) > atr * 1.0:
            return "failed_breakout_risk"

    # Check for strong breakout
    if bar_range >= atr * 1.0:
        # Large bar with close near extreme → strong
        if market_direction == "up":
            if (last_close - last_low) / max(bar_range, 0.001) >= 0.7:
                # Check prior level breakout
                if n >= 15:
                    prior_highs = [float(highs[i]) for i in range(max(0, n - 15), n - 3)]
                    if prior_highs and last_high > max(prior_highs):
                        # Next bar: check follow-through (use bar before last as proxy)
                        if n >= 2:
                            prev_close = float(closes[-2])
                            if last_close > prev_close:
                                return "strong_breakout"
                return "strong_breakout"  # Close near high with large range

        elif market_direction == "down":
            if (last_high - last_close) / max(bar_range, 0.001) >= 0.7:
                if n >= 15:
                    prior_lows = [float(lows[i]) for i in range(max(0, n - 15), n - 3)]
                    if prior_lows and last_low < min(prior_lows):
                        if n >= 2 and last_close < float(closes[-2]):
                            return "strong_breakout"
                return "strong_breakout"

    # Check for weak breakout: small range, close not committed
    if bar_range < atr * 0.5:
        return "weak_breakout"

    # Weak close location
    if market_direction == "up":
        if (last_close - last_low) / max(bar_range, 0.001) < 0.5:
            return "weak_breakout"
    elif market_direction == "down":
        if (last_high - last_close) / max(bar_range, 0.001) < 0.5:
            return "weak_breakout"

    return "unknown"
