"""时点正确的行情访问（S2-06，F17/任务书 §7 因果场景）。

规则（任务书 §4 Bar 协议）：
- 每根 bar 带 available_at（默认=bar_end；供应商延迟可叠加）；
- as-of 查询只返回 available_at <= 查询时刻 的完成 bar；
- 午间请求当日日线 → 拿不到最终 high/close（返回的是未完成标记，
  本模块直接不给，除非显式声明 partial 通道）；
- 周线/日线由 30m 聚合时，只聚合已可用的 bar。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from pal.domain.models import (
    DomainValidationError,
    require_non_negative,
    require_positive_price,
)


@dataclass(frozen=True)
class Bar:
    """一根完成K线（可用性显式）。"""
    instrument_id: str
    timeframe: str            # "30m" | "1d" | "1w"
    bar_start: datetime
    bar_end: datetime
    available_at: datetime    # 系统可知时刻（默认=bar_end，可加供应商延迟）
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    is_final: bool = True     # False = 未完成bar（只允许走显式partial通道）

    def __post_init__(self):
        if self.bar_end <= self.bar_start:
            raise DomainValidationError("bar 时间倒置")
        if self.available_at < self.bar_end:
            raise DomainValidationError(
                f"available_at({self.available_at}) 早于 bar_end({self.bar_end})："
                f"信息不可先于其产生而可用（F17）")
        for f in ("open", "high", "low", "close"):
            require_positive_price(getattr(self, f), f)
        require_non_negative(self.volume, "volume")
        if not (self.low <= self.open <= self.high
                and self.low <= self.close <= self.high
                and self.low <= self.high):
            raise DomainValidationError(
                f"OHLC 关系非法: O={self.open} H={self.high} L={self.low} C={self.close}")


class BarSeries:
    """时间排序的 bar 序列 + as-of 视图。"""

    def __init__(self, bars: Sequence[Bar]):
        self._bars = sorted(bars, key=lambda b: b.bar_start)
        for a, b in zip(self._bars, self._bars[1:]):
            if a.bar_start == b.bar_start and a.instrument_id == b.instrument_id \
                    and a.timeframe == b.timeframe:
                raise DomainValidationError(f"重复 bar: {b.bar_start}")

    def asof(self, when: datetime, instrument_id: Optional[str] = None,
             timeframe: Optional[str] = None) -> List[Bar]:
        """只取 available_at <= when 的完成 bar（因果红线）。"""
        out = [
            b for b in self._bars
            if b.available_at <= when and b.is_final
            and (instrument_id is None or b.instrument_id == instrument_id)
            and (timeframe is None or b.timeframe == timeframe)
        ]
        return out

    def last_known_close(self, when: datetime, instrument_id: str) -> Optional[float]:
        bars = self.asof(when, instrument_id=instrument_id)
        return bars[-1].close if bars else None

    def __len__(self) -> int:
        return len(self._bars)

    @property
    def bars(self) -> List[Bar]:
        return list(self._bars)


def resample_30m_to_daily(bars_30m: Sequence[Bar], instrument_id: str,
                          expected_slots_per_day: int = 8,
                          calendar: Optional["TradingCalendar"] = None,
                          ) -> List[Bar]:
    """30m → 日线（R03+F07+T06 修正：证券过滤+完整性+槽位唯一+日历强制）。

    无日历时（legacy 近似）：
    - 只聚合 instrument_id 匹配的完成 bar；
    - F07：同一槽位（bar_start）重复出现 → 该日不构成 final；
    - 不足 expected_slots_per_day → is_final=False。

    T06（传入 TradingCalendar 时，正式路径）：
    - 混票/错周期 bar → 直接拒绝（DomainValidationError），不静默丢弃；
    - 非交易日出现的 bar → 该日不构成 final；
    - 槽位集合必须与日历网格（calendar.bars_for_day）精确相等——
      缺槽（含缺尾棒）、多槽、跨午休错位一律 partial；
    - final 日线的 available_at = 15:00 收盘（日历口径）。
    """
    from pal.data.calendar import TradingCalendar  # 局部导入避免环

    by_day = {}
    dup_detected = set()
    seen_slots = set()
    for b in bars_30m:
        if not b.is_final:
            continue
        if b.instrument_id != instrument_id:
            continue        # 混票由调用方过滤；这里只处理本票
        if b.timeframe != "30m":
            raise DomainValidationError(
                f"错周期输入: {b.timeframe}（期望 30m，T06 拒绝静默聚合）")
        d = b.bar_start.date()
        slot = (d, b.bar_start.time())
        if slot in seen_slots:
            dup_detected.add(d)          # F07：重复数据
            continue
        seen_slots.add(slot)
        by_day.setdefault(d, []).append(b)
    daily = []
    for d in sorted(by_day):
        chunk = sorted(by_day[d], key=lambda x: x.bar_start)
        if calendar is not None:
            # T06：日历网格精确匹配
            if not calendar.is_trading_day(d):
                complete = False
            else:
                expected = {s.time() for s, _ in calendar.bars_for_day(d)}
                actual = {b.bar_start.time() for b in chunk}
                complete = (actual == expected and d not in dup_detected)
        else:
            complete = (len(chunk) >= expected_slots_per_day
                        and d not in dup_detected)
        day_end = chunk[-1].bar_end
        # A09：最终可知时间 ≥ max(正式收盘可用时刻, 所有输入 available_at)
        # ——供应商延迟必须传播，不得提前暴露收盘数据
        if calendar is not None and calendar.is_trading_day(d):
            avail = max(calendar.daily_close_available_at(d),
                        max(x.available_at for x in chunk))
        else:
            avail = max(x.available_at for x in chunk)
        daily.append(Bar(
            instrument_id=instrument_id, timeframe="1d",
            bar_start=chunk[0].bar_start, bar_end=day_end,
            available_at=avail,
            open=chunk[0].open, high=max(x.high for x in chunk),
            low=min(x.low for x in chunk), close=chunk[-1].close,
            volume=sum(x.volume for x in chunk),
            amount=sum(x.amount for x in chunk),
            is_final=complete,
        ))
    return daily
