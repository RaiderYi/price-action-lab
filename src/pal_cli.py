"""pal CLI entrypoint（S0-03 → T12 → N03/N10 第四轮接通）。

命令：
    pal doctor / version        环境自检 / 版本指纹
    pal scan --snapshot D       盘后扫描：候选→真实引擎评估→日报
    pal backtest --snapshot D   历史回放（跨日历史+事件仓库+账本快照）
    pal paper --events F --state D   离线 paper（消费事件文件、可恢复）
    pal report --run D          渲染 run 产物
    pal reconcile --run D       对账：事件重放 vs 账本快照

N03 状态语义（A02）：
    NO_CANDIDATES / NO_SIGNAL / NO_TRADES / BLOCKED / FAILED 分立，
    不再用空跑退出码 0 冒充策略运行成功。
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

EXIT_OK = 0
EXIT_NO_TRADES = 0          # 策略运行成功但无交易（结构化区分）
EXIT_USAGE = 1
EXIT_INVALID = 2
EXIT_BLOCKED = 3

STATUS_FILE = "run_status.json"   # N03：结构化状态必写


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_id() -> str:
    return f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _git_commit() -> str:
    try:
        import subprocess
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=_SRC)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


LEGACY_MODULES = [
    "bar_counting_detector", "focus_config", "market_analyzer",
    "signal_predictor", "signal_registry", "strict_breakout_strength",
    "strict_pa_detector", "strict_pa_qualification",
    "strict_pa_actionability", "system_price_builder",
]
KNOWN_OPTIONAL = ["kb_rules", "brooks_ontology_registry", "rule_guardrail"]
KERNEL_MODULES = [
    "pal.pipeline.orchestrator", "pal.portfolio.allocator",
    "pal.pipeline.event_store", "pal.research.backtest_runner",
    "pal.reporting.daily_plan",
]


def _doctor(_args=None) -> int:
    import platform
    print(f"python: {platform.python_version()}")
    failed = []
    for label, mods in (("core", LEGACY_MODULES),
                        ("kernel", KERNEL_MODULES)):
        print(f"--- {label} modules ---")
        for m in mods:
            try:
                importlib.import_module(m)
                print(f"  ok   {m}")
            except Exception as e:  # noqa: BLE001
                failed.append(m)
                print(f"  FAIL {m}: {type(e).__name__}: {e}")
    print("--- optional external ---")
    for m in KNOWN_OPTIONAL:
        try:
            importlib.import_module(m)
            print(f"  present {m}")
        except ImportError:
            print(f"  absent  {m} (capability disabled)")
    if failed:
        print(f"INVALID: {failed}")
        return EXIT_INVALID
    print("OK")
    return EXIT_OK


DATA_PROVIDER_STATUS = {
    "provider": "none", "status": "BLOCKED",
    "reason": "真实行情 provider 未接入（N12 外部依赖）",
}


def _load_bars_file(fp: str):
    from datetime import datetime as _dt
    from pal.data.bars import Bar
    bars = []
    with open(fp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            bars.append(Bar(
                instrument_id=d["instrument_id"], timeframe=d["timeframe"],
                bar_start=_dt.fromisoformat(d["bar_start"]),
                bar_end=_dt.fromisoformat(d["bar_end"]),
                available_at=_dt.fromisoformat(d["available_at"]),
                open=d["open"], high=d["high"], low=d["low"],
                close=d["close"], volume=d["volume"],
                amount=d.get("amount", 0.0),
                is_final=d.get("is_final", True)))
    return bars


def _load_snapshot(snap: str) -> dict:
    """载入快照：bars + daily + manifest（校验 hash 契约）。"""
    import glob as _glob
    mf_path = os.path.join(snap, "manifest.json")
    if not os.path.isfile(mf_path):
        print(f"ERROR: 快照缺 manifest.json: {snap}", file=sys.stderr)
        raise SystemExit(EXIT_INVALID)
    with open(mf_path, encoding="utf-8") as f:
        manifest = json.load(f)
    bars, daily = [], []
    input_hashes = {}
    for fp in sorted(_glob.glob(os.path.join(snap, "bars_*.jsonl"))):
        input_hashes[os.path.basename(fp)] = _sha256_file(fp)
        bars += _load_bars_file(fp)
    for fp in sorted(_glob.glob(os.path.join(snap, "daily_*.jsonl"))):
        input_hashes[os.path.basename(fp)] = _sha256_file(fp)
        daily += _load_bars_file(fp)
    # manifest 声明的 hash 必须匹配（篡改检测，A12 版本追溯）
    # V09：声明文件缺失 = 契约违反，直接拒绝（不再静默接受）
    declared = manifest.get("file_sha256", {})
    for fn, h in declared.items():
        if not os.path.isfile(os.path.join(snap, fn)):
            print(f"ERROR: 声明的输入文件缺失: {fn}", file=sys.stderr)
            raise SystemExit(EXIT_INVALID)
        actual = input_hashes.get(fn)
        if actual is not None and actual != h:
            print(f"ERROR: 快照文件与冻结 hash 不符: {fn}", file=sys.stderr)
            raise SystemExit(EXIT_INVALID)
    return {"manifest": manifest, "bars": bars, "daily": daily,
            "input_hashes": input_hashes}


def _manifest_doc(run_id: str, config_version: str, snap_info: dict,
                  status: str) -> dict:
    return {
        "run_id": run_id,
        "created_at": _now_iso(),
        "commit": _git_commit(),
        "config_version": config_version,
        "kernel": "SessionOrchestrator",
        "input_hashes": snap_info["input_hashes"],
        "snapshot_id": snap_info["manifest"].get("snapshot_id"),
        "calendar_version": snap_info["manifest"].get(
            "calendar_version", "snapshot-derived"),
        "status": status,       # N03：OK / NO_CANDIDATES / NO_SIGNAL / ...
    }


def _write_status(out_dir: str, status: str, detail: dict) -> None:
    with open(os.path.join(out_dir, STATUS_FILE), "w",
              encoding="utf-8") as f:
        json.dump({"status": status, "detail": detail,
                   "generated_at": _now_iso()}, f,
                  ensure_ascii=False, indent=1)


def _candidates_from_snapshot(snap_info: dict):
    """N03/A02：候选来自快照 instruments（StaticPool 契约）。"""
    from pal.selection.providers import Candidate
    man = snap_info["manifest"]
    iids = list(man.get("instruments", {}).keys())
    if not iids:
        return []
    asof_date = man.get("asof_date")
    from datetime import datetime as _dt, timezone as _tz
    tz = _tz(_dt.now().utcoffset() or timezone.utc.utcoffset(None)
             if False else timezone.utc.utcoffset(None))
    asof = _dt.fromisoformat(asof_date + "T00:00:00+08:00") \
        if asof_date else None
    if asof is None:
        return []
    return [Candidate(
        candidate_id=f"cand_{iid.replace('.', '_')}",
        instrument_id=iid, source_models=("static_pool",),
        available_at=asof, eligible_from=asof, estimate=None)
        for iid in iids]


def _cmd_scan(args) -> int:
    """R6-07：盘后扫描——复用统一 TradingRuntime（与 backtest 同一
    决策/订单/风控/账本内核），scan 只做决策投影：无 store、无持久化、
    无账户副作用，输出候选状态（awaiting_trigger/watch/rejected）。
    """
    snap = _arg(args, "--snapshot")
    if not snap:
        print("usage: pal scan --snapshot DIR [--out DIR]", file=sys.stderr)
        return EXIT_USAGE
    si = _load_snapshot(snap)
    run_id = _run_id()
    out_dir = _arg(args, "--out") or os.path.join("runs", run_id)
    os.makedirs(out_dir, exist_ok=True)
    if not si["bars"]:
        _write_status(out_dir, "BLOCKED", {"reason": "无行情"})
        print("BLOCKED: 快照无 bars_*.jsonl")
        return EXIT_BLOCKED
    from pal.reporting.daily_plan import (
        DailyPlanEntry, render_daily_plan, write_outputs)
    from pal.runtime.service import TradingRuntime

    rt = TradingRuntime(si, 1_000_000.0, engine_version="cli-scan-v1")
    orch = rt.orch
    # V08：ARMED/FILL 即时捕获（setup 成交/过期后从 orch.armed 消失，
    # 必须在每根 bar 处理时即时记录归属票）
    armed_seen: set = set()
    _orig_on_bar = orch.on_bar

    def _capture_on_bar(iid, bar, *a, **k):
        ev = _orig_on_bar(iid, bar, *a, **k)
        for e in ev:
            if e.startswith(("ARMED:", "FILL:")):
                armed_seen.add(iid)
        return ev

    orch.on_bar = _capture_on_bar
    ev_all = rt.process_bars(si["bars"])
    evaluated = {b.instrument_id for b in si["bars"]
                 if rt.day_candidates(b.bar_start.date())}
    # 触发成交的票也算 awaiting 过（scan 语义：曾有武装计划）
    entries = []
    for iid in sorted(evaluated):
        reasons = [w for c, w in orch.rejected_candidates if c == iid]
        if iid in armed_seen:
            entries.append(DailyPlanEntry(iid, iid, "awaiting_trigger",
                                          ["ARMED"], {}))
        elif reasons:
            entries.append(DailyPlanEntry(iid, iid, "rejected",
                                          reasons, {}))
        else:
            entries.append(DailyPlanEntry(iid, iid, "watch",
                                          ["NO_SIGNAL"], {}))
    doc = render_daily_plan(
        plan_date=si["manifest"].get("asof_date", "unknown"),
        entries=entries, run_id=run_id, config_version="cli-scan-v1")
    write_outputs(doc, os.path.join(out_dir, "daily_plan.json"),
                  os.path.join(out_dir, "daily_plan.md"))
    has_signal = bool(armed_seen)
    status = "OK" if has_signal else "NO_SIGNAL"
    _write_status(out_dir, status, {
        "evaluated": sorted(evaluated),
        "not_evaluated": sorted(
            {b.instrument_id for b in si["bars"]} - evaluated),
        "armed": sorted(armed_seen),
        "account_side_effects": False})
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest_doc(run_id, "cli-scan-v1", si, status), f,
                  ensure_ascii=False, indent=1)
    print(f"scan {status}: run={run_id} armed={len(armed_seen)} "
          f"evaluated={len(evaluated)}")
    print(f"  report: {os.path.join(out_dir, 'daily_plan.md')}")
    return EXIT_OK


def _cmd_backtest(args) -> int:
    snap = _arg(args, "--snapshot")
    if not snap:
        print("usage: pal backtest --snapshot DIR [--out DIR]",
              file=sys.stderr)
        return EXIT_USAGE
    si = _load_snapshot(snap)
    run_id = _run_id()
    out_dir = _arg(args, "--out") or os.path.join("runs", run_id)
    os.makedirs(out_dir, exist_ok=True)
    if not si["bars"]:
        _write_status(out_dir, "BLOCKED", {"reason": "无行情"})
        return EXIT_BLOCKED
    from datetime import date as _date
    from pal.data.calendar import TradingCalendar
    from pal.pipeline.event_store import EventStore
    from pal.pipeline.orchestrator import OrchestratorConfig
    from pal.research.backtest_runner import BacktestDay, BacktestRunner
    from pal.signals.engine import EngineConfig

    cands = _candidates_from_snapshot(si)
    days = sorted({b.bar_start.date() for b in si["bars"]})
    cal = TradingCalendar(tuple(days), si["manifest"].get(
        "calendar_version", "snapshot-derived"))
    by_day = {}
    for b in si["bars"]:
        by_day.setdefault(b.bar_start.date(), []).append(b)
    daily_by_iid = {}
    for b in si["daily"]:
        daily_by_iid.setdefault(b.instrument_id, []).append(b)

    from datetime import datetime as _dtm
    # AR11：CLI 只是适配器——统一走 TradingRuntime 服务
    from pal.runtime.service import TradingRuntime
    store = EventStore(os.path.join(out_dir, "events.jsonl"))
    rt = TradingRuntime(si, 1_000_000.0, store=store,
                        engine_version="cli-backtest-v1")
    all_ev = rt.process_bars(si["bars"])
    class _Res:  # 兼容产物结构
        events = all_ev
        final_cash = rt.ledger.cash
        final_nav = rt.ledger.cash
        nav_series = list(rt.orch.nav_series)
        open_position_marks = {}
    res = _Res()
    marks = {b.instrument_id: b.close for b in si["bars"]}
    res.final_nav = rt.ledger.nav(marks)
    for iid in {b.instrument_id for b in si["bars"]}:
        q = rt.ledger.positions.total_qty(iid)
        if q > 0:
            res.open_position_marks[iid] = (q, marks[iid])

    marks = {b.instrument_id: b.close for b in si["bars"]}
    traded = {e.payload["instrument_id"] for e in store.by_kind("fill")}
    ledger_snapshot = {
        "cash": round(rt.ledger.cash, 4),
        "positions": {iid: rt.ledger.positions.total_qty(iid)
                      for iid in sorted(traded)},
    }
    with open(os.path.join(out_dir, "ledger_snapshot.json"), "w",
              encoding="utf-8") as f:
        json.dump(ledger_snapshot, f, ensure_ascii=False, indent=1)

    n_fills = len(store.by_kind("fill"))
    status = "OK" if n_fills > 0 else (
        "NO_SIGNAL" if not cands is None and len(cands) == 0 else
        "NO_TRADES")
    nav_doc = {
        "schema": "backtest/v2",
        "run_id": run_id,
        "n_days": len(by_day),
        "n_candidates": len(cands),
        "n_events": len(res.events),
        "n_fills": n_fills,
        "status": status,
        "final_cash": round(res.final_cash, 2),
        "final_nav": round(res.final_nav, 2) if res.final_nav else None,
        "open_positions_marked": {
            k: [v[0], v[1]] for k, v in res.open_position_marks.items()},
        "nav_series": [[t.isoformat(), round(v, 2)]
                       for t, v in res.nav_series],
        "events": res.events,
        "caveat": "快照数据；交易链真实执行；不构成收益证据（M4 需预注册研究）",
    }
    with open(os.path.join(out_dir, "backtest.json"), "w",
              encoding="utf-8") as f:
        json.dump(nav_doc, f, ensure_ascii=False, indent=1)
    _write_status(out_dir, status, {"n_fills": n_fills})
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest_doc(run_id, "cli-backtest-v1", si, status), f,
                  ensure_ascii=False, indent=1)
    print(f"backtest {status}: run={run_id} days={len(by_day)} "
          f"fills={n_fills} events={len(res.events)} "
          f"nav={nav_doc['final_nav']}")
    print(f"  events : {os.path.join(out_dir, 'events.jsonl')}")
    print(f"  ledger : {os.path.join(out_dir, 'ledger_snapshot.json')}")
    return EXIT_OK


def _cmd_paper(args) -> int:
    """N03/V04/V05 + R6-04/R6-07：离线 paper——统一 Runtime 驱动。

    恢复（R6-04）：按真实 fill→lot→plan 关联逐笔重放每笔买卖及
    剩余数量——恢复现金、lot（含费成本+可卖日）、全部退出计划
    （含剩余量）、consumed 游标、OMS 订单/占用。多批持仓每批
    独立恢复，不再压成一个 lot 取最后一笔买入。
    """
    events_fp = _arg(args, "--events")
    state_dir = _arg(args, "--state")
    if not events_fp:
        print("usage: pal paper --events BARS_JSONL [--state DIR]",
              file=sys.stderr)
        return EXIT_USAGE
    if not os.path.isfile(events_fp):
        print(f"ERROR: 事件文件不存在: {events_fp}", file=sys.stderr)
        return EXIT_INVALID
    run_id = _run_id()
    out_dir = state_dir or os.path.join("runs", run_id)
    os.makedirs(out_dir, exist_ok=True)
    bars = _load_bars_file(events_fp)
    if not bars:
        _write_status(out_dir, "BLOCKED", {"reason": "事件文件无 bar"})
        return EXIT_BLOCKED
    from datetime import date as _date, datetime as _dtm
    from pal.data.calendar import TradingCalendar
    from pal.pipeline.event_store import EventStore, replay_events
    from pal.pipeline.orchestrator import (
        ArmedSetup, OrchestratorConfig, PositionPlan, SessionOrchestrator)
    from pal.ledger.positions import AccountLedger, PositionLot
    from pal.signals.engine import EngineConfig
    from pal.portfolio.risk import PaperDefaults

    days = sorted({b.bar_start.date() for b in bars})
    cal = TradingCalendar(tuple(days), "paper-events")
    store = EventStore(os.path.join(out_dir, "events.jsonl"))
    prior = replay_events(store.events())
    is_fresh = len(store) == 0
    # R6-07：--snapshot 提供候选/日线/日历背景 → 与 backtest 同一
    # TradingRuntime 决策内核；缺省时保持纯事件驱动（无候选）。
    snap_dir = _arg(args, "--snapshot")
    # R6-07：日历优先取快照 manifest.trading_days（事件文件日期可能
    # 只是快照的子集——T+1 next_trading_day 查询会越界）
    if snap_dir is not None:
        _snap_man = json.load(open(
            os.path.join(snap_dir, "manifest.json"), encoding="utf-8"))
        _tds = _snap_man.get("trading_days") or []
        if _tds:
            cal = TradingCalendar(
                tuple(_date.fromisoformat(x) for x in _tds),
                _snap_man.get("calendar_version", "paper-snapshot"))

    ledger = AccountLedger(prior.initial_cash or 1_000_000.0)
    if not is_fresh:
        # V05：恢复现金（不重置资金）
        ledger.cash = prior.cash
        # R6-04：按 fill 逐笔重放 buy→lot + 卖出扣减 + 退出计划。
        # 每笔买入 = 一个独立 lot（fill_id 派生 lot_id），
        # 计划随 fill.plan 恢复并扣减已执行卖出量。
        all_fills = [e.payload for e in store.by_kind("fill")]
        sold_by_lot: dict = {}
        for f in all_fills:
            if f.get("side") == "sell":
                lid = f.get("lot_id", "")
                if lid:
                    sold_by_lot[lid] = sold_by_lot.get(lid, 0) + int(f["qty"])
        plans_by_iid: dict = {}
        for f in all_fills:
            if f.get("side") != "buy":
                continue
            iid = f["instrument_id"]
            qty = int(f["qty"])
            px = float(f["price"])
            comm = float(f.get("commission", 0.0))
            sf = _date.fromisoformat(f["sellable_from"])
            lot_id = f.get("lot_id") or f"lot_{iid}_{f['fill_id']}"
            sold = sold_by_lot.get(lot_id, 0)
            remaining = qty - sold
            if remaining > 0:
                ledger.positions.add_lot(PositionLot(
                    lot_id, iid, remaining, (qty * px + comm) / qty,
                    _date.fromisoformat(
                        f.get("plan", {}).get(
                            "entry_date", f["sellable_from"])), sf))
            plan_p = f.get("plan")
            if plan_p:
                plan = PositionPlan(
                    iid, plan_p["setup_id"], px,
                    float(plan_p["stop"]), float(plan_p["target"]),
                    _date.fromisoformat(plan_p["entry_date"]),
                    int(plan_p["qty"]), lot_id=lot_id)
                # 卖出已消耗部分从计划剩余量里扣
                plan.remaining_qty = max(0, int(plan_p["qty"]) - sold)
                if plan.remaining_qty > 0:
                    plans_by_iid.setdefault(iid, []).append(plan)
        # 无 lot_id 的旧格式卖出：按 FIFO 从最早 lot 扣
        for f in all_fills:
            if f.get("side") == "sell" and not f.get("lot_id"):
                iid = f["instrument_id"]
                rem = int(f["qty"])
                lots = ledger.positions._lots.get(iid, [])
                for lot in lots:
                    if rem <= 0:
                        break
                    take = min(lot.qty, rem)
                    lot.qty -= take
                    rem -= take
                ledger.positions._lots[iid] = [
                    l for l in lots if l.qty > 0]
        for iid, plans in plans_by_iid.items():
            if ledger.positions.total_qty(iid) > 0:
                pass    # orch 构造后统一注入（见下）

    orch = SessionOrchestrator(
        OrchestratorConfig(EngineConfig("paper-v1"), calendar=cal),
        ledger, store=store)
    if not is_fresh:
        pend = plans_by_iid
        for iid, plans in pend.items():
            existing = orch.position_plans.get(iid)
            if existing is None:
                orch.position_plans[iid] = plans
            elif isinstance(existing, list):
                existing.extend(plans)
            else:
                orch.position_plans[iid] = [existing] + plans
    # V04：恢复 consumed 游标（重复 bar 不报错、不重复消费）
    # R6-04：bar_consumed 携带完整 bar → 重建行情历史引用，
    # 使恢复后的引擎评估窗口与连续运行一致
    from pal.data.bars import Bar as _Bar
    hist_by_iid: dict = {}
    for e in store.by_kind("bar_consumed"):
        orch._consumed_bars.add(e.payload["bar_key"])
        b = e.payload.get("bar")
        if b:
            hist_by_iid.setdefault(b["instrument_id"], []).append(_Bar(
                b["instrument_id"], b["timeframe"],
                _dtm.fromisoformat(b["bar_start"]),
                _dtm.fromisoformat(b["bar_end"]),
                _dtm.fromisoformat(b["available_at"]),
                b["open"], b["high"], b["low"], b["close"],
                b["volume"], b.get("amount", 0.0),
                b.get("is_final", True)))
    # R6-04：恢复 armed/setup 状态（最后事件优先——被删除的 setup
    # 按 setup_removed 剔除）
    removed = {e.payload["setup_id"]
               for e in store.by_kind("setup_removed")}
    last_armed: dict = {}
    for e in store.by_kind("armed"):
        last_armed[e.payload["setup_id"]] = e.payload
    for sid, a in last_armed.items():
        if sid not in removed and sid not in orch.armed:
            orch.armed[sid] = ArmedSetup(
                sid, a["instrument_id"], a["family"],
                float(a["entry"]), float(a["stop"]), float(a["target"]),
                _dtm.fromisoformat(a["armed_at"]))

    n_new = 0
    new_events: list = []
    if snap_dir is not None and is_fresh:
        # 统一路径：TradingRuntime 处理同一事件文件（候选/日线来自快照）
        from pal.runtime.service import TradingRuntime
        snap_bars = _load_bars_file(events_fp)
        si = {"manifest": _load_snapshot(snap_dir)["manifest"],
              "bars": snap_bars,
              "daily": _load_snapshot(snap_dir)["daily"]}
        rt = TradingRuntime(si, 1_000_000.0, store=store,
                            engine_version="paper-v1")
        all_ev = rt.process_bars(snap_bars)
        n_new = len(all_ev)
        new_events = list(all_ev)
        ledger = rt.ledger
        orch = rt.orch
    else:
        # R6-07：--snapshot 时恢复态同样提供候选/日线背景——
        # 与 backtest 同一决策输入契约（缺省纯事件流保持原语义）
        snap_si = (_load_snapshot(snap_dir) if snap_dir is not None
                   else None)
        snap_daily: dict = {}
        if snap_si is not None:
            from pal.selection.providers import Candidate as _C
            for b in snap_si["daily"]:
                snap_daily.setdefault(b.instrument_id, []).append(b)

        def _cand_for(bar):
            if snap_si is None:
                return None
            man = snap_si["manifest"]
            if bar.instrument_id not in man.get("instruments", {}):
                return None
            at = _dtm.fromisoformat(
                bar.bar_start.date().isoformat() + "T00:00:00+08:00")
            return _C(f"cand_{bar.instrument_id.replace('.', '_')}"
                         f"_{bar.bar_start.date().isoformat()}",
                         bar.instrument_id, ("static_pool",), at, at, None)

        for bar in sorted(bars, key=lambda b: (b.available_at,
                                               b.bar_start)):
            hist = hist_by_iid.get(bar.instrument_id, [])
            ev = orch.on_bar(bar.instrument_id, bar, hist,
                             snap_daily.get(bar.instrument_id, []),
                             _cand_for(bar))
            n_new += len(ev)
            new_events.extend(ev)
            hist_by_iid.setdefault(bar.instrument_id, []).append(bar)
    traded = {e.payload["instrument_id"] for e in store.by_kind("fill")}
    ledger_snapshot = {
        "cash": round(ledger.cash, 4),
        "positions": {i: ledger.positions.total_qty(i)
                      for i in sorted(traded)},
    }
    with open(os.path.join(out_dir, "ledger_snapshot.json"), "w",
              encoding="utf-8") as f:
        json.dump(ledger_snapshot, f, ensure_ascii=False, indent=1)
    status = "OK" if n_new > 0 else "NO_TRADES"
    _write_status(out_dir, status, {
        "new_events": n_new, "new_event_list": new_events[:20],
        "recovered": (not is_fresh),
        "recovered_cash": (prior.cash if not is_fresh else None)})
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest_doc(run_id, "paper-v1",
                                {"manifest": {}, "input_hashes": {
                                    os.path.basename(events_fp):
                                        _sha256_file(events_fp)}},
                                status), f, ensure_ascii=False, indent=1)
    print(f"paper {status}: run={run_id} new_events={n_new} "
          f"cash={ledger.cash:.2f} "
          f"positions={ledger_snapshot['positions']} "
          f"{'(recovered)' if not is_fresh else ''}")
    print(f"  state  : {out_dir}")
    return EXIT_OK


def _cmd_report(args) -> int:
    run_dir = _arg(args, "--run")
    if not run_dir:
        print("usage: pal report --run DIR", file=sys.stderr)
        return EXIT_USAGE
    if not os.path.isfile(os.path.join(run_dir, "run_manifest.json")):
        print(f"ERROR: run 目录无 run_manifest.json: {run_dir}",
              file=sys.stderr)
        return EXIT_INVALID
    printed = False
    for name in (STATUS_FILE, "daily_plan.md", "backtest.json"):
        p = os.path.join(run_dir, name)
        if os.path.isfile(p):
            print(f"--- {name} ---")
            with open(p, encoding="utf-8") as f:
                print(f.read())
            printed = True
    if not printed:
        print("EMPTY: run 目录无可渲染产物")
        return EXIT_INVALID
    return EXIT_OK


def _cmd_reconcile(args) -> int:
    run_dir = _arg(args, "--run")
    if not run_dir:
        print("usage: pal reconcile --run DIR", file=sys.stderr)
        return EXIT_USAGE
    ev_path = os.path.join(run_dir, "events.jsonl")
    if not os.path.isfile(ev_path):
        print("BLOCKED: run 目录无 events.jsonl")
        return EXIT_BLOCKED
    from pal.pipeline.event_store import EventStore, replay_events
    es = EventStore(ev_path)
    st = replay_events(es.events())
    snap_path = os.path.join(run_dir, "ledger_snapshot.json")
    if not os.path.isfile(snap_path):
        print("BLOCKED: 无 ledger_snapshot.json 可比对")
        return EXIT_BLOCKED
    with open(snap_path, encoding="utf-8") as f:
        snap = json.load(f)
    ok, diffs = st.reconcile(snap.get("cash", 0.0),
                             snap.get("positions", {}))
    if ok:
        print("reconcile OK: 事件重放与账本快照一致 "
              f"(cash={snap.get('cash')}, positions={snap.get('positions')})")
        return EXIT_OK
    print("MISMATCH:")
    for d in diffs:
        print(f"  {d}")
    return EXIT_INVALID


def _cmd_version(_args) -> int:
    print(json.dumps({
        "commit": _git_commit(),
        "kernel": "SessionOrchestrator",
        "cli": "N03",
        "data_provider": DATA_PROVIDER_STATUS,
    }, ensure_ascii=False, indent=1))
    return EXIT_OK


def _arg(args, flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: doctor, scan, backtest, paper, report, "
              "reconcile, version")
        return EXIT_OK if not argv else EXIT_USAGE
    cmd, rest = argv[0], argv[1:]
    handlers = {
        "doctor": _doctor, "scan": _cmd_scan, "backtest": _cmd_backtest,
        "paper": _cmd_paper, "report": _cmd_report,
        "reconcile": _cmd_reconcile, "version": _cmd_version,
    }
    h = handlers.get(cmd)
    if h is None:
        print(f"unknown command: {cmd}（见 pal --help）", file=sys.stderr)
        return EXIT_USAGE
    return h(rest)


if __name__ == "__main__":
    sys.exit(main())
