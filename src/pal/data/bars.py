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
                          expected_slots_per_day: int = 8) -> List[Bar]:
    """30m → 日线（R03 修正：完整性检查 + 证券过滤）。

    - 只聚合 instrument_id 匹配的完成 bar；
    - 每交易日聚合后与 expected_slots_per_day 比对：不足 → 不产出
      final 日线（输出 partial：is_final=False，或直接不产出当根为空时）；
    - available_at = 参与bar 的最大 available_at（供应商延迟传播，R10）。
    """
    by_day = {}
    for b in bars_30m:
        if not b.is_final:
            continue
        if b.instrument_id != instrument_id:      # R03：证券过滤
            continue
        d = b.bar_start.date()
        by_day.setdefault(d, []).append(b)
    daily = []
    for d in sorted(by_day):
        chunk = sorted(by_day[d], key=lambda x: x.bar_start)
        complete = len(chunk) >= expected_slots_per_day    # R03：完整性
        day_end = chunk[-1].bar_end
        daily.append(Bar(
            instrument_id=instrument_id, timeframe="1d",
            bar_start=chunk[0].bar_start, bar_end=day_end,
            available_at=max(x.available_at for x in chunk),
            open=chunk[0].open, high=max(x.high for x in chunk),
            low=min(x.low for x in chunk), close=chunk[-1].close,
            volume=sum(x.volume for x in chunk),
            amount=sum(x.amount for x in chunk),
            is_final=complete,        # R03：不足8根 → 非 final
        ))
    # 只保留 final 日线为常规输出语义？不——partial 显式保留但标记，
    # 调用方 as-of 视图天然排除（BarSeries.asof 过滤 is_final）。
    return daily
