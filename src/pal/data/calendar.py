"""交易日历与 30m bar 对齐（S2-03）。

A 股连续竞价时段（上交所/深交所普通股票）：
  上午 09:30–11:30，下午 13:00–15:00（Asia/Shanghai）
30m bar 网格：每日 8 根
  09:30-10:00, 10:00-10:30, 10:30-11:00, 11:00-11:30
  13:00-13:30, 13:30-14:00, 14:00-14:30, 14:30-15:00

节假日由使用方注入（官方放假安排每年发布，不做内置猜测——
日历版本化随快照冻结）。bar 可用时刻 = bar_end（无供应商延迟时）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, List, Optional, Sequence, Tuple

from pal.domain.models import DomainValidationError

TZ = timezone(timedelta(hours=8))  # Asia/Shanghai

SESSIONS: Tuple[Tuple[time, time], ...] = (
    (time(9, 30), time(11, 30)),
    (time(13, 0), time(15, 0)),
)

BAR_MINUTES = 30


@dataclass(frozen=True)
class TradingCalendar:
    """显式交易日集合 + 节假日集合的日历（版本化数据，非算法猜测）。"""
    trading_days: Tuple[date, ...]
    calendar_version: str

    def __post_init__(self):
        if not self.trading_days:
            raise DomainValidationError("trading_days 不能为空")
        if list(self.trading_days) != sorted(set(self.trading_days)):
            raise DomainValidationError("trading_days 必须严格递增去重")
        if not self.calendar_version:
            raise DomainValidationError("calendar_version 不能为空")

    # ── 基本查询 ──
    def is_trading_day(self, d: date) -> bool:
        return d in self._index

    @property
    def _index(self) -> set:
        # frozen dataclass 缓存走外部；小数据量直接建
        return set(self.trading_days)

    def next_trading_day(self, d: date) -> date:
        for td in self.trading_days:
            if td > d:
                return td
        raise KeyError(f"{d} 之后无交易日（日历范围外）")

    def prev_trading_day(self, d: date) -> Optional[date]:
        prev = None
        for td in self.trading_days:
            if td < d:
                prev = td
            else:
                break
        return prev

    # ── 30m bar 网格 ──
    def bars_for_day(self, d: date) -> List[Tuple[datetime, datetime]]:
        """某交易日的 8 根 30m bar (start, end)（bar_end=available_at 基线）。"""
        if not self.is_trading_day(d):
            return []
        bars = []
        for s, e in SESSIONS:
            t = s
            while t < e:
                t2 = (
                    datetime.combine(d, t) + timedelta(minutes=BAR_MINUTES)
                ).time()
                bars.append((
                    datetime.combine(d, t, tzinfo=TZ),
                    datetime.combine(d, t2, tzinfo=TZ),
                ))
                t = t2
        return bars

    def expected_bar_slots_between(self, start: date, end: date) -> int:
        n = 0
        for td in self.trading_days:
            if start <= td <= end:
                n += len(self.bars_for_day(td))
        return n

    def daily_close_available_at(self, d: date) -> datetime:
        """日线最终 bar 的可用时刻 = 收盘 15:00（午间请求当日日线拿不到完成bar，
        任务书 §7 因果验收场景）。"""
        if not self.is_trading_day(d):
            raise KeyError(f"{d} 非交易日")
        return datetime.combine(d, time(15, 0), tzinfo=TZ)


def calendar_from_sessions(days: Iterable[date], version: str) -> TradingCalendar:
    return TradingCalendar(tuple(sorted(set(days))), version)
