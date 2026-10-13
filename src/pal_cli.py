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
    declared = manifest.get("file_sha256", {})
    for fn, h in declared.items():
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
    from datetime import date as _date
    from pal.data.calendar import TradingCalendar
    from pal.pipeline.orchestrator import (
        OrchestratorConfig,
        SessionOrchestrator,
    )
    from pal.ledger.positions import AccountLedger
    from pal.signals.engine import EngineConfig
    from pal.reporting.daily_plan import (
        DailyPlanEntry, render_daily_plan, write_outputs)

    cands = _candidates_from_snapshot(si)
    if not cands:
        _write_status(out_dir, "NO_CANDIDATES", {"reason": "快照无候选源"})
        print("NO_CANDIDATES: manifest.instruments 为空，策略未评估")
        return EXIT_NO_TRADES
    # N03：候选按交易日刷新（静态池每日产出，eligible=当日00:00）
    from datetime import datetime as _dtm, timedelta as _td
    from pal.selection.providers import Candidate as _Cand

    def _day_cands(d):
        at = _dtm.fromisoformat(d.isoformat() + "T00:00:00+08:00")
        return [_Cand(f"cand_{iid.replace('.', '_')}_{d.isoformat()}",
                      iid, ("static_pool",), at, at, None)
                for iid in si["manifest"].get("instruments", {})]

    days = sorted({b.bar_start.date() for b in si["bars"]})
    cal = TradingCalendar(tuple(days), si["manifest"].get(
        "calendar_version", "snapshot-derived"))
    by_day = {}
    for b in si["bars"]:
        by_day.setdefault(b.bar_start.date(), []).append(b)
    daily_by_iid = {}
    for b in si["daily"]:
        daily_by_iid.setdefault(b.instrument_id, []).append(b)

    cfg = OrchestratorConfig(EngineConfig("cli-scan-v1"), calendar=cal)
    orch = SessionOrchestrator(cfg, AccountLedger(1_000_000.0))
    history = {}
    evaluated = set()
    for d in sorted(by_day):
        day_c = _day_cands(d)
        for bar in sorted(by_day[d], key=lambda b: b.bar_start):
            cand = next((c for c in day_c
                         if c.instrument_id == bar.instrument_id
                         and c.eligible_from <= bar.available_at), None)
            hist = history.get(bar.instrument_id, [])
            orch.on_bar(bar.instrument_id, bar, hist,
                        daily_by_iid.get(bar.instrument_id, []),
                        cand)
            if cand is not None:
                evaluated.add(bar.instrument_id)
            history.setdefault(bar.instrument_id, []).append(bar)

    entries = []
    for iid in sorted(evaluated):
        if iid in [c for c, _ in orch.rejected_candidates]:
            entries.append(DailyPlanEntry(
                iid, iid, "rejected",
                [w for c, w in orch.rejected_candidates if c == iid], {}))
        elif any(s.instrument_id == iid for s in orch.armed.values()):
            entries.append(DailyPlanEntry(iid, iid, "awaiting_trigger",
                                          ["ARMED"], {}))
        else:
            entries.append(DailyPlanEntry(iid, iid, "watch",
                                          ["NO_SIGNAL"], {}))
    # A02：未评估的票不算 watch（区分"未评估"与"评估后无信号"）
    doc = render_daily_plan(
        plan_date=si["manifest"].get("asof_date", "unknown"),
        entries=entries, run_id=run_id, config_version="cli-scan-v1")
    write_outputs(doc, os.path.join(out_dir, "daily_plan.json"),
                  os.path.join(out_dir, "daily_plan.md"))
    has_signal = bool(orch.armed)
    status = "OK" if has_signal else "NO_SIGNAL"
    _write_status(out_dir, status, {
        "evaluated": sorted(evaluated),
        "not_evaluated": sorted(
            {b.instrument_id for b in si["bars"]} - evaluated),
        "armed": sorted(orch.armed)})
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest_doc(run_id, "cli-scan-v1", si, status), f,
                  ensure_ascii=False, indent=1)
    print(f"scan {status}: run={run_id} armed={len(orch.armed)} "
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
    from pal.selection.providers import Candidate as _Cand
    bt_days = []
    for d, bars in sorted(by_day.items()):
        at = _dtm.fromisoformat(d.isoformat() + "T00:00:00+08:00")
        day_cands = tuple(
            _Cand(f"cand_{iid.replace('.', '_')}_{d.isoformat()}",
                  iid, ("static_pool",), at, at, None)
            for iid in si["manifest"].get("instruments", {})
            if any(b.instrument_id == iid for b in bars))
        bt_days.append(BacktestDay(d, tuple(bars), tuple(si["daily"]),
                                   day_cands))

    # N09/N10：事件仓库+账本快照自产（reconcile 可直接运行）
    store = EventStore(os.path.join(out_dir, "events.jsonl"))
    cfg = OrchestratorConfig(EngineConfig("cli-backtest-v1"), calendar=cal)
    runner = BacktestRunner(cfg, 1_000_000.0)
    runner.orch = __import__("pal.pipeline.orchestrator",
                             fromlist=["SessionOrchestrator"]) \
        .SessionOrchestrator(cfg, runner.ledger, store=store)
    res = runner.run(bt_days)

    marks = {b.instrument_id: b.close for b in si["bars"]}
    traded = {e.payload["instrument_id"] for e in store.by_kind("fill")}
    ledger_snapshot = {
        "cash": round(runner.ledger.cash, 4),
        "positions": {iid: runner.ledger.positions.total_qty(iid)
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
        "n_days": len(bt_days),
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
    print(f"backtest {status}: run={run_id} days={len(bt_days)} "
          f"fills={n_fills} events={len(res.events)} "
          f"nav={nav_doc['final_nav']}")
    print(f"  events : {os.path.join(out_dir, 'events.jsonl')}")
    print(f"  ledger : {os.path.join(out_dir, 'ledger_snapshot.json')}")
    return EXIT_OK


def _cmd_paper(args) -> int:
    """N03：离线 paper——消费事件文件（bars JSONL），支持 --state 恢复。"""
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
    from datetime import date as _date
    from pal.data.calendar import TradingCalendar
    from pal.pipeline.event_store import EventStore
    from pal.pipeline.orchestrator import (
        OrchestratorConfig, SessionOrchestrator)
    from pal.ledger.positions import AccountLedger
    from pal.signals.engine import EngineConfig

    days = sorted({b.bar_start.date() for b in bars})
    cal = TradingCalendar(tuple(days), "paper-events")
    store = EventStore(os.path.join(out_dir, "events.jsonl"))
    # 恢复：重放已持久化事件重建账本状态
    from pal.pipeline.event_store import replay_events
    prior = replay_events(store.events())
    ledger = AccountLedger(1_000_000.0 if not prior.initial_cash
                           else prior.initial_cash)
    ledger.cash = prior.cash if store.events() else 1_000_000.0
    orch = SessionOrchestrator(
        OrchestratorConfig(EngineConfig("paper-v1"), calendar=cal),
        ledger, store=store)
    consumed_prior = len(store.by_kind("bar_consumed"))
    n_new = 0
    for bar in sorted(bars, key=lambda b: (b.available_at, b.bar_start)):
        ev = orch.on_bar(bar.instrument_id, bar, [], [], None)
        n_new += len(ev)
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
    _write_status(out_dir, status, {"new_events": n_new,
                                    "prior_bars": consumed_prior})
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest_doc(run_id, "paper-v1",
                                {"manifest": {}, "input_hashes": {
                                    os.path.basename(events_fp):
                                        _sha256_file(events_fp)}},
                                status), f, ensure_ascii=False, indent=1)
    print(f"paper {status}: run={run_id} new_events={n_new} "
          f"cash={ledger.cash:.2f} "
          f"positions={ledger_snapshot['positions']}")
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
