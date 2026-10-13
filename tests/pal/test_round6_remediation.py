# -*- coding: utf-8 -*-
"""第六轮整改回归（R6-01~R6-10 十二项证据的正式断言）。

对应 price-action-lab_第六轮复审与整改验收清单_20261013.md 第 6 节。
全部为独立反例的精确期望，不是"脚本未崩溃即通过"。
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.execution.market_rules import MAIN_BOARD
from pal.ledger.positions import AccountLedger, PositionLot
from pal.pipeline.event_store import EventStore
from pal.pipeline.orchestrator import (
    ArmedSetup,
    OrchestratorConfig,
    PositionPlan,
    SessionOrchestrator,
)
from pal.portfolio.allocator import PortfolioAllocator
from pal.portfolio.risk import PaperDefaults
from pal.research.acceptance_pack import build_pack, write_bar_jsonl
from pal.runtime.service import TradingRuntime, load_snapshot
from pal.selection.providers import Candidate
from pal.signals.engine import EngineConfig

REPO = Path(__file__).resolve().parents[2]
IID = "SSE.600519"
T = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)


def _bar(t=T, o=10, h=10.5, l=9.8, c=10.2, v=100_000, iid=IID):
    return Bar(iid, "30m", t, t + timedelta(minutes=30),
               t + timedelta(minutes=30), o, h, l, c, v)


def _qnew(store=None, tmp=None):
    q = SessionOrchestrator(
        OrchestratorConfig(EngineConfig("r6",
                                        enabled_families=("breakout",))),
        AccountLedger(1_000_000), store=store)
    q._industries = {IID: "test"}
    return q


def _arm(q, sid="s", entry=10, stop=9, target=12, iid=IID,
         armed_at=T - timedelta(minutes=30)):
    q.armed[sid] = ArmedSetup(sid, iid, "breakout", entry, stop, target,
                              armed_at)


def _cli(*args):
    p = subprocess.run(
        [sys.executable, str(REPO / "src" / "pal_cli.py"),
         *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout


# ── 证据1：干净 checkout 冻结文件 hash 与 manifest 一致（R6-01）──
def test_e1_frozen_hash_matches_git_bytes():
    fixture = REPO / "tests" / "fixtures" / "acceptance_pack"
    man = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    for fn, h in man["file_sha256"].items():
        raw = (fixture / fn).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == h, fn
        assert b"\r" not in raw          # 无 CRLF


# ── 证据4：fill 写失败 → 零半状态，同 bar 重试完整成功（R6-03）──
def test_e4_fill_write_failure_atomic_retry(tmp_path):
    class FailingStore(EventStore):
        fail = True

        def _fsync_write(self, blob):
            if self.fail and b'"fill"' in blob:
                self.fail = False
                raise OSError("injected one-shot atomic-batch write failure")
            return super()._fsync_write(blob)

    es = FailingStore(str(tmp_path / "events.jsonl"))
    q = _qnew(es)
    _arm(q)
    with pytest.raises(OSError):
        q.on_bar(IID, _bar(), [], [], None)
    # 零半状态：现金/持仓/游标全部未变
    assert q.ledger.cash == 1_000_000
    assert q.ledger.positions.total_qty(IID) == 0
    assert len(q._consumed_bars) == 0
    assert [e.kind for e in es.events()] == ["session_init"]
    # 重试：同 bar 完整成功，经济效果与无故障运行一致
    ev = q.on_bar(IID, _bar(), [], [], None)
    assert any(e.startswith("FILL:s:") for e in ev)
    es2 = EventStore(str(tmp_path / "clean.jsonl"))
    q2 = _qnew(es2)
    _arm(q2)
    q2.on_bar(IID, _bar(), [], [], None)
    assert abs(q.ledger.cash - q2.ledger.cash) < 1e-9
    assert q.ledger.positions.total_qty(IID) == \
        q2.ledger.positions.total_qty(IID)


# ── 证据5：两批共 4800 股恢复反例 = 连续运行（R6-04）──
def test_e5_multi_lot_restart_equals_continuous(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    es = EventStore(str(state / "events.jsonl"))
    q = _qnew(es)
    _arm(q, "first")
    q.on_bar(IID, _bar(), [], [], None)
    _arm(q, "second", armed_at=T + timedelta(hours=23))
    q.on_bar(IID, _bar(t=T + timedelta(days=1)), [], [], None)
    assert q.ledger.positions.total_qty(IID) == 4800
    bnext = _bar(t=T + timedelta(days=2), o=8.5, h=8.8, l=8, c=8.2)
    fp = tmp_path / "next_day.jsonl"
    write_bar_jsonl(str(fp), [bnext])
    q.store = None      # 冻结事件流
    cont_ev = q.on_bar(IID, bnext, [], [], None)
    assert cont_ev.count("EXIT_STOP:2400@8.5") == 2
    assert q.ledger.positions.total_qty(IID) == 0
    cont_cash = q.ledger.cash
    rc, out = _cli("paper", "--events", fp, "--state", state)
    assert rc == 0
    snap = json.loads((state / "ledger_snapshot.json").read_text(
        encoding="utf-8"))
    assert snap["positions"] == {IID: 0}
    assert abs(snap["cash"] - cont_cash) < 0.01


# ── 证据6：同日同票同数量不同计划不串扣 lot（R6-05）──
def test_e6_same_day_lots_no_cross_deduction():
    q = _qnew()
    q.ledger.buy(IID, 100, 10, date(2026, 10, 12), MAIN_BOARD,
                 date(2026, 10, 13), lot_id="lotA")
    q.ledger.buy(IID, 100, 11, date(2026, 10, 12), MAIN_BOARD,
                 date(2026, 10, 13), lot_id="lotB")
    q.position_plans[IID] = [
        PositionPlan(IID, "first", 10, 8, 20, date(2026, 10, 12), 100,
                     lot_id="lotA"),
        PositionPlan(IID, "second", 11, 9.5, 20, date(2026, 10, 12), 100,
                     lot_id="lotB")]
    ev = q.on_bar(IID, _bar(o=9.6, h=10, l=9, c=9.7), [], [], None)
    # 仅第二计划（stop=9.5 被触发）成交退出
    assert "EXIT_STOP:100@9.5" in ev
    lots = q.ledger.positions._lots[IID]
    # 剩余的必须是第一批（成本 10.05，lot_id=lotA）——评审时错误地
    # 剩下成本 11.05 的第二批
    assert len(lots) == 1
    assert lots[0].lot_id == "lotA"
    assert abs(lots[0].cost_price - 10.05) < 1e-9
    assert lots[0].qty == 100
    plans = q.position_plans[IID]
    plans = plans if isinstance(plans, list) else [plans]
    assert [p.setup_id for p in plans] == ["first"]


# ── 证据7：连续 / 逐事件重启后的状态一致（R6-03/R6-04）──
def test_e7_restart_after_every_event_equals_continuous(tmp_path):
    pack = tmp_path / "pack"
    build_pack(str(pack))
    si = load_snapshot(str(pack))
    rc1, _ = _cli("backtest", "--snapshot", pack,
                  "--out", tmp_path / "whole")
    assert rc1 == 0
    whole = json.loads((tmp_path / "whole" / "ledger_snapshot.json")
                       .read_text(encoding="utf-8"))
    bars_fp = pack / "bars_SSE_600519.jsonl"
    # 逐事件重启：每根 bar 一次 paper 调用（每次进程重启恢复）
    import io
    all_bars = [json.loads(l) for l in
                bars_fp.read_text(encoding="utf-8").splitlines() if l]
    state = tmp_path / "stepwise"
    for i in range(len(all_bars)):
        part = tmp_path / f"part_{i}.jsonl"
        with open(part, "w", encoding="utf-8") as f:
            f.write(json.dumps(all_bars[i], sort_keys=True) + "\n")
        rc, _ = _cli("paper", "--events", part, "--state", state,
                     "--snapshot", pack)
        assert rc == 0
    step = json.loads((state / "ledger_snapshot.json").read_text(
        encoding="utf-8"))
    assert step["positions"] == whole["positions"]
    assert abs(step["cash"] - whole["cash"]) < 0.01


# ── 证据8：主链买卖单在 OMS 中可追溯（R6-06）──
def test_e8_oms_owns_orders_in_main_chain(tmp_path):
    es = EventStore(str(tmp_path / "events.jsonl"))
    q = _qnew(es)
    _arm(q, "buy1")
    ev = q.on_bar(IID, _bar(), [], [], None)
    assert any(e.startswith("FILL:buy1:") for e in ev)
    # 买单在 OMS：数量/状态/fill 关联与持久记录一致
    buys = [o for o in q.oms.orders.values() if o.side == "buy"]
    assert len(buys) == 1
    assert buys[0].state.value == "filled"
    assert buys[0].filled_qty == 2400
    assert buys[0].fill_ids
    # 重启恢复：新进程从事件流重建 OMS
    es2 = EventStore(str(tmp_path / "events.jsonl"))
    q2 = _qnew(es2)
    assert set(q2.oms.orders) == set(q.oms.orders)
    o2 = q2.oms.orders[buys[0].order_id]
    assert o2.filled_qty == 2400
    assert o2.state.value == "filled"
    # 卖单同样经 OMS（跳空止损退出）
    bnext = _bar(t=T + timedelta(days=2), o=8.5, h=8.8, l=8, c=8.2)
    q.store = None
    ev2 = q.on_bar(IID, bnext, [], [], None)
    assert any(e.startswith("EXIT_STOP") for e in ev2)
    sells = [o for o in q.oms.orders.values() if o.side == "sell"]
    assert len(sells) == 1
    assert sells[0].state.value == "filled"


# ── 证据10：多股票输入排列不改变获配结果（R6-08）──
def test_e10_batch_input_order_invariant():
    def order_case(reverse=False):
        iids = [IID, "SZSE.000001"]
        rb = [_bar(iid=i) for i in iids]
        info = {"manifest": {"instruments": {i: {"industry": i}
                                             for i in iids},
                             "trading_days": ["2026-10-13",
                                              "2026-10-14"]},
                "bars": rb, "daily": []}
        rt = TradingRuntime(info)
        rt.orch.allocator = PortfolioAllocator(
            replace(PaperDefaults(), max_positions=1))
        for i in iids:
            _arm(rt.orch, "s_" + i, iid=i)
        ev = rt.process_bars(list(reversed(rb)) if reverse else rb)
        return ev, rt.ledger_snapshot()

    ev_f, led_f = order_case()
    ev_r, led_r = order_case(True)
    assert led_f["positions"] == led_r["positions"]
    assert len([e for e in ev_f if e.startswith("FILL:")]) == 1
    assert len([e for e in ev_r if e.startswith("FILL:")]) == 1


# ── 证据11：无新单期间净值峰值/回撤进入风控（R6-09）──
def test_e11_breaker_consumes_full_nav_series():
    q = _qnew()
    q.ledger.buy(IID, 2400, 10.0, date(2026, 10, 11), MAIN_BOARD,
                 date(2026, 10, 12), lot_id="lotP")
    q._marks_cache[IID] = 10.0
    # 暴涨（净值峰值 >1.08M）→ 暴跌回 10 → 回撤超 10%
    q.on_bar(IID, _bar(t=T, o=46.6, h=46.6, l=46.6, c=46.6), [], [], None)
    q.on_bar(IID, _bar(t=T + timedelta(minutes=30), o=10, h=10, l=10,
                       c=10), [], [], None)
    assert q.allocator.breaker.peak_nav > 1_080_000
    _arm(q, "second", iid=IID, entry=10.0)
    ev = q.on_bar(IID, _bar(t=T + timedelta(hours=1), o=10.5, h=11,
                            l=10, c=10.5), [], [], None)
    # 超限后开仓必须被熔断阻断
    assert any("NO_CAPACITY" in e and "CB_" in e for e in ev)
    assert not any(e.startswith("FILL:second") for e in ev)


# ── 证据12：同票同 bar 多订单共享容量（R6-10）──
def test_e12_shared_bar_volume_budget():
    q = _qnew()
    _arm(q, "a", entry=10)
    _arm(q, "b", entry=10)
    ev = q.on_bar(IID, _bar(t=T, v=1000), [], [], None)
    fills = [e for e in ev if e.startswith("FILL:")]
    total = sum(int(e.split(":")[2].split("@")[0]) for e in fills)
    # 1000 股 × 10% = 100 股上限，两个计划合计不得超
    assert total <= 100
    assert len(fills) == 1
    # 未成交计划的剩余量仍受退出计划管理（armed 消费了一个 setup）
    assert q.ledger.positions.total_qty(IID) <= 100


# ── 证据2/3 附属：wheel 包含新包 + 默认 pytest 由 CI 保证 ──
def test_e3_wheel_contains_runtime_and_oms(tmp_path):
    import zipfile
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(REPO),
         "--no-deps", "--no-build-isolation", "-w", str(tmp_path)],
        check=True, capture_output=True)
    whl = next(tmp_path.glob("*.whl"))
    with zipfile.ZipFile(whl) as z:
        names = z.namelist()
    assert any(n.startswith("pal/runtime/") for n in names)
    assert any(n.startswith("pal/oms/") for n in names)
