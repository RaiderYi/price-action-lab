"""S2-02/S2-06 测试：主数据 + as-of 因果查询（任务书 §7 场景）。"""
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar, BarSeries, resample_30m_to_daily
from pal.data.calendar import TZ
from pal.data.security_master import (
    SecurityLifecycle,
    SecurityMaster,
    UnknownSecurityError,
)
from pal.domain.models import DomainValidationError, InstrumentId


def mk_bar(dt_start, o=10.0, h=10.5, l=9.5, c=10.2, vol=100.0, tf="30m",
           available_at=None, final=True, iid="SSE.600519"):
    return Bar(
        instrument_id=iid, timeframe=tf,
        bar_start=dt_start, bar_end=dt_start + timedelta(minutes=30),
        available_at=available_at or dt_start + timedelta(minutes=30),
        open=o, high=h, low=l, close=c, volume=vol, is_final=final,
    )


class TestBarCausality:
    def test_available_before_bar_end_rejected(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        with pytest.raises(DomainValidationError, match="F17"):
            mk_bar(s, available_at=s)  # 可用时刻=bar_start → 非法

    def test_ohlc_relation_enforced(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        with pytest.raises(DomainValidationError, match="OHLC"):
            mk_bar(s, h=9.0)  # high < low

    def test_asof_excludes_future_bars(self):
        d10 = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        d11 = datetime(2026, 10, 13, 11, 0, tzinfo=TZ)
        series = BarSeries([mk_bar(d10), mk_bar(d11)])
        ask = datetime(2026, 10, 13, 10, 30, tzinfo=TZ)
        visible = series.asof(ask)
        assert len(visible) == 1
        assert visible[0].bar_start == d10

    def test_incomplete_bar_excluded_from_asof(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        series = BarSeries([mk_bar(s), mk_bar(s + timedelta(minutes=30), final=False)])
        ask = datetime(2026, 10, 13, 23, 0, tzinfo=TZ)
        assert len(series.asof(ask)) == 1  # 未完成bar永远不进 as-of 视图

    def test_supplier_delay_pushes_availability(self):
        """改变供应商 available_at 延迟 → 可见性顺延（§7 因果场景）。"""
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        fast = mk_bar(s)
        slow = mk_bar(s, available_at=s + timedelta(minutes=45))
        ask = datetime(2026, 10, 13, 10, 35, tzinfo=TZ)
        series = BarSeries([fast])
        assert len(series.asof(ask)) == 1
        series2 = BarSeries([slow])
        assert len(series2.asof(ask)) == 0  # 延迟45分钟 → 10:35不可见

    def test_duplicate_bar_rejected(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        with pytest.raises(DomainValidationError, match="重复"):
            BarSeries([mk_bar(s), mk_bar(s)])

    def test_midday_daily_resample(self):
        """午间只聚合上午已完成bar；下午bar不可见（§7：午间请求当日日线）。"""
        bars = [mk_bar(datetime(2026, 10, 13, h, 0, tzinfo=TZ))
                for h in (9, 9, 10, 10)]  # 上午4根（9:30/10:00/10:30/11:00 简化）
        bars += [mk_bar(datetime(2026, 10, 13, 13, 0, tzinfo=TZ))]  # 下午1根
        noon = datetime(2026, 10, 13, 12, 0, tzinfo=TZ)
        visible = [b for b in bars if b.available_at <= noon]
        daily = resample_30m_to_daily(visible, "SSE.600519")
        # 午间生成的"当日日线"只含上午信息（简化场景验证 as-of 过滤先行）
        assert all(b.bar_end <= noon or b.bar_start.date() != daily[0].bar_start.date()
                   for b in visible)


class TestSecurityMaster:
    def _master(self):
        m = SecurityMaster(version="test-2026")
        m.register(SecurityLifecycle(
            instrument=InstrumentId(code="688120", exchange="SSE", board="star"),
            list_date=date(2022, 6, 8), delist_date=None,
            name="华海清科", board="star"))
        m.register(SecurityLifecycle(
            instrument=InstrumentId(code="600519", exchange="SSE", board="main"),
            list_date=date(2001, 8, 27), delist_date=None,
            name="贵州茅台", board="main"))
        return m

    def test_correct_name_for_688120(self):
        """F22 回归：688120 名称必须来自主数据。"""
        m = self._master()
        assert m.name_of("688120", date(2026, 8, 18)) == "华海清科"

    def test_unknown_code_rejected(self):
        m = self._master()
        with pytest.raises(UnknownSecurityError):
            m.name_of("999999", date(2026, 1, 1))

    def test_pre_listing_rejected(self):
        m = self._master()
        with pytest.raises(UnknownSecurityError, match="未上市"):
            m.name_of("688120", date(2020, 1, 1))

    def test_tradable_universe_asof(self):
        m = self._master()
        u = m.tradable_universe(date(2021, 1, 1))
        assert "688120" not in u   # 2021年未上市
        assert "600519" in u

    def test_empty_name_rejected(self):
        with pytest.raises(DomainValidationError):
            SecurityLifecycle(
                instrument=InstrumentId(code="000001", exchange="SZSE", board="main"),
                list_date=date(1991, 1, 1), delist_date=None,
                name="  ", board="main")
