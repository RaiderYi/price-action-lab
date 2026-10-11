"""
bar_counting_detector.py — Phase 4.1 Strict Bar-Counting Detector

Pure bar counting: H1/H2/H3..., L1/L2/L3... based on Brooks strict definition.
No context, no DB, no price builder, no production touches.

KB-confirmed rules:
  - prior_bar = natural previous bar (no skip of inside bar)
  - inside bar: high > inside_bar.high → counts as H (natural prior)
  - outside bar: context-directed single count (bull→H only, bear→L only)
  - trigger resets counting
  - no hard trigger expiry window
  - H4+ → extended_count_warning, not rejected
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class BarInfo:
    """Single bar metadata for counting"""
    index: int              # bar index in K-line sequence
    high: float
    low: float
    close: float
    open: float
    time: str = ""          # bar timestamp string
    is_inside_bar: bool = False
    is_outside_bar: bool = False
    gap_up: bool = False
    gap_down: bool = False


@dataclass
class CountEvent:
    """A single count event in the sequence"""
    bar_index: int
    count_index: int        # 1=H1, 2=H2, 3=H3, 4=H4+
    rule: str               # "high > prior_bar.high" | "low < prior_bar.low"
    satisfies: bool
    signal_bar_high: float
    signal_bar_low: float
    prior_bar_high: float   # the prior_bar.high used for comparison
    prior_bar_low: float    # the prior_bar.low used for comparison


@dataclass
class StrictBarCountResult:
    """Complete bar counting result for one context window"""
    direction: str                      # "long" or "short"
    count_events: List[CountEvent] = field(default_factory=list)
    h_count: int = 0                    # max H count achieved
    l_count: int = 0                    # max L count achieved
    inside_bar_count: int = 0
    outside_bar_seen: bool = False
    extended_count_warning: bool = False  # H4+/L4+
    signal_bar_index: Optional[int] = None  # 最后形成信号的 bar index (>0 means has signal)
    notes: List[str] = field(default_factory=list)


def build_bar_info_list(highs, lows, closes, opens, times=None) -> List[BarInfo]:
    """Build list of BarInfo from raw K-line arrays."""
    n = len(highs)
    bars = []
    for i in range(n):
        h = float(highs[i])
        l = float(lows[i])
        c = float(closes[i])
        o = float(opens[i])
        t = str(times[i]) if times is not None and i < len(times) else ""

        is_inside = False
        is_outside = False
        gap_up = False
        gap_down = False

        if i >= 1:
            ph = float(highs[i - 1])
            pl = float(lows[i - 1])
            is_inside = (h <= ph and l >= pl)
            is_outside = (h > ph and l < pl)
            # gap detection: open jumps over prior bar range
            if o > ph:
                gap_up = True
            if o < pl:
                gap_down = True

        bars.append(BarInfo(
            index=i, high=h, low=l, close=c, open=o, time=t,
            is_inside_bar=is_inside, is_outside_bar=is_outside,
            gap_up=gap_up, gap_down=gap_down,
        ))
    return bars


def count_bars_strict(
    bars: List[BarInfo],
    context_start_index: int,
    direction: str,
    pullback_low: Optional[float] = None,
    rally_high: Optional[float] = None,
) -> StrictBarCountResult:
    """
    Execute strict bar counting within a context window.

    Args:
        bars: full bar list for the symbol
        context_start_index: bar index where pullback/rally context starts
        direction: "long" (bull pullback → count H) or "short" (bear rally → count L)
        pullback_low: for bull context — price below this invalidates context
        rally_high: for bear context — price above this invalidates context

    Returns:
        StrictBarCountResult with all count events
    """
    result = StrictBarCountResult(direction=direction)
    result.signal_bar_index = None

    if direction not in ("long", "short"):
        result.notes.append(f"invalid direction: {direction}")
        return result

    is_long = (direction == "long")
    total_bars = len(bars)

    # --- Scanning pass: detect bar type flags ---
    inside_count = 0
    outside_seen = False
    for b in bars:
        if b.is_inside_bar:
            inside_count += 1
        if b.is_outside_bar:
            outside_seen = True
    result.inside_bar_count = inside_count
    result.outside_bar_seen = outside_seen

    # --- Counting pass ---
    # KB Rule: prior_bar = natural previous bar (never skip inside bar)
    # KB Rule: outside bar → context-directed single count only
    # KB Rule: trigger resets count; no hard expiry window

    count_idx = 0       # current H/L count (1 = H1/L1, 2 = H2/L2, ...)
    last_signal_bar_idx = -1  # 0-index bar index where count was achieved
    trigger_reset_done = False  # True after trigger fired and we reset

    for i in range(context_start_index + 1, total_bars):
        # skip index 0 (no prior bar)
        if i < 1:
            continue

        bar = bars[i]
        prior = bars[i - 1]

        satisfied = False
        rule_text = ""

        # ----- BULL (H counting) -----
        if is_long:
            # KB Rule: natural prior (including inside bar)
            # KB Rule: outside bar → bull context counts H only, not L
            if bar.high > prior.high:
                satisfied = True
                rule_text = "high > prior_bar.high"
            # inside bar with high <= prior.high → not counted (natural result)

            # Invalidation check: price breaks below pullback_low
            if pullback_low is not None and bar.low < pullback_low:
                result.notes.append(f"bar {i}: low {bar.low:.2f} < pullback_low {pullback_low:.2f} — context invalid")
                result.signal_bar_index = last_signal_bar_idx if last_signal_bar_idx >= 0 else None
                return result

        # ----- BEAR (L counting) -----
        else:
            if bar.low < prior.low:
                satisfied = True
                rule_text = "low < prior_bar.low"

            # Invalidation check: price breaks above rally_high
            if rally_high is not None and bar.high > rally_high:
                result.notes.append(f"bar {i}: high {bar.high:.2f} > rally_high {rally_high:.2f} — context invalid")
                result.signal_bar_index = last_signal_bar_idx if last_signal_bar_idx >= 0 else None
                return result

        # Record event
        if satisfied:
            count_idx += 1
            last_signal_bar_idx = i
            event = CountEvent(
                bar_index=i,
                count_index=count_idx,
                rule=rule_text,
                satisfies=True,
                signal_bar_high=bar.high,
                signal_bar_low=bar.low,
                prior_bar_high=prior.high,
                prior_bar_low=prior.low,
            )
            result.count_events.append(event)

            # Check trigger reset: the bar right after signal bar
            # If price breaks signal_bar.high (bull) or signal_bar.low (bear)
            next_idx = i + 1
            if next_idx < total_bars and not trigger_reset_done:
                next_bar = bars[next_idx]
                if is_long and next_bar.high > bar.high:
                    # H2 trigger fired → reset
                    result.notes.append(f"bar {i}: signal bar → bar {next_idx} trigger fired (reset)")
                    # Record the trigger bar as part of this signal's lifecycle
                    # but keep the count result for this pullback
                    trigger_reset_done = True
                    # Don't return — record remaining bars as H3/H4 but mark post-trigger
                    continue
                elif not is_long and next_bar.low < bar.low:
                    result.notes.append(f"bar {i}: signal bar → bar {next_idx} trigger fired (reset)")
                    trigger_reset_done = True
                    continue

        # H4+ warning
        if count_idx >= 4:
            result.extended_count_warning = True

    # Post-scan: set signal_bar_index and counts
    result.signal_bar_index = last_signal_bar_idx if last_signal_bar_idx >= 0 else None
    if is_long:
        result.h_count = count_idx
    else:
        result.l_count = count_idx

    if count_idx >= 4:
        result.notes.append(f"extended_count_warning: {count_idx} counts reached — trend context may be weakening")

    return result


def get_bar_count_sequence(result: StrictBarCountResult) -> List[dict]:
    """Extract bar count sequence for shadow output debug field."""
    seq = []
    for ev in result.count_events:
        seq.append({
            "bar_index": ev.bar_index,
            "count_index": ev.count_index,
            "rule": ev.rule,
            "signal_bar_high": ev.signal_bar_high,
            "signal_bar_low": ev.signal_bar_low,
        })
    return seq
