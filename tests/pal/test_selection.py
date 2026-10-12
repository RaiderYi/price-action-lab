"""S3 测试：提供者协议 / V1桥接 / 去重合并 / 基线 / 生命周期。"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError
from pal.selection.merge import (
    CandidateLifecycle,
    merge_candidates,
    rank_by_score,
)
from pal.selection.providers import (
    BridgeFormatError,
    Candidate,
    StaticPoolProvider,
    candidates_from_structured_v1,
    parse_structured_v1,
)
from pal.selection.baselines import BaselineParams, baseline_rank


def mk_cand(iid, models, at, direction="buy", eligible=None):
    return Candidate(
        candidate_id=f"c_{iid}_{'-'.join(models)}", instrument_id=iid,
        source_models=tuple(models), available_at=at,
        eligible_from=eligible or at, estimate=None,
        meta={"direction": direction})


ASOF = datetime(2026, 10, 12, 15, 30, tzinfo=TZ)


class TestCandidateContract:
    def test_eligible_before_available_rejected(self):
        with pytest.raises(DomainValidationError, match="候选不可"):
            mk_cand("SSE.600519", ["m1"], ASOF,
                    eligible=ASOF - timedelta(minutes=1))

    def test_no_source_rejected(self):
        with pytest.raises(DomainValidationError):
            mk_cand("SSE.600519", [], ASOF)

    def test_static_provider(self):
        p = StaticPoolProvider(["SSE.600519", "SZSE.000001"], ASOF)
        cands = p.candidates(ASOF)
        assert len(cands) == 2


V1_OK = """<!-- TRADE_PLAN_STRUCTURED_V1 -->
```json
{"symbol": "600519", "direction": "buy", "models": ["m1", "m3"],
 "asof": "2026-10-12T15:30:00+08:00", "eligible_from": "2026-10-13T09:30:00+08:00"}
```
"""


class TestStructuredV1Bridge:
    def test_valid_block(self):
        objs = parse_structured_v1(V1_OK)
        assert len(objs) == 1
        assert objs[0]["symbol"] == "600519"

    def test_leading_zero_symbol_ok(self):
        text = V1_OK.replace("600519", "000001")
        cands = candidates_from_structured_v1(
            text, exchange_of=lambda c: "SZSE")
        assert cands[0].instrument_id == "SZSE.000001"

    def test_missing_field_rejected(self):
        bad = V1_OK.replace('"direction": "buy", ', "")
        with pytest.raises(BridgeFormatError, match="缺必需字段"):
            parse_structured_v1(bad)

    def test_time_inversion_rejected(self):
        bad = V1_OK.replace("2026-10-13T09:30:00+08:00", "2026-10-12T09:30:00+08:00")
        with pytest.raises(BridgeFormatError, match="时间倒置"):
            parse_structured_v1(bad)

    def test_non_string_symbol_rejected(self):
        bad = V1_OK.replace('"600519"', "600519")
        with pytest.raises(BridgeFormatError, match="symbol"):
            parse_structured_v1(bad)

    def test_mark_without_block_rejected(self):
        with pytest.raises(BridgeFormatError, match="无法提取"):
            parse_structured_v1("some text TRADE_PLAN_STRUCTURED_V1 junk")

    def test_no_mark_returns_empty(self):
        assert parse_structured_v1("普通文档，无块") == []

    def test_markdown_table_not_parsed(self):
        """任务书：不靠解析 Markdown 表格获得交易事实。"""
        table = "| symbol | dir |\n|---|---|\n| 600519 | buy |"
        assert parse_structured_v1(table) == []


class TestMergeDedupe:
    def test_five_models_one_position(self):
        cands = [mk_cand("SSE.600519", [f"m{i}"], ASOF) for i in range(5)]
        merged = merge_candidates(cands)
        assert len(merged) == 1
        assert len(merged[0].sources) == 5   # 来源保留

    def test_conflict_recorded_not_dropped(self):
        cands = [
            mk_cand("SSE.600519", ["m1", "m2"], ASOF, direction="buy"),
            mk_cand("SSE.600519", ["m3"], ASOF, direction="sell"),
        ]
        merged = merge_candidates(cands)
        assert merged[0].conflicts == ("m3",)  # 少数侧记入冲突

    def test_different_instruments_kept(self):
        cands = [mk_cand("SSE.600519", ["m1"], ASOF),
                 mk_cand("SZSE.000001", ["m1"], ASOF)]
        assert len(merge_candidates(cands)) == 2

    def test_rank_deterministic_tiebreak(self):
        cands = [mk_cand("SSE.688120", ["m1"], ASOF),
                 mk_cand("SSE.600519", ["m2"], ASOF)]
        merged = merge_candidates(cands)
        ranked = rank_by_score(merged, scorer=lambda m: (0.5, {"flat": 0.5}))
        # 同分 → 按代码升序
        assert [r.instrument_id for r in ranked] == ["SSE.600519", "SSE.688120"]


class TestLifecycle:
    def test_not_yet_eligible(self):
        c = mk_cand("SSE.600519", ["m1"], ASOF,
                    eligible=ASOF + timedelta(hours=18))
        lc = CandidateLifecycle()
        ok, why = lc.validate_for_session(c, session_open=ASOF, now=ASOF)
        assert not ok and "NOT_YET_ELIGIBLE" in why

    def test_eligible_next_day_ok(self):
        c = mk_cand("SSE.600519", ["m1"], ASOF,
                    eligible=datetime(2026, 10, 13, 9, 30, tzinfo=TZ))
        lc = CandidateLifecycle()
        ok, _ = lc.validate_for_session(
            c, session_open=datetime(2026, 10, 13, 9, 30, tzinfo=TZ),
            now=datetime(2026, 10, 13, 9, 35, tzinfo=TZ))
        assert ok

    def test_expired_after_24h(self):
        c = mk_cand("SSE.600519", ["m1"], ASOF)
        lc = CandidateLifecycle(max_valid_hours=24)
        ok, why = lc.validate_for_session(
            c, session_open=ASOF, now=ASOF + timedelta(hours=25))
        assert not ok and "EXPIRED" in why


def mk_daily(n, start_price=10.0, drift=0.001, amount=5e7):
    from datetime import date, time, timedelta as td
    bars = []
    px = start_price
    d0 = date(2026, 1, 5)
    for i in range(n):
        px *= (1 + drift)
        d = d0 + td(days=i)
        s = datetime.combine(d, time(9, 30), tzinfo=TZ)
        e = datetime.combine(d, time(15, 0), tzinfo=TZ)
        bars.append(Bar(instrument_id="X", timeframe="1d",
                        bar_start=s, bar_end=e, available_at=e,
                        open=px * 0.999, high=px * 1.005, low=px * 0.995,
                        close=px, volume=1e6, amount=amount))
    return bars


class TestBaseline:
    def test_rank_orders_by_momentum(self):
        strong = mk_daily(80, drift=0.003)
        weak = mk_daily(80, drift=-0.001)
        params = BaselineParams(top_k=10)
        ranked = baseline_rank(
            {"SSE.STRONG": strong, "SSE.WEAK": weak}, params)
        assert ranked[0][0] == "SSE.STRONG"
        assert ranked[0][2]["momentum"] > 0 > ranked[1][2]["momentum"]

    def test_illiquid_excluded(self):
        thin = mk_daily(80, amount=1e6)   # 100万/日 < 3000万下限
        ranked = baseline_rank({"SSE.THIN": thin}, BaselineParams())
        assert ranked == []

    def test_insufficient_data_skipped(self):
        short = mk_daily(30)
        ranked = baseline_rank({"SSE.SHORT": short}, BaselineParams())
        assert ranked == []
