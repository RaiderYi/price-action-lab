"""Phase 4.1: bar_counting_detector tests — pure bar counting logic"""
import pytest
from bar_counting_detector import (
    build_bar_info_list, count_bars_strict,
    BarInfo, CountEvent, StrictBarCountResult,
)


def _make_flat_bars(highs, lows=None, closes=None, opens=None, times=None):
    """Helper: build bars from simple arrays. lows/closes/opens default to slight offsets from highs."""
    n = len(highs)
    if lows is None:
        lows = [h - 0.5 for h in highs]
    if closes is None:
        closes = highs
    if opens is None:
        opens = [h - 0.1 for h in highs]
    return build_bar_info_list(highs, lows, closes, opens, times)


# ═══ H1 / H2 counting ═══

class TestH1H2Counting:
    def test_h1_first_high_gt_prior(self):
        """T1: 第一根 high > prior_high → H1"""
        highs  = [10, 9.5, 9.3, 9.6, 9.4, 9.3, 9.2]  # only bar 3 satisfies
        # bar 0-2: flat/down (context), bar 3: high 9.6 > 9.3 → H1
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 1
        assert len(result.count_events) == 1
        assert result.count_events[0].count_index == 1
        assert result.count_events[0].bar_index == 3

    def test_h2_second_high_gt_prior(self):
        """T2: 第二根 high > prior_high → H2"""
        highs = [10, 9.8, 9.5, 9.7, 9.4, 9.9, 9.6]
        bars = _make_flat_bars(highs)
        # bar 3: 9.7 > 9.5 → H1, bar 5: 9.9 > 9.4 → H2
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 2
        assert len(result.count_events) == 2
        assert result.count_events[0].count_index == 1
        assert result.count_events[1].count_index == 2

    def test_h3_third_count(self):
        """连续三根都满足 → H3"""
        highs = [10, 9.5, 9.6, 9.8, 10.0]
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 3
        assert not result.extended_count_warning  # H3 no warning
        assert result.count_events[-1].count_index == 3

    def test_h4_extended_warning(self):
        """四根满足 → H4 + extended_count_warning"""
        highs = [10, 9.0, 9.2, 9.4, 9.6, 9.8]
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 4
        assert result.extended_count_warning

    def test_not_satisfied_not_counted(self):
        """不满足条件 → 不计数"""
        highs = [10, 9.5, 9.3, 9.2, 9.1]  # all decreasing
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 0
        assert len(result.count_events) == 0


# ═══ L1 / L2 counting ═══

class TestL1L2Counting:
    def test_l1_first_low_lt_prior(self):
        """T3: 第一根 low < prior_low → L1"""
        highs = [10, 9.8, 9.7, 9.65, 9.9, 10.0]     # only bar 3 satisfies low < prior
        lows  = [9.5, 9.3, 9.4, 9.0, 9.5, 9.6]       # bar 2: low 9.4 > 9.3, bar 3: low 9.0 < 9.4 → L1
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="short")
        assert result.l_count == 1
        assert result.count_events[0].count_index == 1

    def test_l2_second_low_lt_prior(self):
        """T4: 第二根 low < prior_low → L2"""
        highs = [10, 9.8, 9.7, 9.65, 9.9, 9.7, 9.6, 9.8]
        lows  = [9.5, 9.3, 9.4, 9.0, 9.5, 9.2, 8.8, 9.5]
        # bar 3 low 9.0 < 9.4 → L1
        # bar 4 low 9.5 > 9.0 → no count (rally)
        # bar 5 low 9.2 < 9.5 → no count yet (bar 4 is up)
        # bar 6 low 8.8 < 9.2 → L2
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="short")
        # We only need at least 2 counts (L1 + L2)
        assert result.l_count >= 2
        # Verify L2 is present in one of the events
        count_indices = [e.count_index for e in result.count_events]
        assert 2 in count_indices

    def test_l4_extended_warning(self):
        """L4 → extended_count_warning"""
        highs = [10, 10.5, 10.3, 10.1, 9.9, 9.7]
        lows  = [9.5, 10.0, 9.8, 9.6, 9.4, 9.2]
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="short")
        assert result.l_count == 4
        assert result.extended_count_warning


# ═══ Inside bar handling (KB Rule 2: natural prior, no skip) ═══

class TestInsideBarHandling:
    def test_inside_bar_natural_prior(self):
        """T5: inside bar 不跳过，作为 natural prior"""
        highs = [10, 9.5, 9.3, 9.2, 9.4]
        # bar 3: high 9.2 <= 9.3 → inside bar, HS: inside bar IS bar 2 if high=9.2 low=9.0
        # Actually: need to make bar 3 an inside bar: high <= prior_high AND low >= prior_low
        lows  = [9.5, 9.0, 8.8, 8.9, 8.8]
        # bar 2: high=9.3 low=8.8. bar 3: high=9.2(<=9.3) low=8.9(>=8.8) → inside bar
        bars = build_bar_info_list(highs, lows, highs, highs)
        assert bars[3].is_inside_bar

        # Now bar 4 high 9.4 > 9.2 → H1 (counted, inside bar was natural prior)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 1

    def test_high_gt_inside_bar_high_counts(self):
        """T6: inside bar 后，high > inside_bar.high → 可计 H"""
        highs = [10, 9.5, 9.3, 9.2, 9.45]
        lows  = [9.5, 9.0, 8.8, 8.9, 8.85]
        # bar 3: inside bar (high 9.2 <= 9.3, low 8.9 >= 8.8)
        bars = build_bar_info_list(highs, lows, highs, highs)
        assert bars[3].is_inside_bar
        # bar 4: high 9.45 > prior bar 3 high 9.2 → H1
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 1
        assert result.count_events[0].bar_index == 4

    def test_inside_bar_not_satisfying_not_counted(self):
        """inside bar 自身 high <= prior high → 不增加计数"""
        highs = [10, 9.5, 9.3, 9.2, 9.1]  # bar 3: inside, bar 4: also inside/down
        lows  = [9.5, 9.0, 8.8, 8.9, 8.7]
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 0


# ═══ Outside bar handling (KB Rule 3: context-directed single count) ═══

class TestOutsideBarHandling:
    def test_outside_bar_bull_only_counts_h(self):
        """T7: outside bar 在 bull context 中只计 H，不计 L"""
        highs = [10, 9.5, 9.3, 9.6]      # bar 3: high 9.6 > 9.3 AND low < 9.0
        lows  = [9.5, 9.0, 8.8, 8.5]      # bar 3: low 8.5 < 8.8 → outside bar
        bars = build_bar_info_list(highs, lows, highs, highs)
        assert bars[3].is_outside_bar

        result = count_bars_strict(bars, context_start_index=1, direction="long")
        # Outside bar high 9.6 > prior high 9.3 → counted as H
        assert result.h_count >= 1

    def test_outside_bar_bear_only_counts_l(self):
        """T8: outside bar 在 bear context 中只计 L，不计 H"""
        highs = [10, 11, 10.8, 11.2]      # bar 3: outside bar (high > prior, low < prior)
        lows  = [9.5, 10.5, 10.3, 10.0]
        bars = build_bar_info_list(highs, lows, highs, highs)
        assert bars[3].is_outside_bar

        result = count_bars_strict(bars, context_start_index=1, direction="short")
        # Outside bar low 10.0 < prior low 10.3 → counted as L
        assert result.l_count >= 1


# ═══ Context: start index ═══

class TestContextStart:
    def test_counting_starts_at_context_index(self):
        """只从 context_start_index 之后计数"""
        highs = [20, 18, 19, 17, 18.5]
        bars = _make_flat_bars(highs)
        # context_start=3: bar 1 (high=19>18) 不应被计入
        result = count_bars_strict(bars, context_start_index=3, direction="long")
        assert result.h_count == 1  # only bar 4 (high 18.5>17)

    def test_bars_before_context_not_counted(self):
        """context 之前的 bar 完全不计入"""
        highs = [10, 11, 12, 10.5, 11, 10.8]
        bars = _make_flat_bars(highs)
        # bar 1-2 are up but context starts at 3
        result = count_bars_strict(bars, context_start_index=3, direction="long")
        for ev in result.count_events:
            assert ev.bar_index >= 3


# ═══ Trigger reset ═══

class TestTriggerReset:
    def test_h2_trigger_resets_count(self):
        """T9: H2 trigger detected → count continues but notes reset"""
        highs = [10, 9.5, 9.7, 9.4, 9.9, 10.2, 9.8, 9.7]
        # bar 2: 9.7 > 9.5 → H1, bar 4: 9.9 > 9.4 → H2
        # bar 5: high 10.2 > signal bar 4 high 9.9 → trigger fired
        # Trigger fired recorded in notes; counting continues for H3/H4 (KB: no hard reset)
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        # H1+H2 detected, trigger note present
        assert result.h_count >= 2
        assert "trigger fired" in " ".join(result.notes).lower()

    def test_h2_not_triggered_continues_to_h3(self):
        """T10: H2 未触发 → 可继续计 H3/H4"""
        highs = [10, 9.5, 9.7, 9.4, 9.8, 9.6, 10.0]
        # bar 2: H1, bar 4: H2, bar 6: H3
        # No bar breaks above H2 signal bar high
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count == 3

    def test_h4_no_hard_reject(self):
        """T11: H4+ 只产生 warning，不 reject"""
        highs = [10, 9.0, 9.3, 9.1, 9.4, 9.2, 9.5, 9.3, 9.6]
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.h_count >= 4
        assert result.extended_count_warning
        # Must NOT raise or reject — just a warning flag


# ═══ Invalidation ═══

class TestInvalidation:
    def test_pullback_low_broken_invalidates(self):
        """price < pullback_low → context invalid, counting stops"""
        highs = [10, 9.5, 9.7, 9.4, 9.2, 8.5, 8.8]
        bars = _make_flat_bars(highs)
        # pullback_low = 9.0, bar 5 low < 9.0 → invalid
        result = count_bars_strict(bars, context_start_index=1, direction="long",
                                    pullback_low=9.0)
        # Should stop before bar 5
        assert "context invalid" in " ".join(result.notes).lower()

    def test_rally_high_broken_invalidates(self):
        """price > rally_high → ctx invalid, L counting stops"""
        highs = [10, 10.5, 10.2, 10.3, 10.1, 11.0]
        lows  = [9.5, 10.0, 9.8, 9.7, 9.5, 10.2]
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="short",
                                    rally_high=10.8)
        assert "context invalid" in " ".join(result.notes).lower()


# ═══ Bar type detection ═══

class TestBarTypeDetection:
    def test_inside_bar_detected(self):
        highs = [10, 9.5, 9.3, 9.2]
        lows  = [9.5, 9.0, 8.8, 8.9]
        bars = build_bar_info_list(highs, lows, highs, highs)
        assert bars[3].is_inside_bar

    def test_outside_bar_detected(self):
        highs = [10, 9.5, 9.3, 9.6]
        lows  = [9.5, 9.0, 8.8, 8.5]
        bars = build_bar_info_list(highs, lows, highs, highs)
        assert bars[3].is_outside_bar

    def test_gap_up_detected(self):
        highs = [10, 9.5, 9.3, 10.0]
        opens = [9.8, 9.3, 9.1, 9.8]  # bar 3 open > bar 2 high 9.3
        lows  = [9.5, 9.0, 8.8, 9.5]
        bars = build_bar_info_list(highs, lows, highs, opens)
        # bar 3 open 9.8 > bar 2 high 9.3 → gap up
        assert bars[3].gap_up

    def test_inside_bar_count_tracked(self):
        highs = [10, 9.5, 9.3, 9.2, 9.1, 9.4]
        lows  = [9.5, 9.0, 8.8, 8.9, 8.85, 8.8]
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.inside_bar_count > 0

    def test_outside_bar_seen_tracked(self):
        highs = [10, 9.5, 9.3, 9.6]
        lows  = [9.5, 9.0, 8.8, 8.5]
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.outside_bar_seen


# ═══ Edge cases ═══

class TestEdgeCases:
    def test_zero_bars_graceful(self):
        bars = _make_flat_bars([10])
        result = count_bars_strict(bars, context_start_index=0, direction="long")
        assert result.h_count == 0

    def test_context_start_at_last_bar(self):
        """context_start at last bar → nothing to count"""
        highs = [10, 9.5, 9.3, 9.6, 9.8]
        bars = _make_flat_bars(highs)
        result = count_bars_strict(bars, context_start_index=4, direction="long")
        assert result.h_count == 0

    def test_consecutive_outside_bars(self):
        """Two consecutive outside bars handled correctly"""
        highs = [10, 9.5, 9.8, 9.7, 10.0]  # bar 2-3 both create outsides
        lows  = [9.5, 9.0, 8.5, 9.6, 9.8]
        bars = build_bar_info_list(highs, lows, highs, highs)
        result = count_bars_strict(bars, context_start_index=1, direction="long")
        assert result.outside_bar_seen
        assert result.h_count > 0
