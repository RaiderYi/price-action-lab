"""pal CLI entrypoint（S0-03 最小 → T12 统一命令族）。

命令（T12 验收：业务能力不可省略，具体语法可调）：
    pal doctor              环境+模块自检（退出码 0/2）
    pal scan --snapshot D   盘后扫描：候选→准入/待触发/观察/拒绝 日报
    pal backtest --snapshot D [--out D]   历史回放（同一内核）
    pal paper --events F [--state D]      模拟运行（同一内核+事件仓库）
    pal report --run D      从 run 目录渲染日报（JSON+MD）
    pal reconcile --run D   对账：事件重放 vs 在线账本
    pal version             版本/内核指纹

所有命令共测同一原则：无行情/无候选/无交易/失败各有不同状态与退出码；
结果带 run_id、commit、config/calendar 版本（T12 验收）。
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

# -- pal 包定位（支持仓库外运行） --
_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_INVALID = 2      # 数据/状态无效
EXIT_BLOCKED = 3      # 外部依赖缺失（显式 BLOCKED，不算失败也不算成功）


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


def _manifest(run_id: str, config_version: str) -> dict:
    """run 清单（T12：commit/config 版本随产物）。"""
    return {
        "run_id": run_id,
        "created_at": _now_iso(),
        "commit": _git_commit(),
        "config_version": config_version,
        "kernel": "SessionOrchestrator",
    }


LEGACY_MODULES = [
    "bar_counting_detector",
    "focus_config",
    "market_analyzer",
    "signal_predictor",
    "signal_registry",
    "strict_breakout_strength",
    "strict_pa_detector",
    "strict_pa_qualification",
    "strict_pa_actionability",
    "system_price_builder",
]

KNOWN_OPTIONAL = ["kb_rules", "brooks_ontology_registry", "rule_guardrail"]


def _doctor(_args=None) -> int:
    import platform

    print(f"python: {platform.python_version()}")
    print("--- core modules ---")
    failed = []
    for m in LEGACY_MODULES:
        try:
            importlib.import_module(m)
            print(f"  ok   {m}")
        except Exception as e:  # noqa: BLE001
            failed.append(m)
            print(f"  FAIL {m}: {type(e).__name__}: {e}")
    print("--- optional external modules (absence = capability disabled, not error) ---")
    for m in KNOWN_OPTIONAL:
        try:
            importlib.import_module(m)
            print(f"  present {m}")
        except ImportError:
            print(f"  absent  {m} (capability disabled)")
    print("--- pal kernel modules ---")
    kernel = ["pal.pipeline.orchestrator", "pal.portfolio.allocator",
              "pal.pipeline.event_store", "pal.research.backtest_runner",
              "pal.reporting.daily_plan"]
    for m in kernel:
        try:
            importlib.import_module(m)
            print(f"  ok   {m}")
        except Exception as e:  # noqa: BLE001
            failed.append(m)
            print(f"  FAIL {m}: {type(e).__name__}: {e}")
    print("--- result ---")
    if failed:
        print(f"INVALID: {len(failed)} core module(s) failed to import: {failed}")
        return EXIT_INVALID
    print("OK: all core modules import; optional gaps reported above")
    return EXIT_OK


# ═══════════════════════════════════════════════════════════
# T10 之前：数据源能力显式登记（不伪装可拉取）
# ═══════════════════════════快────────══════════════════════════

DATA_PROVIDER_STATUS = {
    "provider": "none",
    "status": "BLOCKED",
    "reason": "真实行情 provider 未接入（T10 外部依赖：数据来源/权限/费用未定）",
    "capability": "scan/backtest/paper 需 --snapshot 指向已冻结快照目录",
}


def _load_snapshot(path: str) -> dict:
    """读取冻结快照目录（data snapshot manifest + bars JSONL）。"""
    mf = os.path.join(path, "manifest.json")
    if not os.path.isfile(mf):
        print(f"ERROR: 快照缺 manifest.json: {path}", file=sys.stderr)
        raise SystemExit(EXIT_INVALID)
    with open(mf, encoding="utf-8") as f:
        manifest = json.load(f)
    return manifest


def _load_bars_file(fp: str):
    from pal.data.bars import Bar

    bars = []
    with open(fp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            from datetime import datetime as _dt
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


# ═══════════════════════════════════════════════════════════
# 命令实现
# ═══════════════════════════════════════════════════════════

def _cmd_scan(args) -> int:
    """盘后扫描：snapshot → 决策 → 日报（T12+T08 产物目录）。"""
    import glob as _glob
    from pal.pipeline.orchestrator import (
        OrchestratorConfig,
        SessionOrchestrator,
    )
    from pal.ledger.positions import AccountLedger
    from pal.signals.engine import EngineConfig
    from pal.reporting.daily_plan import (
        DailyPlanEntry,
        render_daily_plan,
        write_outputs,
    )

    snap = _arg(args, "--snapshot")
    if not snap:
        print("usage: pal scan --snapshot DIR [--out DIR]", file=sys.stderr)
        return EXIT_USAGE
    manifest = _load_snapshot(snap)
    run_id = _run_id()
    out_dir = _arg(args, "--out") or os.path.join("runs", run_id)
    os.makedirs(out_dir, exist_ok=True)

    bars_files = sorted(_glob.glob(os.path.join(snap, "bars_*.jsonl")))
    if not bars_files:
        print("BLOCKED: 快照无 bars_*.jsonl（无行情不能扫描，不用伪数据）")
        return EXIT_BLOCKED

    cfg = OrchestratorConfig(EngineConfig("cli-scan-v1"))
    orch = SessionOrchestrator(cfg, AccountLedger(1_000_000.0))
    iids = set()
    for fp in bars_files:
        for b in _load_bars_file(fp):
            orch.on_bar(b.instrument_id, b, [b], [], candidate=None)
            iids.add(b.instrument_id)

    entries = []
    for iid in sorted(iids):
        # 从决策日志投影四类目（无候选日=观察）
        rejected = [(c, w) for c, w in orch.rejected_candidates
                    if iid in c] if orch.rejected_candidates else []
        if any(iid in c for c, _ in orch.rejected_candidates):
            entries.append(DailyPlanEntry(
                iid, iid, "rejected",
                [w for c, w in orch.rejected_candidates if iid in c], {}))
        elif any(s.instrument_id == iid for s in orch.armed.values()):
            entries.append(DailyPlanEntry(
                iid, iid, "awaiting_trigger",
                ["ARMED"], {}))
        else:
            entries.append(DailyPlanEntry(iid, iid, "watch", ["NO_SIGNAL"], {}))

    doc = render_daily_plan(
        plan_date=manifest.get("asof_date", "unknown"), entries=entries,
        run_id=run_id, config_version="cli-scan-v1")
    json_path = os.path.join(out_dir, "daily_plan.json")
    md_path = os.path.join(out_dir, "daily_plan.md")
    write_outputs(doc, json_path, md_path)
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest(run_id, "cli-scan-v1"), f, ensure_ascii=False,
                  indent=1)
    s = doc["summary"]
    print(f"scan OK: run={run_id} 准入{s['admitted']} 待触发"
          f"{s['awaiting_trigger']} 观察{s['watch']} 拒绝{s['rejected']}")
    print(f"  report: {json_path}")
    print(f"  report: {md_path}")
    return EXIT_OK


def _cmd_backtest(args) -> int:
    snap = _arg(args, "--snapshot")
    if not snap:
        print("usage: pal backtest --snapshot DIR [--out DIR]",
              file=sys.stderr)
        return EXIT_USAGE
    manifest = _load_snapshot(snap)
    run_id = _run_id()
    out_dir = _arg(args, "--out") or os.path.join("runs", run_id)
    os.makedirs(out_dir, exist_ok=True)

    import glob as _glob
    from datetime import date as _date
    from pal.data.calendar import TradingCalendar
    from pal.pipeline.orchestrator import OrchestratorConfig
    from pal.research.backtest_runner import BacktestDay, BacktestRunner
    from pal.signals.engine import EngineConfig

    bars = []
    for fp in sorted(_glob.glob(os.path.join(snap, "bars_*.jsonl"))):
        bars += _load_bars_file(fp)
    if not bars:
        print("BLOCKED: 快照无行情（回测不用伪数据）")
        return EXIT_BLOCKED

    days = sorted({b.bar_start.date() for b in bars})
    cal = TradingCalendar(tuple(days), manifest.get("calendar_version",
                                                   "snapshot-derived"))
    by_day = {}
    for b in bars:
        by_day.setdefault(b.bar_start.date(), []).append(b)
    bt_days = [BacktestDay(d, tuple(v)) for d, v in sorted(by_day.items())]

    cfg = OrchestratorConfig(EngineConfig("cli-backtest-v1"), calendar=cal)
    runner = BacktestRunner(cfg, 1_000_000.0)
    res = runner.run(bt_days)

    nav_doc = {
        "schema": "backtest/v1",
        "run_id": run_id,
        "n_days": len(bt_days),
        "n_events": len(res.events),
        "final_cash": round(res.final_cash, 2),
        "final_nav": round(res.final_nav, 2) if res.final_nav else None,
        "open_positions_marked": {
            k: [v[0], v[1]] for k, v in res.open_position_marks.items()},
        "nav_series": [[t.isoformat(), round(v, 2)]
                       for t, v in res.nav_series],
        "events": res.events,
        "caveat": "合成/快照数据；不构成收益证据（M4 需真实数据+预注册）",
    }
    out_json = os.path.join(out_dir, "backtest.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(nav_doc, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "run_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(_manifest(run_id, "cli-backtest-v1"), f, ensure_ascii=False,
                  indent=1)
    print(f"backtest OK: run={run_id} days={len(bt_days)} "
          f"events={len(res.events)} final_nav={nav_doc['final_nav']}")
    print(f"  report: {out_json}")
    return EXIT_OK


def _cmd_paper(args) -> int:
    print("paper: BLOCKED —— 需要实时行情事件流（T10 外部依赖）")
    print("  已交付内核与事件仓库：pal.pipeline.event_store + "
          "SessionOrchestrator（同一内核）")
    return EXIT_BLOCKED


def _cmd_report(args) -> int:
    run_dir = _arg(args, "--run")
    if not run_dir:
        print("usage: pal report --run DIR", file=sys.stderr)
        return EXIT_USAGE
    mf = os.path.join(run_dir, "run_manifest.json")
    if not os.path.isfile(mf):
        print(f"ERROR: run 目录无 run_manifest.json: {run_dir}",
              file=sys.stderr)
        return EXIT_INVALID
    printed = False
    for name in ("daily_plan.md", "backtest.json"):
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
        print(f"BLOCKED: run 目录无 events.jsonl（scan 模式不产生交易事件）")
        return EXIT_BLOCKED
    from pal.pipeline.event_store import EventStore, replay_events
    es = EventStore(ev_path)
    st = replay_events(es.events())
    # 在线账本快照（若存在）
    snap_path = os.path.join(run_dir, "ledger_snapshot.json")
    if not os.path.isfile(snap_path):
        print("BLOCKED: 无 ledger_snapshot.json 可比对")
        return EXIT_BLOCKED
    with open(snap_path, encoding="utf-8") as f:
        snap = json.load(f)
    ok, diffs = st.reconcile(snap.get("cash", 0.0),
                             snap.get("positions", {}))
    if ok:
        print("reconcile OK: 事件重放与账本快照一致")
        return EXIT_OK
    print("MISMATCH:")
    for d in diffs:
        print(f"  {d}")
    return EXIT_INVALID


def _cmd_version(_args) -> int:
    from pal.signals.engine import EngineConfig
    print(json.dumps({
        "commit": _git_commit(),
        "kernel": "SessionOrchestrator",
        "cli": "T12",
        "data_provider": DATA_PROVIDER_STATUS,
    }, ensure_ascii=False, indent=1))
    return EXIT_OK


def _arg(args, flag) -> "str | None":
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
        "doctor": _doctor,
        "scan": _cmd_scan,
        "backtest": _cmd_backtest,
        "paper": _cmd_paper,
        "report": _cmd_report,
        "reconcile": _cmd_reconcile,
        "version": _cmd_version,
    }
    h = handlers.get(cmd)
    if h is None:
        print(f"unknown command: {cmd}（见 pal --help）", file=sys.stderr)
        return EXIT_USAGE
    return h(rest)


if __name__ == "__main__":
    sys.exit(main())
