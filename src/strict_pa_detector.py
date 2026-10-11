"""
strict_pa_detector.py — Phase 4.1 Strict PA Shadow Detector

Combines context detection (bull pullback / bear rally) with bar counting
to produce complete shadow signal objects. Zero production impact.

Imports allowed (read-only): market_analyzer (MarketStructure), bar_counting_detector,
_sdetect_swings from system_structure_builder, signal_registry.

Forbidden imports: signal_predictor, candidate_pool, rule_guardrail, run_strategy,
system_price_builder, sqlite3.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
import pandas as pd

# Read-only imports — never modify production modules
from bar_counting_detector import (
    build_bar_info_list, count_bars_strict, StrictBarCountResult, get_bar_count_sequence,
)


# ═══════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ContextDetection:
    """Result of pullback/rally context detection"""
    context_type: str                # "bull_pullback" | "bear_rally" | "none"
    context_confidence: str          # "high" | "medium" | "low"
    context_start_index: int         # bar index where pullback/rally starts
    context_start_price: float
    context_start_time: str
    bull_move_high: Optional[float] = None    # for bull_pullback
    pullback_low: Optional[float] = None      # for bull_pullback
    bear_move_low: Optional[float] = None     # for bear_rally
    rally_high: Optional[float] = None        # for bear_rally
    range_position: Optional[str] = None      # "upper_third" | "middle" | "lower_third" | None
    middle_range_signal: bool = False
    invalid_level: Optional[float] = None     # level that invalidates context
    notes: List[str] = field(default_factory=list)


@dataclass
class ShadowSignalResult:
    """Complete shadow signal detection result for one symbol"""
    symbol: str
    timeframe: str = "30m"
    shadow_signal_type: str = ""           # "brooks_h1_strict" etc
    direction: str = ""                    # "long" / "short"
    detected: bool = False
    context_type: str = ""                 # "bull_pullback" / "bear_rally"
    context_confidence: str = ""
    context_details: Dict = field(default_factory=dict)

    # Signal bar
    signal_bar_time: Optional[str] = None
    signal_bar_high: Optional[float] = None
    signal_bar_low: Optional[float] = None
    signal_bar_close: Optional[float] = None
    signal_bar_index: Optional[int] = None
    is_inside_bar_signal: bool = False
    is_outside_bar_signal: bool = False

    # Count
    count_index: int = 0
    count_rule: str = ""
    h1_h2_continuous: bool = False         # H2 is consecutive bar after H1
    bar_count_sequence: List[Dict] = field(default_factory=list)

    # Trigger
    triggered: bool = False
    trigger_bar_time: Optional[str] = None
    trigger_bar_index: Optional[int] = None
    trigger_rule: str = ""
    trigger_delay_bars: Optional[int] = None
    close_confirmation: bool = False

    # Entry/Stop (shadow only)
    shadow_entry: Optional[float] = None
    shadow_stop: Optional[float] = None
    invalid_level: Optional[float] = None
    invalid_reason: Optional[str] = None

    # Signal quality
    signal_quality: str = ""               # "good" | "moderate" | "weak"
    recommended: bool = False

    # Debug & confidence (KB rules: record but don't hard-reject)
    bars_since_signal: Optional[int] = None
    inside_bar_count: int = 0
    outside_bar_seen: bool = False
    # P2: H1-H2 intervening pullback
    has_intervening_pullback_between_h1_h2: bool = False
    intervening_pullback_filter_passed: bool = False

    # Phase 4.3: Qualification
    qualified: bool = False
    qualification_status: str = ""
    blocked_reason: str = ""
    dominant_context: str = ""
    market_direction: str = ""
    market_phase: str = ""
    pullback_depth_atr: float = 0.0
    pullback_significance_passed: bool = False
    close_confirmation_passed: bool = False
    signal_bar_body_pct: float = 0.0
    signal_bar_range_atr: float = 0.0
    is_doji_like: bool = False
    tail_rejection: str = ""

    # Phase 2-3 fields (keep for existing code compatibility)
    range_position: Optional[str] = None
    middle_range_signal: bool = False
    h3_h4_warning: bool = False
    extended_count_warning: bool = False
    trend_context_may_be_weakening: bool = False
    confidence_notes: List[str] = field(default_factory=list)

    # Optional filter tracking
    optional_filter_passed: List[str] = field(default_factory=list)
    optional_filter_failed: List[str] = field(default_factory=list)
    confidence_penalty_reasons: List[str] = field(default_factory=list)
    confidence_bonus_reasons: List[str] = field(default_factory=list)
    manual_review_needed: bool = False

    # Phase 4.5: Actionable layer
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

    # Phase 4.8: KB-aligned actionability fields
    breakout_strength: str = "unknown"
    failed_breakout_risk: bool = False
    boundary_distance_score: int = 0
    signal_bar_strength_score: int = 0
    recent_momentum_score: int = 0
    triggered_bonus: int = 0
    actionability_decision_basis: str = ""

    # Proxy comparison
    proxy_comparison: Dict = field(default_factory=dict)
    debug: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════
# Context Detection
# ═══════════════════════════════════════════════════════════════════

def _get_swing_points(highs, lows, window=5) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """Detect swing highs and lows from K-line arrays."""
    n = len(highs)
    if n < 2 * window + 1:
        return [], []

    sh, sl = [], []
    for i in range(window, n - window):
        is_high = all(highs[i] > highs[j] for j in range(i - window, i + window + 1) if j != i)
        is_low = all(lows[i] < lows[j] for j in range(i - window, i + window + 1) if j != i)
        if is_high:
            sh.append((i, float(highs[i])))
        if is_low:
            sl.append((i, float(lows[i])))
    return sh, sl


def _compute_atr(highs, lows, closes, period=20) -> float:
    """Simple ATR from K-line arrays."""
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


def detect_bull_pullback_context(
    highs, lows, closes, opens, times=None,
    swing_window=5, atr_period=20,
) -> ContextDetection:
    """
    Detect bull pullback context.

    Returns ContextDetection with context_type="bull_pullback" or "none".
    """
    n = len(highs)
    result = ContextDetection(context_type="none", context_confidence="low",
                               context_start_index=-1, context_start_price=0.0,
                               context_start_time="")

    if n < 20:
        result.notes.append("insufficient bars (<20)")
        return result

    atr = _compute_atr(highs, lows, closes, atr_period)
    sh, sl = _get_swing_points(highs, lows, swing_window)

    if not sl or not sh:
        result.notes.append("insufficient swing points")
        return result

    # Find most recent swing high and the prior swing low before it
    recent_sh_idx, recent_sh_price = sh[-1]
    recent_sl_idx, recent_sl_price = sl[-1]

    # bull_move: recent swing low → swing high > 1.5 * ATR
    bull_move_size = recent_sh_price - recent_sl_price
    if bull_move_size < atr * 0.5:
        result.notes.append(f"bull_move too small ({bull_move_size:.2f} < {atr * 0.5:.2f})")
        return result

    # pullback: from recent_sh to current price
    pullback_start_idx = recent_sh_idx
    pullback_start_price = recent_sh_price
    current_idx = n - 1

    if current_idx <= pullback_start_idx:
        result.notes.append("no bars after swing high — not yet in pullback")
        return result

    # pullback_low = min low from pullback_start to current
    pullback_low_price = min(lows[pullback_start_idx:current_idx + 1])

    # Deeper than swing low → bull context broken
    if pullback_low_price < recent_sl_price:
        result.notes.append(f"pullback broke prior swing low ({pullback_low_price:.2f} < {recent_sl_price:.2f}) — bull context invalid")
        return result

    # pullback depth
    pullback_depth = recent_sh_price - pullback_low_price
    pullback_depth_atr = pullback_depth / atr if atr > 0 else 0

    # Trading range detection: check if market is in range
    range_position = _detect_range_position(highs, lows, current_idx, sh, sl)

    # Confidence
    if pullback_depth_atr >= 0.8:
        confidence = "high"
    elif pullback_depth_atr >= 0.3:
        confidence = "medium"
    else:
        confidence = "low"

    # Context valid
    result.context_type = "bull_pullback"
    result.context_confidence = confidence
    result.context_start_index = pullback_start_idx
    result.context_start_price = pullback_start_price
    result.context_start_time = str(times[pullback_start_idx]) if times is not None and pullback_start_idx < len(times) else ""
    result.bull_move_high = recent_sh_price
    result.pullback_low = pullback_low_price
    result.invalid_level = pullback_low_price  # break below → context invalid
    result.range_position = range_position
    if range_position == "middle":
        result.middle_range_signal = True
        result.notes.append(f"signal in range middle — reduced confidence ({range_position})")
    else:
        result.notes.append(f"pullback depth={pullback_depth_atr:.1f} ATR, confidence={confidence}")

    return result


def detect_bear_rally_context(
    highs, lows, closes, opens, times=None,
    swing_window=5, atr_period=20,
) -> ContextDetection:
    """
    Detect bear rally context (symmetric to bull pullback).
    """
    n = len(highs)
    result = ContextDetection(context_type="none", context_confidence="low",
                               context_start_index=-1, context_start_price=0.0,
                               context_start_time="")

    if n < 20:
        result.notes.append("insufficient bars (<20)")
        return result

    atr = _compute_atr(highs, lows, closes, atr_period)
    sh, sl = _get_swing_points(highs, lows, swing_window)

    if not sl or not sh:
        result.notes.append("insufficient swing points")
        return result

    recent_sl_idx, recent_sl_price = sl[-1]
    recent_sh_idx, recent_sh_price = sh[-1]

    # bear_move: swing high → swing low
    # Reorder: find recent SH then the SL after it
    if recent_sh_idx > recent_sl_idx:
        # normal: sh[-1] is more recent, find prior sl
        if len(sl) >= 2:
            prior_sl_idx, prior_sl_price = sl[-2]
        else:
            prior_sl_idx, prior_sl_price = sl[-1]  # fallback
        bear_high_idx, bear_high_price = recent_sh_idx, recent_sh_price
        bear_low_idx, bear_low_price = recent_sl_idx, recent_sl_price
    else:
        # sl is more recent — bear move from sh to sl
        bear_high_idx, bear_high_price = recent_sh_idx, recent_sh_price
        bear_low_idx, bear_low_price = recent_sl_idx, recent_sl_price

    bear_move_size = bear_high_price - bear_low_price
    if bear_move_size < atr * 0.5:
        result.notes.append(f"bear_move too small ({bear_move_size:.2f} < {atr * 0.5:.2f})")
        return result

    # rally: from bear_low to current
    rally_start_idx = bear_low_idx
    rally_start_price = bear_low_price
    current_idx = n - 1

    if current_idx <= rally_start_idx:
        result.notes.append("no bars after swing low — not yet in rally")
        return result

    rally_high_price = max(highs[rally_start_idx:current_idx + 1])

    if rally_high_price > bear_high_price:
        result.notes.append(f"rally broke prior swing high ({rally_high_price:.2f} > {bear_high_price:.2f}) — bear context invalid")
        return result

    rally_depth = rally_high_price - bear_low_price
    rally_depth_atr = rally_depth / atr if atr > 0 else 0

    range_position = _detect_range_position(highs, lows, current_idx, sh, sl)

    if rally_depth_atr >= 0.8:
        confidence = "high"
    elif rally_depth_atr >= 0.3:
        confidence = "medium"
    else:
        confidence = "low"

    result.context_type = "bear_rally"
    result.context_confidence = confidence
    result.context_start_index = rally_start_idx
    result.context_start_price = rally_start_price
    result.context_start_time = str(times[rally_start_idx]) if times is not None and rally_start_idx < len(times) else ""
    result.bear_move_low = bear_low_price
    result.rally_high = rally_high_price
    result.invalid_level = rally_high_price  # break above → context invalid
    result.range_position = range_position
    if range_position == "middle":
        result.middle_range_signal = True
        result.notes.append(f"signal in range middle — reduced confidence ({range_position})")
    else:
        result.notes.append(f"rally depth={rally_depth_atr:.1f} ATR, confidence={confidence}")

    return result


def _detect_range_position(highs, lows, current_idx, sh, sl) -> Optional[str]:
    """Detect position within trading range: upper_third / middle / lower_third / None."""
    if not sh or not sl:
        return None
    range_high = max(p for _, p in sh[-3:]) if len(sh) >= 3 else sh[-1][1]
    range_low = min(p for _, p in sl[-3:]) if len(sl) >= 3 else sl[-1][1]

    if range_high <= range_low:
        return None

    range_width = range_high - range_low
    cp = float(highs[current_idx])
    position_pct = (cp - range_low) / range_width if range_width > 0 else 0.5

    if position_pct >= 0.67:
        return "upper_third"
    elif position_pct <= 0.33:
        return "lower_third"
    else:
        return "middle"


# ═══════════════════════════════════════════════════════════════════════
# Main Detector
# ═══════════════════════════════════════════════════════════════════════

def detect_strict_bar_counting_signals(
    symbol: str,
    kline_df: pd.DataFrame,
    direction: str,           # "long" (scan for H1/H2) or "short" (scan for L1/L2)
    analysis_time: str = "",
    proxy_signals: Optional[List[Dict]] = None,
) -> List[ShadowSignalResult]:
    """
    Main entry: detect strict bar-counting signals for one symbol.
    Returns list of ShadowSignalResult (H1, H2, L1, L2 as applicable).
    """
    results = []

    highs = kline_df['high'].values.astype(float)
    lows = kline_df['low'].values.astype(float)
    closes = kline_df['close'].values.astype(float)
    opens = kline_df['open'].values.astype(float)

    # Extract times if available
    times = None
    if 'date' in kline_df.columns:
        times = kline_df['date'].values
    elif kline_df.index.name == 'date' or 'time' in str(kline_df.index.name).lower():
        times = [str(t) for t in kline_df.index.values]

    # Build bar info list
    bars = build_bar_info_list(highs, lows, closes, opens, times)

    # Detect context
    if direction == "long":
        ctx = detect_bull_pullback_context(highs, lows, closes, opens, times)
    else:
        ctx = detect_bear_rally_context(highs, lows, closes, opens, times)

    if ctx.context_type == "none":
        # Record no-context result for proxy comparison
        for proxy_type in ("H1", "H2") if direction == "long" else ("L1", "L2"):
            results.append(_make_no_context_result(symbol, direction, proxy_type, ctx, proxy_signals))
        return results

    # Execute bar counting
    bull_level = ctx.invalid_level if direction == "long" else None
    bear_level = ctx.invalid_level if direction == "short" else None

    count_result = count_bars_strict(bars, ctx.context_start_index, direction,
                                      pullback_low=bull_level, rally_high=bear_level)

    # Build shadow results for each count level applicable
    if direction == "long":
        count_targets = [("brooks_h1_strict", "H1", 1), ("brooks_h2_strict", "H2", 2)]
    else:
        count_targets = [("brooks_l1_strict", "L1", 1), ("brooks_l2_strict", "L2", 2)]

    for strict_type, proxy_type, target_count in count_targets:
        sr = _build_shadow_result(
            symbol=symbol,
            direction=direction,
            strict_signal_type=strict_type,
            proxy_signal_type=proxy_type,
            target_count=target_count,
            ctx=ctx,
            count_result=count_result,
            bars=bars,
            proxy_signals=proxy_signals,
            analysis_time=analysis_time,
        )
        results.append(sr)

    return results


def _make_no_context_result(symbol, direction, proxy_type, ctx, proxy_signals) -> ShadowSignalResult:
    """Build result when no context detected."""
    sr = ShadowSignalResult(symbol=symbol)
    sr.shadow_signal_type = f"brooks_h{1 if proxy_type=='H1' else 2}_strict" if direction == "long" else f"brooks_l{1 if proxy_type=='L1' else 2}_strict"
    sr.direction = direction
    sr.detected = False
    sr.confidence_notes = ctx.notes
    sr.proxy_comparison = _compare_with_proxy(symbol, proxy_type, direction, sr, proxy_signals)
    return sr


def _build_shadow_result(
    symbol, direction, strict_signal_type, proxy_signal_type,
    target_count, ctx, count_result, bars, proxy_signals, analysis_time,
) -> ShadowSignalResult:
    """Build a single ShadowSignalResult from context + count."""
    sr = ShadowSignalResult(symbol=symbol)
    sr.shadow_signal_type = strict_signal_type
    sr.direction = direction
    sr.context_type = ctx.context_type
    sr.context_confidence = ctx.context_confidence
    sr.range_position = ctx.range_position
    sr.middle_range_signal = ctx.middle_range_signal
    sr.inside_bar_count = count_result.inside_bar_count
    sr.outside_bar_seen = count_result.outside_bar_seen

    # Context details
    sr.context_details = {
        "context_type": ctx.context_type,
        "context_confidence": ctx.context_confidence,
        "context_start_time": ctx.context_start_time,
        "context_start_price": ctx.context_start_price,
        "range_position": ctx.range_position,
        "invalid_level": ctx.invalid_level,
    }
    if direction == "long":
        sr.context_details["bull_move_high"] = ctx.bull_move_high
        sr.context_details["pullback_low"] = ctx.pullback_low
        sr.invalid_level = ctx.pullback_low
    else:
        sr.context_details["bear_move_low"] = ctx.bear_move_low
        sr.context_details["rally_high"] = ctx.rally_high
        sr.invalid_level = ctx.rally_high

    # Find the count event matching target_count
    target_event = None
    for ev in count_result.count_events:
        if ev.count_index == target_count:
            target_event = ev
            break

    if target_event is None:
        # Target count not reached
        max_count = count_result.h_count if direction == "long" else count_result.l_count
        sr.detected = False
        sr.count_index = max_count
        sr.count_rule = "high > prior_bar.high" if direction == "long" else "low < prior_bar.low"
        sr.confidence_notes.append(f"max count reached: {max_count}, target={target_count}")
        sr.proxy_comparison = _compare_with_proxy(symbol, proxy_signal_type, direction, sr, proxy_signals)
        return sr

    # Target count reached — populate signal
    sr.detected = True
    sr.count_index = target_count
    sr.count_rule = target_event.rule

    signal_bar = bars[target_event.bar_index]
    sr.signal_bar_time = signal_bar.time
    sr.signal_bar_high = target_event.signal_bar_high
    sr.signal_bar_low = target_event.signal_bar_low
    sr.signal_bar_close = signal_bar.close
    sr.signal_bar_index = target_event.bar_index
    sr.is_inside_bar_signal = signal_bar.is_inside_bar
    sr.is_outside_bar_signal = signal_bar.is_outside_bar

    # Check if H1/H2 continuous (consecutive bars)
    sr.h1_h2_continuous = _check_continuous(count_result, target_count)

    # Bar count sequence
    sr.bar_count_sequence = get_bar_count_sequence(count_result)

    # Extended count warning
    max_count = count_result.h_count if direction == "long" else count_result.l_count
    sr.extended_count_warning = count_result.extended_count_warning
    sr.h3_h4_warning = (max_count >= 3 and target_count <= 2)
    sr.trend_context_may_be_weakening = (max_count >= 4)

    # Trigger detection
    _detect_trigger(sr, bars, target_event.bar_index, direction)

    # Compute shadow entry/stop
    if sr.triggered:
        if direction == "long":
            sr.shadow_entry = target_event.signal_bar_high + 0.01
            sr.shadow_stop = target_event.signal_bar_low - 0.01
        else:
            sr.shadow_entry = target_event.signal_bar_low - 0.01
            sr.shadow_stop = target_event.signal_bar_high + 0.01
    else:
        # Shadow stop always computed
        if direction == "long":
            sr.shadow_stop = target_event.signal_bar_low - 0.01
        else:
            sr.shadow_stop = target_event.signal_bar_high + 0.01

    # Bars since signal
    total_bars = len(bars)
    sr.bars_since_signal = total_bars - 1 - target_event.bar_index if target_event.bar_index < total_bars else None

    # Signal quality
    sr.signal_quality = _assess_quality(sr, ctx, target_count, max_count)

    # Recommended
    sr.recommended = (target_count <= 2 and not ctx.middle_range_signal and max_count < 4)

    # Confidence notes
    sr.confidence_notes = list(ctx.notes) + list(count_result.notes)
    if sr.extended_count_warning:
        sr.confidence_notes.append(f"H={count_result.h_count} L={count_result.l_count} — extended count warning")
    if sr.middle_range_signal:
        sr.confidence_notes.append("trading range middle signal — reduced confidence")

    # Proxy comparison
    sr.proxy_comparison = _compare_with_proxy(symbol, proxy_signal_type, direction, sr, proxy_signals)

    # Debug
    sr.debug = {
        "bar_count_sequence": [e.bar_index for e in count_result.count_events],
        "inside_bar_handling": f"{count_result.inside_bar_count} inside bars, natural prior",
        "outside_bar_handling": "context-directed single count" if count_result.outside_bar_seen else "none",
        "context_notes": list(ctx.notes),
        "total_bars_in_window": len(bars),
    }

    return sr


def _check_continuous(count_result, target_count) -> bool:
    """Check if H1 and H2 are consecutive bars (continuous)."""
    if target_count < 2:
        return False
    events = count_result.count_events
    for i in range(len(events) - 1):
        if events[i].count_index == target_count - 1 and events[i + 1].count_index == target_count:
            return (events[i + 1].bar_index == events[i].bar_index + 1)
    return False


def _detect_trigger(sr: ShadowSignalResult, bars, signal_bar_index, direction):
    """Detect if trigger bar exists after signal bar. No hard expiry window."""
    total_bars = len(bars)
    for t_idx in range(signal_bar_index + 1, min(signal_bar_index + 21, total_bars)):
        bar = bars[t_idx]
        if direction == "long":
            if bar.high > bars[signal_bar_index].high:
                sr.triggered = True
                sr.trigger_bar_time = bar.time
                sr.trigger_bar_index = t_idx
                sr.trigger_rule = "break above signal_bar.high"
                sr.trigger_delay_bars = t_idx - signal_bar_index
                if bar.close > bars[signal_bar_index].high:
                    sr.close_confirmation = True
                return
        else:
            if bar.low < bars[signal_bar_index].low:
                sr.triggered = True
                sr.trigger_bar_time = bar.time
                sr.trigger_bar_index = t_idx
                sr.trigger_rule = "break below signal_bar.low"
                sr.trigger_delay_bars = t_idx - signal_bar_index
                if bar.close < bars[signal_bar_index].low:
                    sr.close_confirmation = True
                return

    # Not triggered
    sr.triggered = False
    sr.trigger_delay_bars = None
    sr.trigger_rule = "break above signal_bar.high" if direction == "long" else "break below signal_bar.low"


def _assess_quality(sr: ShadowSignalResult, ctx, target_count, max_count) -> str:
    """Assess signal quality: good / moderate / weak."""
    score = 0
    if ctx.context_confidence == "high":
        score += 3
    elif ctx.context_confidence == "medium":
        score += 2
    else:
        score += 1

    if target_count == 1:
        score += 1  # H1/L1 lower quality than H2/L2
    elif target_count == 2:
        score += 2

    if sr.middle_range_signal:
        score -= 2
    elif sr.range_position in ("upper_third", "lower_third"):
        score += 1

    if max_count >= 4:
        score -= 2
    elif max_count >= 3:
        score -= 1

    if sr.triggered:
        score += 1
    if sr.close_confirmation:
        score += 1

    if score >= 6:
        return "good"
    elif score >= 4:
        return "moderate"
    else:
        return "weak"


def _compare_with_proxy(symbol, proxy_signal_type, direction, sr, proxy_signals) -> Dict:
    """Compare strict signal with current proxy signal. Returns comparison dict."""
    comparison = {
        "current_proxy_signal_type": proxy_signal_type,
        "proxy_detected": False,
        "proxy_display_label": f"{proxy_signal_type}代理（{'higher-low' if direction == 'long' else 'lower-high'} proxy）",
        "strict_matches_proxy": False,
        "difference_reason": "",
    }

    if not proxy_signals:
        if not sr.detected:
            comparison["difference_reason"] = "strict 未检测到信号 (no context / count not reached)"
        else:
            comparison["difference_reason"] = "无 proxy 数据可供对比"
        return comparison

    # Find proxy signal matching type and direction
    proxy_found = None
    for ps in proxy_signals:
        ps_type = str(ps.get("signal_type", ps.get("type", "")))
        ps_dir = str(ps.get("direction", "")).lower()
        ps_dir = "long" if ps_dir in ("long", "buy", "bull") else "short" if ps_dir in ("short", "sell", "bear") else ""
        if ps_type.upper() == proxy_signal_type.upper() and ps_dir == direction:
            proxy_found = ps
            break

    if proxy_found:
        comparison["proxy_detected"] = True
        if sr.detected:
            comparison["strict_matches_proxy"] = True
            comparison["difference_reason"] = ""
        else:
            comparison["strict_matches_proxy"] = False
            comparison["difference_reason"] = f"proxy 检测到 {proxy_signal_type}，但 strict bar-counting 未确认（count={sr.count_index}, target 未达）"
    else:
        comparison["proxy_detected"] = False
        if sr.detected:
            comparison["strict_matches_proxy"] = False
            comparison["difference_reason"] = f"strict bar-counting 检测到信号，但 proxy 未检测到 {proxy_signal_type}"
        else:
            comparison["strict_matches_proxy"] = False
            comparison["difference_reason"] = "both proxy and strict: no signal"

    return comparison


def get_proxy_vs_strict_matrix(results: List[ShadowSignalResult]) -> List[Dict]:
    """Build the 4-quadrant comparison matrix from shadow results."""
    matrix = []
    for sr in results:
        pc = sr.proxy_comparison
        if sr.detected and pc.get("proxy_detected"):
            match_type = "A"
        elif not sr.detected and pc.get("proxy_detected"):
            match_type = "B"
        elif sr.detected and not pc.get("proxy_detected"):
            match_type = "C"
        else:
            match_type = "D"

        matrix.append({
            "symbol": sr.symbol,
            "analyzed_at": "",
            "proxy_signal": pc.get("current_proxy_signal_type", ""),
            "strict_signal": sr.shadow_signal_type,
            "match_type": match_type,
            "direction": sr.direction,
            "proxy_detected": pc.get("proxy_detected", False),
            "strict_detected": sr.detected,
            "strict_count_index": sr.count_index,
            "proxy_structure": "",
            "strict_trigger": sr.triggered,
            "strict_entry": sr.shadow_entry,
            "strict_stop": sr.shadow_stop,
            "difference_reason": pc.get("difference_reason", ""),
            "manual_review_needed": (match_type in ("B", "C")),
        })
    return matrix


# ═══════════════════════════════════════════════════════════════════════
# Phase 4.3: Qualification Integration
# ═══════════════════════════════════════════════════════════════════════

def qualify_shadow_signals(
    results: List[ShadowSignalResult],
    market_direction: str,
    market_phase: str,
    highs,
    lows,
    closes,
    opens,
    count_results: Dict = None,   # {signal_type: StrictBarCountResult}
    atr: float = 0.0,
    config: Dict = None,
) -> List[ShadowSignalResult]:
    """
    Apply qualification to a list of shadow signals.

    Each signal gets qualified=True/False based on context arbitration,
    pullback significance, range position, etc.

    Args:
        results: list of ShadowSignalResult from detect_strict_bar_counting_signals
        market_direction: "up" | "down" | "neutral"
        market_phase: "trend" | "range" | "transition"
        highs, lows, closes, opens: raw K-line arrays
        count_results: optional dict of StrictBarCountResult by signal_type
        atr: ATR(20) value
        config: qualification config dict
    """
    from strict_pa_qualification import qualify_signal, DEFAULT_QUALIFICATION_CONFIG

    if config is None:
        config = DEFAULT_QUALIFICATION_CONFIG

    for sr in results:
        if not sr.detected:
            sr.qualified = False
            sr.qualification_status = "not_detected"
            sr.manual_review_needed = False
            continue

        # Compute pullback depth for this signal
        pd_atr = 0.0
        pd_pct = 0.0
        if sr.context_type == "bull_pullback":
            ctx = sr.context_details
            bull_high = ctx.get("bull_move_high", 0)
            pullback_low = ctx.get("pullback_low", 0)
            if bull_high > 0 and pullback_low > 0:
                pd_atr = (bull_high - pullback_low) / max(atr, 0.001) if atr > 0 else 0
                pd_pct = (bull_high - pullback_low) / max(bull_high, 0.001) * 100
        elif sr.context_type == "bear_rally":
            ctx = sr.context_details
            bear_low = ctx.get("bear_move_low", 0)
            rally_high = ctx.get("rally_high", 0)
            if rally_high > 0 and bear_low > 0:
                pd_atr = (rally_high - bear_low) / max(atr, 0.001) if atr > 0 else 0
                pd_pct = (rally_high - bear_low) / max(rally_high, 0.001) * 100

        # Get count result for H1-H2 check
        cr = None
        if count_results and sr.shadow_signal_type in count_results:
            cr = count_results[sr.shadow_signal_type]

        # Apply qualification
        qr = qualify_signal(
            sr=sr,
            market_direction=market_direction,
            market_phase=market_phase,
            highs=highs,
            lows=lows,
            closes=closes,
            opens=opens,
            pullback_depth_atr=pd_atr,
            pullback_depth_pct=pd_pct,
            count_result=cr,
            atr=atr,
            config=config,
        )

        # Map qualification to ShadowSignalResult
        sr.qualified = qr.qualified
        sr.qualification_status = qr.qualification_status
        sr.blocked_reason = qr.blocked_reason
        sr.dominant_context = qr.dominant_context
        sr.market_direction = qr.market_direction
        sr.market_phase = qr.market_phase
        sr.pullback_depth_atr = qr.pullback_depth_atr
        sr.pullback_significance_passed = qr.pullback_significance_passed
        sr.close_confirmation_passed = qr.close_confirmation_passed
        sr.signal_bar_body_pct = qr.signal_bar_body_pct
        sr.signal_bar_range_atr = qr.signal_bar_range_atr
        sr.is_doji_like = qr.is_doji_like
        sr.tail_rejection = qr.tail_rejection
        sr.has_intervening_pullback_between_h1_h2 = qr.has_intervening_pullback_between_h1_h2
        sr.intervening_pullback_filter_passed = qr.intervening_pullback_filter_passed
        sr.confidence_penalty_reasons = qr.confidence_penalty_reasons
        sr.confidence_bonus_reasons = qr.confidence_bonus_reasons
        sr.manual_review_needed = qr.manual_review_needed or (
            sr.shadow_signal_type in ("brooks_h3_strict", "brooks_h4_strict"))

    return results
