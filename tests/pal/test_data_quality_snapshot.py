"""S2-04/05/07/08 测试：质量/复权/快照/新鲜度。"""
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.adjustments import (
    AdjustmentSeries,
    CorporateAction,
    apply_action_to_position,
)
from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.data.health import (
    DataStaleError,
    FreshnessPolicy,
    FreshnessState,
    gating_for_orders,
)
from pal.data.quality import SourceMergeConflict, check_series, merge_sources
from pal.data.snapshots import build_snapshot, verify_snapshot
from pal.domain.models import DomainValidationError


def mk_bar(start, o=10.0, h=10.5, l=9.5, c=10.2, vol=100.0):
    return Bar(instrument_id="SSE.600519", timeframe="30m",
               bar_start=start, bar_end=start + timedelta(minutes=30),
               available_at=start + timedelta(minutes=30),
               open=o, high=h, low=l, close=c, volume=vol)


class TestQuality:
    def test_zero_volume_flagged(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        rep = check_series([mk_bar(s), mk_bar(s + timedelta(minutes=30), vol=0)])
        assert rep.codes_summary().get("ZERO_VOLUME") == 1

    def test_abnormal_jump_flagged(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        b1 = mk_bar(s, c=10.0)
        b2 = mk_bar(s + timedelta(minutes=30), o=15.0, h=15.5, l=14.8, c=15.2)  # +50% 跳变
        rep = check_series([b1, b2])
        assert rep.codes_summary().get("ABNORMAL_JUMP") == 1

    def test_source_conflict_raises(self):
        s = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        a = [mk_bar(s, c=10.0)]
        b = [mk_bar(s, c=10.5)]  # 5% 分歧
        with pytest.raises(SourceMergeConflict, match="供应商分歧"):
            merge_sources(a, b, tolerance_pct=0.1)

    def test_merge_fills_gap(self):
        s1 = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        s2 = datetime(2026, 10, 13, 10, 30, tzinfo=TZ)
        merged = merge_sources([mk_bar(s1)], [mk_bar(s2)])
        assert len(merged) == 2


class TestAdjustments:
    def test_split_factor(self):
        acts = AdjustmentSeries([CorporateAction(
            kind="split", instrument_id="SSE.600519",
            ex_date=date(2026, 6, 1), share_factor=2.0)])
        assert acts.forward_factor(date(2026, 7, 1)) == 2.0
        assert acts.forward_factor(date(2026, 5, 31)) == 1.0  # ex-date 前 unaffected

    def test_raw_research_roundtrip(self):
        acts = AdjustmentSeries([CorporateAction(
            kind="split", instrument_id="X", ex_date=date(2026, 6, 1),
            share_factor=2.0)])
        raw = 40.0
        adj = acts.raw_to_research(raw, date(2026, 7, 1))
        assert adj == pytest.approx(20.0)
        assert acts.research_to_raw(adj, date(2026, 7, 1)) == pytest.approx(raw)

    def test_dividend_position_credit(self):
        qty, cost, cash = apply_action_to_position(
            100, 50.0, CorporateAction(kind="cash_dividend",
                                       instrument_id="X",
                                       ex_date=date(2026, 6, 1),
                                       cash_per_share=0.5))
        assert (qty, cost, cash) == (100, 50.0, 50.0)

    def test_split_position(self):
        qty, cost, cash = apply_action_to_position(
            100, 40.0, CorporateAction(kind="split", instrument_id="X",
                                       ex_date=date(2026, 6, 1),
                                       share_factor=2.0))
        assert qty == 200
        assert cost == pytest.approx(20.0)
        assert cash == 0.0

    def test_bad_action_rejected(self):
        with pytest.raises(DomainValidationError):
            CorporateAction(kind="moon", instrument_id="X", ex_date=date(2026, 1, 1))


class TestSnapshots:
    def test_snapshot_deterministic(self, tmp_path):
        f1 = tmp_path / "a.csv"
        f1.write_text("date,close\n2026-10-12,10.0\n")
        s1 = build_snapshot([str(f1)], "30m", ("2026-10-12", "2026-10-12"),
                            "raw", "test", "cal-v1", now_iso="2026-10-12T16:00:00+08:00")
        s2 = build_snapshot([str(f1)], "30m", ("2026-10-12", "2026-10-12"),
                            "raw", "test", "cal-v1", now_iso="2026-10-12T17:00:00+08:00")
        assert s1.snapshot_id == s2.snapshot_id  # 内容寻址：时间不同 ID 相同

    def test_snapshot_detects_mutation(self, tmp_path):
        f1 = tmp_path / "a.csv"
        f1.write_text("date,close\n2026-10-12,10.0\n")
        snap = build_snapshot([str(f1)], "30m", ("x", "y"),
                              "raw", "t", "c", now_iso="2026-10-12T16:00:00+08:00")
        assert verify_snapshot(snap, str(tmp_path))[str(f1)] == "OK"
        f1.write_text("date,close\n2026-10-12,11.0\n")  # 篡改
        assert "MISMATCH" in verify_snapshot(snap, str(tmp_path))[str(f1)]


class TestFreshness:
    POLICY = FreshnessPolicy(max_lag_minutes=35)

    def test_fresh_ok(self):
        now = datetime(2026, 10, 13, 15, 20, tzinfo=TZ)
        st = FreshnessState(
            last_bar_available_at=datetime(2026, 10, 13, 15, 0, tzinfo=TZ),
            expected_latest_bar_end=datetime(2026, 10, 13, 15, 0, tzinfo=TZ))
        ok, _ = st.status(self.POLICY, now)
        assert ok

    def test_missing_final_bar_locks(self):
        now = datetime(2026, 10, 13, 16, 0, tzinfo=TZ)
        st = FreshnessState(
            last_bar_available_at=datetime(2026, 10, 13, 11, 30, tzinfo=TZ),
            expected_latest_bar_end=datetime(2026, 10, 13, 15, 0, tzinfo=TZ))
        with pytest.raises(DataStaleError, match="闭锁"):
            gating_for_orders(st, self.POLICY, now)

    def test_source_error_locks(self):
        now = datetime(2026, 10, 13, 16, 0, tzinfo=TZ)
        st = FreshnessState(last_bar_available_at=None,
                            expected_latest_bar_end=None,
                            source_error="http 502")
        with pytest.raises(DataStaleError, match="SOURCE_ERROR"):
            gating_for_orders(st, self.POLICY, now)
