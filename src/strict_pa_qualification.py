"""
strict_pa_qualification.py — Phase 4.3 Strict PA Detector Qualification

Qualification layer on top of raw bar-counting detection. Does NOT modify
Brooks raw counting definitions. Only adds qualification flags, confidence
adjustments, and context arbitration.

Rules:
  P0: Direction mutual exclusivity (context arbitration)
  P0: Min pullback significance (>=0.3 ATR)
  P1: Close confirmation (debug only, not hard filter)
  P1: Bar size / doji filter (debug only)
  P1: Trading range middle demotion (qualified=false)
  P2: H1-H2 intervening pullback (record only)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd


# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

DEFAULT_QUALIFICATION_CONFIG = {
    "min_pullback_atr": 0.3,
    "enable_min_pullback_filter": True,
    "close_confirmation_mode": "debug_only",    # "debug_only" | "soft_filter" | "hard_filter"
    "enable_range_middle_demotion": True,
    "enable_direction_arbitration": True,
    "enable_h1_h2_intervening_check": False,     # P2: default disabled
}


@dataclass
class QualificationResult:
    """Result of applying qualification filters to a raw strict signal."""

    # Raw detection (unchanged from bar counting)
    raw_detected: bool = False

    # Qualification
    qualified: bool = False
    qualification_status: str = ""  # "qualified" | "blocked_by_opposite_context" | "pullback_too_shallow" | "middle_range_noise" | ...
    blocked_reason: str = ""
    dominant_context: str = ""      # "bull_pullback" | "bear_rally" | "none"
    manual_review_needed: bool = False

    # P0: Direction arbitration
    direction_match: bool = True
    market_direction: str = ""      # "up" | "down" | "neutral"
    market_phase: str = ""          # "trend" | "range" | "transition"

    # P0: Pullback significance
    pullback_depth_atr: float = 0.0
    pullback_depth_pct: float = 0.0
    pullback_significance_passed: bool = False

    # P1: Close confirmation
    close_confirmation_passed: bool = False
    close_confirmation_mode: str = "debug_only"
    close_vs_prior_close: float = 0.0
    close_vs_signal_bar_open: float = 0.0

    # P1: Bar size / doji
    signal_bar_body_pct: float = 0.0
    signal_bar_range_atr: float = 0.0
    is_doji_like: bool = False
    tail_rejection: str = ""        # "none" | "top" | "bottom" | "both"

    # P1: Range position quality
    range_position: Optional[str] = None
    range_position_allows_direction: bool = True

    # P2: H1-H2 intervening pullback
    has_intervening_pullback_between_h1_h2: bool = False
    intervening_pullback_filter_passed: bool = False

    # Confidence adjustments
    confidence_penalty_reasons: List[str] = field(default_factory=list)
    confidence_bonus_reasons: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# Core Qualification Functions
# ═══════════════════════════════════════════════════════════════════

def compute_atr(highs, lows, closes, period=20) -> float:
    """Compute ATR from arrays."""
    n = min(period, len(highs) - 1)
    if n < 2:
        return 0.0
    tr_sum = 0.0
    for i in range(-n, 0):
        h = float(highs[i])
        l = float(lows[i])
        pc = float(closes[i - 1]) if i - 1 >= -len(closes) else float(closes[i])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_sum += tr
    return tr_sum / n if n > 0 else 0.0


def check_direction_arbitration(
    signal_direction: str,
    context_type: str,
    market_direction: str,
    market_phase: str,
    range_position: Optional[str],
) -> Tuple[bool, str, str]:
    """
    P0: Determine if signal direction matches dominant market context.

    Returns (qualified, status, reason)
    """
    # Breakout / transition — use market_direction; if neutral → manual review
    if market_phase in ("breakout", "transition"):
        if market_direction == "up" and signal_direction == "short":
            return False, "blocked_by_opposite_context", \
                f"phase={market_phase} market_direction=up — short blocked"
        if market_direction == "down" and signal_direction == "long":
            return False, "blocked_by_opposite_context", \
                f"phase={market_phase} market_direction=down — long blocked"
        if market_direction == "neutral":
            return False, "neutral_market", \
                f"phase={market_phase} direction=neutral — raw only, manual review"
        return True, "qualified", ""

    # Trend up — allow bull, block bear
    if market_direction == "up" and market_phase == "trend":
        if signal_direction == "long":
            return True, "qualified", ""
        else:
            return False, "blocked_by_opposite_context", "market in uptrend — bear_rally signals blocked"

    # Trend down — allow bear, block bull
    if market_direction == "down" and market_phase == "trend":
        if signal_direction == "short":
            return True, "qualified", ""
        else:
            return False, "blocked_by_opposite_context", "market in downtrend — bull_pullback signals blocked"

    # Range — use position
    if market_phase == "range":
        if range_position == "lower_third":
            if signal_direction == "long":
                return True, "qualified", ""
            else:
                return False, "blocked_by_opposite_context", "range lower_third — long H1/H2 preferred"
        elif range_position == "upper_third":
            if signal_direction == "short":
                return True, "qualified", ""
            else:
                return False, "blocked_by_opposite_context", "range upper_third — short L1/L2 preferred"
        else:
            # Middle — raw allowed, qualified=false
            return False, "middle_range_noise", "range middle — both directions raw only, not qualified"

    # Neutral / transition — raw only, qualified=false
    if market_direction == "neutral" or market_phase == "transition":
        return False, "neutral_market", f"market direction={market_direction}, phase={market_phase} — raw only"

    # Default: allow
    return True, "qualified", ""


def check_pullback_significance(
    pullback_depth_atr: float,
    min_atr: float,
    enable_filter: bool,
) -> Tuple[bool, str]:
    """P0: Check pullback depth >= min_atr * ATR."""
    if not enable_filter or min_atr <= 0:
        return True, ""
    if pullback_depth_atr >= min_atr:
        return True, ""
    return False, f"pullback_too_shallow ({pullback_depth_atr:.2f} ATR < {min_atr})"


def check_close_confirmation(
    signal_bar_close: float,
    signal_bar_open: float,
    signal_bar_high: float,
    signal_bar_low: float,
    prior_bar_close: float,
    direction: str,
    mode: str,
) -> Tuple[bool, float, float]:
    """P1: Check close confirmation. Not a hard filter by default."""
    close_vs_prior = signal_bar_close - prior_bar_close
    close_vs_open = signal_bar_close - signal_bar_open

    passed = False
    if direction == "long":
        passed = close_vs_prior > 0 or close_vs_open > 0
    else:
        passed = close_vs_prior < 0 or close_vs_open < 0

    if mode == "hard_filter":
        return passed, close_vs_prior, close_vs_open
    # debug_only or soft_filter: always pass (record only)
    return True, close_vs_prior, close_vs_open


def check_bar_size_quality(
    signal_bar_high: float,
    signal_bar_low: float,
    signal_bar_open: float,
    signal_bar_close: float,
    atr: float,
) -> Dict:
    """P1: Record bar size / doji metrics. Debug only, no hard filter."""
    body = abs(signal_bar_close - signal_bar_open)
    range_val = signal_bar_high - signal_bar_low

    body_pct = body / max(range_val, 0.001)
    range_atr = range_val / max(atr, 0.001)

    is_doji = body_pct < 0.1

    # Tail rejection
    if signal_bar_close > signal_bar_open:
        upper_tail = (signal_bar_high - signal_bar_close) / max(range_val, 0.001)
        lower_tail = (signal_bar_open - signal_bar_low) / max(range_val, 0.001)
    else:
        upper_tail = (signal_bar_high - signal_bar_open) / max(range_val, 0.001)
        lower_tail = (signal_bar_close - signal_bar_low) / max(range_val, 0.001)

    if upper_tail > 0.6:
        tail = "top"
    elif lower_tail > 0.6:
        tail = "bottom"
    elif upper_tail > 0.4 and lower_tail > 0.4:
        tail = "both"
    else:
        tail = "none"

    return {
        "signal_bar_body_pct": round(body_pct, 3),
        "signal_bar_range_atr": round(range_atr, 3),
        "is_doji_like": is_doji,
        "tail_rejection": tail,
    }


def check_h1_h2_intervening(
    count_result,
    target_count: int,
    highs,
    lows,
) -> Tuple[bool, bool]:
    """
    P2: Check if there are bars between H1 and H2 that continued the pullback.
    Only meaningful for H2 (target_count=2).
    """
    if target_count != 2:
        return False, True  # not applicable

    events = count_result.count_events
    h1_event = None
    h2_event = None
    for ev in events:
        if ev.count_index == 1:
            h1_event = ev
        if ev.count_index == 2:
            h2_event = ev

    if h1_event is None or h2_event is None:
        return False, True

    # Check if there are bars between H1 and H2
    if h2_event.bar_index <= h1_event.bar_index + 1:
        # H2 immediately follows H1 — no intervening pullback
        return False, False

    # Check if any bar between H1 and H2 has high <= prior_high (continued pullback)
    has_intervening = False
    for i in range(h1_event.bar_index + 1, h2_event.bar_index):
        if highs[i] <= highs[i - 1]:
            has_intervening = True
            break

    return has_intervening, True


# ═══════════════════════════════════════════════════════════════════
# Main Qualification Function
# ═══════════════════════════════════════════════════════════════════

def qualify_signal(
    sr,                         # ShadowSignalResult
    market_direction: str,      # "up" | "down" | "neutral"
    market_phase: str,          # "trend" | "range" | "transition"
    highs,
    lows,
    closes,
    opens,
    pullback_depth_atr: float = 0.0,
    pullback_depth_pct: float = 0.0,
    count_result=None,          # StrictBarCountResult (for H1-H2 check)
    atr: float = 0.0,
    config: Optional[Dict] = None,
) -> QualificationResult:
    """
    Apply all qualification filters to a raw strict signal.

    Returns QualificationResult with qualified=true/false and detailed status.
    """
    if config is None:
        config = DEFAULT_QUALIFICATION_CONFIG

    qr = QualificationResult()
    qr.raw_detected = sr.detected
    qr.market_direction = market_direction
    qr.market_phase = market_phase
    qr.range_position = sr.range_position

    if not sr.detected:
        qr.qualified = False
        qr.qualification_status = "not_detected"
        return qr

    # --- P0: Direction Arbitration ---
    if config.get("enable_direction_arbitration", True):
        allowed, status, reason = check_direction_arbitration(
            sr.direction, sr.context_type,
            market_direction, market_phase, sr.range_position)
        qr.qualified = allowed
        qr.qualification_status = status
        qr.blocked_reason = reason
        qr.dominant_context = sr.context_type
        if not allowed and status != "middle_range_noise":
            qr.manual_review_needed = True
        if not allowed:
            return qr  # Short-circuit on direction block
    else:
        qr.qualified = True
        qr.qualification_status = "qualified"

    # --- P0: Pullback Significance ---
    min_atr = config.get("min_pullback_atr", 0.3)
    enable_pf = config.get("enable_min_pullback_filter", True)

    if enable_pf and atr > 0:
        qr.pullback_depth_atr = pullback_depth_atr
        qr.pullback_depth_pct = pullback_depth_pct

        passed, reason = check_pullback_significance(pullback_depth_atr, min_atr, True)
        qr.pullback_significance_passed = passed
        if not passed:
            qr.qualified = False
            qr.qualification_status = reason
            qr.blocked_reason = reason
            qr.confidence_penalty_reasons.append(f"pullback_depth={pullback_depth_atr:.2f} ATR < {min_atr}")
            return qr
    elif atr <= 0 and enable_pf:
        qr.confidence_penalty_reasons.append("ATR unavailable — pullback significance not checked")

    # --- P1: Range Middle Demotion (all phases) ---
    if config.get("enable_range_middle_demotion", True):
        if sr.range_position == "middle":
            qr.qualified = False
            qr.qualification_status = "middle_range_noise"
            qr.blocked_reason = "middle_range_noise — both directions raw only"
            qr.confidence_penalty_reasons.append("middle range signal — not qualified")
            return qr

    # --- P1: Close Confirmation (debug only) ---
    if sr.signal_bar_close is not None and sr.signal_bar_high is not None:
        signal_bar_idx = sr.signal_bar_index or -1
        if signal_bar_idx >= 1:
            prior_close = float(closes[signal_bar_idx - 1])
            passed, close_vs_prior, close_vs_open = check_close_confirmation(
                sr.signal_bar_close,
                opens[signal_bar_idx] if opens is not None and signal_bar_idx < len(opens) else sr.signal_bar_close - 0.01,
                sr.signal_bar_high,
                sr.signal_bar_low,
                prior_close,
                sr.direction,
                config.get("close_confirmation_mode", "debug_only"),
            )
            qr.close_confirmation_passed = passed
            qr.close_vs_prior_close = round(close_vs_prior, 4)
            qr.close_vs_signal_bar_open = round(close_vs_open, 4)
            qr.close_confirmation_mode = config.get("close_confirmation_mode", "debug_only")

            if not passed and config.get("close_confirmation_mode") == "hard_filter":
                qr.qualified = False
                qr.qualification_status = "close_not_confirmed"

            if passed:
                qr.confidence_bonus_reasons.append("close confirms direction")
            else:
                qr.confidence_penalty_reasons.append("close does not confirm direction")

    # --- P1: Bar Size / Doji ---
    if sr.signal_bar_high is not None and sr.signal_bar_low is not None and atr > 0:
        signal_bar_idx = sr.signal_bar_index or -1
        if signal_bar_idx >= 0 and opens is not None and signal_bar_idx < len(opens):
            bar_metrics = check_bar_size_quality(
                sr.signal_bar_high, sr.signal_bar_low,
                opens[signal_bar_idx], sr.signal_bar_close or sr.signal_bar_high,
                atr,
            )
            qr.signal_bar_body_pct = bar_metrics["signal_bar_body_pct"]
            qr.signal_bar_range_atr = bar_metrics["signal_bar_range_atr"]
            qr.is_doji_like = bar_metrics["is_doji_like"]
            qr.tail_rejection = bar_metrics["tail_rejection"]

            if qr.is_doji_like:
                qr.confidence_penalty_reasons.append("doji-like signal bar — reduces confidence")
            if bar_metrics["tail_rejection"] in ("top", "bottom") and sr.direction == "long":
                if bar_metrics["tail_rejection"] == "top":
                    qr.confidence_penalty_reasons.append("rejection tail at top — bearish for long")

    # --- P2: H1-H2 Intervening Pullback ---
    if count_result is not None and sr.count_index == 2:
        has_int, filter_applies = check_h1_h2_intervening(
            count_result, sr.count_index, highs, lows)
        qr.has_intervening_pullback_between_h1_h2 = has_int
        qr.intervening_pullback_filter_passed = has_int

        if not has_int and config.get("enable_h1_h2_intervening_check", False):
            qr.confidence_penalty_reasons.append("H1-H2 consecutive bars — no intervening pullback")
        elif has_int:
            qr.confidence_bonus_reasons.append("H1-H2 with intervening pullback — typical setup")

    # --- Final confidence ---
    if config.get("close_confirmation_passed") is None and qr.close_confirmation_passed:
        qr.confidence_bonus_reasons.append("close confirms direction")

    qr.direction_match = (qr.qualification_status == "qualified")
    qr.manual_review_needed = qr.manual_review_needed or (
        not qr.qualified and qr.raw_detected)

    return qr
