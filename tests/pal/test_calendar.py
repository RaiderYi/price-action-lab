"""S2-03 测试：交易日历与 30m 对齐（任务书 §7 因果场景）。"""
import os
import sys
from datetime import date, datetime, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.calendar import TZ, calendar_from_sessions


@pytest.fixture
def cal():
    # 2026-10-12(一)~10-16(五)，跳过周末
    return calendar_from_sessions(
        [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14),
         date(2026, 10, 15), date(2026, 10, 16)], version="test-v1")


class TestCalendar:
    def test_weekend_not_trading(self, cal):
        assert not cal.is_trading_day(date(2026, 10, 17))
        assert not cal.is_trading_day(date(2026, 10, 18))

    def test_next_trading_day(self, cal):
        assert cal.next_trading_day(date(2026, 10, 15)) == date(2026, 10, 16)

    def test_out_of_range_raises(self, cal):
        with pytest.raises(KeyError):
            cal.next_trading_day(date(2026, 10, 16))

    def test_unsorted_rejected(self):
        from pal.data.calendar import TradingCalendar
        with pytest.raises(Exception):
            TradingCalendar((date(2026, 10, 14), date(2026, 10, 12)), version="v")

    def test_from_sessions_normalizes(self):
        cal = calendar_from_sessions(
            [date(2026, 10, 14), date(2026, 10, 12)], version="v")
        assert cal.trading_days == (date(2026, 10, 12), date(2026, 10, 14))

    def test_eight_bars_per_day(self, cal):
        bars = cal.bars_for_day(date(2026, 10, 13))
        assert len(bars) == 8

    def test_lunch_break_not_in_grid(self, cal):
        bars = cal.bars_for_day(date(2026, 10, 13))
        starts = {b[0].time() for b in bars}
        assert time(11, 30) not in starts   # 午休起点不开新bar
        assert time(12, 30) not in starts
        assert time(13, 0) in starts        # 下午第一根
        # 无 bar 跨午休
        for s, e in bars:
            assert s.date() == e.date()
            assert e > s

    def test_last_bar_ends_at_1500(self, cal):
        bars = cal.bars_for_day(date(2026, 10, 13))
        assert bars[-1][1].time() == time(15, 0)

    def test_expected_slots(self, cal):
        assert cal.expected_bar_slots_between(date(2026, 10, 12), date(2026, 10, 16)) == 8 * 5

    def test_daily_close_available_at(self, cal):
        at = cal.daily_close_available_at(date(2026, 10, 13))
        assert at == datetime(2026, 10, 13, 15, 0, tzinfo=TZ)

    def test_non_trading_close_raises(self, cal):
        with pytest.raises(KeyError):
            cal.daily_close_available_at(date(2026, 10, 17))
