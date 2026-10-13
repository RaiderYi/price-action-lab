"""第三轮复审 T06：行情与交易日历完整性强制。

复审 F07 复现 + 验收：
- 重复棒不能伪造 final 日线（8 根重复早盘棒 → partial）；
- 日历路径：槽位集合必须精确等于网格——缺尾棒/多槽/非交易日 → partial；
- 错周期输入 → 拒绝（不静默聚合）；
- 节假日/周末可卖日：周五买入 → 下周一可卖（T+1 用真交易日历）。
"""
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar, resample_30m_to_daily
from pal.data.calendar import TZ, TradingCalendar, calendar_from_sessions

IID = "SSE.600519"

# 覆盖 2026-10-09(五) 10-12(一) 10-13(二)：10-10/10-11 周末
CAL = TradingCalendar(
    (date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 13)),
    "test-cal-v1")


def grid_bars(d: date, fill_slots=None, price=10.0):
    """按日历网格生成某交易日的 30m bar。fill_slots=None 全部，否则子集。"""
    out = []
    slots = CAL.bars_for_day(d)
    for i, (s, e) in enumerate(slots):
        if fill_slots is not None and i not in fill_slots:
            continue
        px = price + i * 0.05
        out.append(Bar(IID, "30m", s, e, e, px, px + 0.1, px - 0.1,
                       px + 0.02, 100_000))
    return out


class TestCalendarGridDaily:
    def test_full_grid_final_and_available_at_1500(self):
        bars = grid_bars(date(2026, 10, 12))
        daily = resample_30m_to_daily(bars, IID, calendar=CAL)
        assert len(daily) == 1
        assert daily[0].is_final
        # T06: available_at = 15:00 收盘口径
        assert daily[0].available_at == datetime(2026, 10, 12, 15, 0, tzinfo=TZ)

    def test_missing_tail_bar_not_final(self):
        """缺尾棒（14:30-15:00 槽位缺失）→ partial。"""
        bars = grid_bars(date(2026, 10, 12), fill_slots=set(range(7)))
        daily = resample_30m_to_daily(bars, IID, calendar=CAL)
        assert len(daily) == 1
        assert not daily[0].is_final

    def test_non_trading_day_not_final(self):
        """周六数据（供应商错发）→ 该日不构成 final。"""
        sat = date(2026, 10, 10)
        bars = [Bar(IID, "30m",
                    datetime.combine(sat, time(9, 30), tzinfo=TZ),
                    datetime.combine(sat, time(10, 0), tzinfo=TZ),
                    datetime.combine(sat, time(10, 0), tzinfo=TZ),
                    10.0, 10.1, 9.9, 10.0, 100_000) for _ in range(8)]
        daily = resample_30m_to_daily(bars, IID, calendar=CAL)
        assert len(daily) == 1
        assert not daily[0].is_final

    def test_duplicate_bars_not_final(self):
        """F07 复现：同一根早盘棒重复 8 次 → partial（不伪造 final）。"""
        d = date(2026, 10, 12)
        bars = grid_bars(d) + grid_bars(d)     # 全部重复
        daily = resample_30m_to_daily(bars, IID, calendar=CAL)
        assert not daily[0].is_final

    def test_wrong_timeframe_rejected(self):
        """错周期输入（1d bar 混入）→ 显式拒绝，不静默聚合。"""
        d = date(2026, 10, 12)
        bars = grid_bars(d)
        s = datetime.combine(d, time(9, 30), tzinfo=TZ)
        e = datetime.combine(d, time(15, 0), tzinfo=TZ)
        bars.append(Bar(IID, "1d", s, e, e, 10.0, 11.0, 9.0, 10.5, 800_000))
        with pytest.raises(Exception, match="错周期"):
            resample_30m_to_daily(bars, IID, calendar=CAL)

    def test_afternoon_slots_required(self):
        """只有上午 4 槽（跨午休缺下午）→ partial。"""
        bars = grid_bars(date(2026, 10, 12), fill_slots={0, 1, 2, 3})
        daily = resample_30m_to_daily(bars, IID, calendar=CAL)
        assert not daily[0].is_final

    def test_calendar_t1_friday_to_monday(self):
        """周五买入 → 下周一可卖（自然日+1 会错给周六）。"""
        assert CAL.next_trading_day(date(2026, 10, 9)) == date(2026, 10, 12)
        # 自然日近似会给出 10-10（周六，非交易日）——这正是 T06 要消灭的
        assert date(2026, 10, 9) + timedelta(days=1) == date(2026, 10, 10)
        assert not CAL.is_trading_day(date(2026, 10, 10))


class TestOrchestratorCalendarT1:
    def test_friday_buy_sellable_monday_not_saturday(self):
        """周五 30m 棒触发买入 → sellable_from=下周一（日历口径）。"""
        from pal.pipeline.orchestrator import (
            ArmedSetup,
            OrchestratorConfig,
            SessionOrchestrator,
        )
        from pal.ledger.positions import AccountLedger
        from pal.signals.engine import EngineConfig

        cfg = OrchestratorConfig(EngineConfig("t06"), calendar=CAL)
        orch = SessionOrchestrator(cfg, AccountLedger(1_000_000))
        d = date(2026, 10, 9)     # 周五
        s = datetime.combine(d, time(10, 0), tzinfo=TZ)
        e = datetime.combine(d, time(10, 30), tzinfo=TZ)
        bar = Bar(IID, "30m", s, e, e, 9.5, 10.6, 9.4, 10.2, 1_000_000)
        orch.armed["s1"] = ArmedSetup("s1", IID, "breakout",
                                      entry=10.0, stop=9.0, target=12.0,
                                      armed_at=s - timedelta(minutes=30))
        ev = orch.on_bar(IID, bar, [bar], [], candidate=None)
        assert any("FILL" in x for x in ev), ev
        # sellable_from 必须是周一 10-12，不是周六 10-10
        lots = orch.ledger.positions._lots.get(IID, [])
        assert lots and lots[0].sellable_from == date(2026, 10, 12)
