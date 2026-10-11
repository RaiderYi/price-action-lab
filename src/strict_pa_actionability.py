"""
strict_pa_actionability.py — Phase 4.8 KB-Aligned Actionable Signal Layer

KB-confirmed rules (Phase 4.8):
  1. Triggered = major weight (+8), NOT absolute override
  2. Same-direction family: triggered > waiting (hard)
  3. Breakout strength: strong→direction_hard, weak→bonus_only, failed→prefer_reverse
  4. Two-sided range: qualified both, actionable only one side
  5. Unresolvable → manual_review, never force direction
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class ActionableResult:
    actionable: bool = False
    actionable_status: str = ""
    actionable_blocked_reason: str = ""
    actionable_direction: str = ""
    actionable_priority_score: int = 0
    opposite_signal_present: bool = False
    opposite_signal_type: str = ""
    opposite_signal_status: str = ""
    conflict_resolution: str = ""
    two_sided_range_allowed: bool = False
    manual_action_review_needed: bool = False

    # Phase 4.8: KB-aligned fields
    breakout_strength: str = "unknown"          # strong_breakout/weak_breakout/failed_breakout_risk/unknown
    failed_breakout_risk: bool = False
    boundary_distance_score: int = 0
    signal_bar_strength_score: int = 0
    recent_momentum_score: int = 0
    triggered_bonus: int = 0                    # +8 if triggered
    actionability_decision_basis: str = ""       # explanation of the final decision


# ═══════════════════════════════════════════════════════════════════
# Breakout strength detection
# ═══════════════════════════════════════════════════════════════════

def detect_breakout_strength(
    market_phase: str,
    market_direction: str,
    highs, lows, closes,
    atr: float = 0.0,
) -> str:
    """
    Detect breakout strength.

    Returns: strong_breakout | weak_breakout | failed_breakout_risk | unknown
    """
    if market_phase not in ("breakout",):
        return "unknown"

    if atr <= 0 or len(highs) < 20:
        return "unknown"

    # Check for failed breakout risk: breakout then immediate reversal
    n = len(highs)
    recent_bars = min(10, n)

    if market_direction == "up":
        # Recent bars: find high point and check if price fell back significantly
        recent_high = max(highs[-recent_bars:])
        recent_low = min(lows[-recent_bars:])
        if recent_high > 0 and (recent_high - closes[-1]) / max(atr, 0.001) > 1.5:
            return "failed_breakout_risk"

        # Strong breakout: sustained above prior high with range expansion
        if n >= 10:
            prev_high = max(highs[-20:-10]) if n >= 20 else max(highs[:n//2])
            if closes[-1] > prev_high and (highs[-1] - lows[-1]) > atr * 1.0:
                return "strong_breakout"

        # Weak breakout: small range, quick retest
        bar_range = highs[-1] - lows[-1]
        if bar_range < atr * 0.5:
            return "weak_breakout"

    elif market_direction == "down":
        recent_high = max(highs[-recent_bars:])
        recent_low = min(lows[-recent_bars:])
        if (closes[-1] - recent_low) / max(atr, 0.001) > 1.5:
            return "failed_breakout_risk"

        if n >= 10:
            prev_low = min(lows[-20:-10]) if n >= 20 else min(lows[:n//2])
            if closes[-1] < prev_low and (highs[-1] - lows[-1]) > atr * 1.0:
                return "strong_breakout"

        bar_range = highs[-1] - lows[-1]
        if bar_range < atr * 0.5:
            return "weak_breakout"

    return "unknown"


# ═══════════════════════════════════════════════════════════════════
# Priority scoring (KB-aligned)
# ═══════════════════════════════════════════════════════════════════

def compute_priority_score(sr, total_bars: int = 0,
                           breakout_strength: str = "unknown",
                           market_direction: str = "neutral",
                           atr: float = 0.0) -> Tuple[int, Dict]:
    """
    Compute actionable priority score with KB-aligned weights.
    Returns (score, component_breakdown).
    """
    components = {}

    # 1. Triggered bonus (KB: major weight, not absolute — +8 instead of +10)
    components['triggered_bonus'] = 8 if sr.triggered else 0

    # 2. Boundary distance (closer to boundary = higher)
    boundary = 0
    if sr.range_position == "lower_third" and sr.direction == "long":
        boundary = 6
    elif sr.range_position == "upper_third" and sr.direction == "short":
        boundary = 6
    elif sr.range_position in ("lower_third", "upper_third"):
        boundary = 3  # Correct boundary but wrong direction
    components['boundary_distance'] = boundary

    # 3. Signal bar strength
    strength = 0
    if hasattr(sr, 'signal_bar_range_atr') and sr.signal_bar_range_atr > 0:
        if sr.signal_bar_range_atr >= 0.8:
            strength = 3  # Strong bar
        elif sr.signal_bar_range_atr >= 0.5:
            strength = 2
        else:
            strength = 1
    else:
        strength = 2  # Default moderate
    components['signal_bar_strength'] = strength

    # 4. Recent momentum (same direction as signal = bonus)
    momentum = 0
    if sr.direction == market_direction:
        momentum = 3
    elif market_direction in ("up", "down"):
        momentum = 1  # Opposite direction has some potential
    components['recent_momentum'] = momentum

    # 5. Signal quality
    quality_map = {"good": 3, "moderate": 2, "weak": 1, "": 0}
    components['quality'] = quality_map.get(sr.signal_quality, 1)

    # 6. Recency
    recency = 0
    if total_bars > 0 and sr.signal_bar_index is not None:
        recency = int((sr.signal_bar_index / total_bars) * 3)
    components['recency'] = recency

    # 7. H2/L2 > H1/L1
    components['count_bonus'] = 1 if sr.count_index >= 2 else 0

    # 8. Middle range penalty
    components['middle_penalty'] = -4 if sr.middle_range_signal else 0

    # 9. Doji penalty
    components['doji_penalty'] = -2 if (hasattr(sr, 'is_doji_like') and sr.is_doji_like) else 0

    total = sum(components.values())
    return total, components


# ═══════════════════════════════════════════════════════════════════
# Conflict resolution (KB-aligned)
# ═══════════════════════════════════════════════════════════════════

def resolve_actionable_conflict(
    long_signals: List,
    short_signals: List,
    market_phase: str,
    market_direction: str,
    breakout_strength: str = "unknown",
    total_bars: int = 0,
    atr: float = 0.0,
) -> Tuple[Optional[str], str, str]:
    """
    KB-aligned conflict resolution.

    Returns (winning_direction, resolution_type, reason)
    """
    long_cand = [s for s in long_signals if s.qualified]
    short_cand = [s for s in short_signals if s.qualified]

    if not long_cand and not short_cand:
        return None, "no_signal", ""
    if not short_cand:
        return "long", "only_long", ""
    if not long_cand:
        return "short", "only_short", ""

    # Transition phase → manual review
    if market_phase == "transition":
        return None, "manual", "transition phase — manual review needed"

    # Check two-sided range boundary positions
    long_lower = any(s.range_position == "lower_third" for s in long_cand)
    short_upper = any(s.range_position == "upper_third" for s in short_cand)
    is_two_sided = long_lower and short_upper

    # ═══ KB Rule: Breakout tiebreaker ═══
    if market_phase == "breakout":
        if breakout_strength == "strong_breakout":
            # Hard rule: direction must match market_direction
            if market_direction == "up":
                return "long", "strong_breakout", "strong breakout up → long only"
            elif market_direction == "down":
                return "short", "strong_breakout", "strong breakout down → short only"
        elif breakout_strength == "weak_breakout":
            # Bonus only — fall through to scoring
            pass
        elif breakout_strength == "failed_breakout_risk":
            # Prefer opposite direction
            if market_direction == "up":
                return "short", "failed_breakout", "failed breakout up → prefer short reversal"
            elif market_direction == "down":
                return "long", "failed_breakout", "failed breakout down → prefer long reversal"
        # unknown → fall through to manual review at the end

    # ═══ Same-direction family: triggered > waiting (hard) ═══
    # Within each direction, keep only the best signal
    def pick_best(signals):
        if not signals: return []
        quality_order = {"good": 3, "moderate": 2, "weak": 1}
        triggered = [s for s in signals if s.triggered]
        if triggered:
            best = max(triggered, key=lambda s: quality_order.get(s.signal_quality, 0))
            return [best]
        best = max(signals, key=lambda s: quality_order.get(s.signal_quality, 0))
        return [best]

    long_cand = pick_best(long_cand)
    short_cand = pick_best(short_cand)

    # ═══ Two-sided range handling ═══
    if is_two_sided:
        # Both valid at opposite boundaries. Score each independently.
        long_score, _ = compute_priority_score(long_cand[0], total_bars,
                                                breakout_strength, market_direction, atr) if long_cand else (0, {})
        short_score, _ = compute_priority_score(short_cand[0], total_bars,
                                                 breakout_strength, market_direction, atr) if short_cand else (0, {})

        if long_score > short_score + 3:
            return "long", "range_two_sided_score", f"two-sided range: long={long_score} vs short={short_score}"
        elif short_score > long_score + 3:
            return "short", "range_two_sided_score", f"two-sided range: short={short_score} vs long={long_score}"
        else:
            return None, "range_two_sided_tie", f"two-sided range tied (long={long_score} short={short_score}) → manual"

    # ═══ Priority scoring tiebreaker ═══
    long_score = 0
    short_score = 0
    if long_cand and short_cand:
        long_score, _ = compute_priority_score(long_cand[0], total_bars,
                                                breakout_strength, market_direction, atr)
        short_score, _ = compute_priority_score(short_cand[0], total_bars,
                                                 breakout_strength, market_direction, atr)

        if long_score > short_score + 3:
            return "long", "priority_wins", f"long={long_score} > short={short_score} (+3 margin)"
        elif short_score > long_score + 3:
            return "short", "priority_wins", f"short={short_score} > long={long_score} (+3 margin)"

        # Close scores — use market_direction as bonus
        if market_direction == "up":
            return "long", "context_wins", f"close scores (long={long_score} short={short_score}) + direction=up → long"
        elif market_direction == "down":
            return "short", "context_wins", f"close scores (long={long_score} short={short_score}) + direction=down → short"

        # Unknown breakout + tie → manual review
        if breakout_strength == "unknown" and market_phase == "breakout":
            return None, "manual", "breakout phase with unknown strength + tie → manual review"

        return None, "manual", f"tie (long={long_score} short={short_score}) → manual review needed"

    # Only one side — that side wins
    if long_cand:
        return "long", "only_qualified", ""
    if short_cand:
        return "short", "only_qualified", ""

    return None, "no_signal", ""


# ═══════════════════════════════════════════════════════════════════
# Main Actionability Function (KB-aligned)
# ═══════════════════════════════════════════════════════════════════

def apply_actionability(
    all_signals: List,
    market_phase: str,
    market_direction: str,
    total_bars: int = 0,
    highs=None, lows=None, closes=None,
    atr: float = 0.0,
) -> List:
    """
    Apply KB-aligned actionable layer to all qualified signals for one symbol.
    """
    # Detect breakout strength
    breakout_strength = "unknown"
    failed_risk = False
    if market_phase == "breakout" and highs is not None:
        breakout_strength = detect_breakout_strength(
            market_phase, market_direction, highs,
            lows if lows is not None else highs,
            closes if closes is not None else highs, atr)
        failed_risk = (breakout_strength == "failed_breakout_risk")

    # Collect qualified
    long_qual = [s for s in all_signals if s.qualified and s.direction == "long"]
    short_qual = [s for s in all_signals if s.qualified and s.direction == "short"]

    # Resolve
    winning_dir, resolution_type, reason = resolve_actionable_conflict(
        long_qual, short_qual, market_phase, market_direction,
        breakout_strength, total_bars, atr)

    # Check two-sided
    long_lower = any(s.range_position == "lower_third" for s in long_qual)
    short_upper = any(s.range_position == "upper_third" for s in short_qual)
    is_two_sided = long_lower and short_upper

    # Apply to each signal
    for sr in all_signals:
        # Phase 4.8 fields
        sr.breakout_strength = breakout_strength
        sr.failed_breakout_risk = failed_risk

        if not sr.qualified:
            sr.actionable = False
            sr.actionable_status = "not_qualified"
            sr.actionable_blocked_reason = "did not pass qualification"
            continue

        # Opposite signal present
        opp = short_qual if sr.direction == "long" else long_qual
        sr.opposite_signal_present = len(opp) > 0
        if opp:
            sr.opposite_signal_type = opp[0].shadow_signal_type if opp else ""
            sr.opposite_signal_status = "triggered" if any(s.triggered for s in opp) else "waiting"

        sr.two_sided_range_allowed = is_two_sided

        # Compute priority score
        score, components = compute_priority_score(
            sr, total_bars, breakout_strength, market_direction, atr)
        sr.actionable_priority_score = score
        sr.triggered_bonus = components.get('triggered_bonus', 0)
        sr.boundary_distance_score = components.get('boundary_distance', 0)
        sr.signal_bar_strength_score = components.get('signal_bar_strength', 0)
        sr.recent_momentum_score = components.get('recent_momentum', 0)

        # Decision
        if winning_dir == sr.direction:
            sr.actionable = True
            sr.actionable_status = "actionable"
            sr.actionable_blocked_reason = ""
            sr.conflict_resolution = resolution_type
            sr.actionability_decision_basis = f"{resolution_type}: {reason}"
            sr.manual_action_review_needed = (resolution_type in ("range_two_sided_tie", "manual"))
        elif winning_dir is None:
            sr.actionable = False
            sr.actionable_status = "conflict_unresolved"
            sr.actionable_blocked_reason = reason
            sr.conflict_resolution = "manual"
            sr.actionability_decision_basis = f"unresolved: {reason}"
            sr.manual_action_review_needed = True
        else:
            sr.actionable = False
            sr.actionable_status = "blocked_by_opposite_signal"
            sr.actionable_blocked_reason = f"opposite ({winning_dir}) won: {reason}"
            sr.conflict_resolution = resolution_type
            sr.actionability_decision_basis = f"{resolution_type}: {reason}"
            sr.manual_action_review_needed = False

    return all_signals
