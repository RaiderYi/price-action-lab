"""第三轮复审 T12：统一 CLI 验收。

验收点（复审）：
- 干净环境按命令完成数据→报告（scan/backtest 走 --snapshot 冻结快照）；
- 每个结果含 run_id、commit、config 版本；
- 无行情、无候选、无交易、失败各有不同状态与退出码；
- 不用写 Python 拼对象即可日常使用。
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime, time, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLI = os.path.join(ROOT, "src", "pal_cli.py")
TZ = timezone(timedelta(hours=8))

SLOTS = [(time(9, 30), time(10, 0)), (time(10, 0), time(10, 30)),
         (time(10, 30), time(11, 0)), (time(11, 0), time(11, 30)),
         (time(13, 0), time(13, 30)), (time(13, 30), time(14, 0)),
         (time(14, 0), time(14, 30)), (time(14, 30), time(15, 0))]


def _run_cli(*args, cwd=None):
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
    return subprocess.run(
        [sys.executable, CLI, *args], capture_output=True, text=True,
        env=env, cwd=cwd or tempfile.mkdtemp())


def _make_snapshot(td: str, days=(date(2026, 10, 12),)):
    snap = os.path.join(td, "snap")
    os.makedirs(snap)
    lines = []
    for d in days:
        for i, (st, en) in enumerate(SLOTS):
            s = datetime.combine(d, st, tzinfo=TZ)
            e = datetime.combine(d, en, tzinfo=TZ)
            px = 10 + i * 0.1
            lines.append(json.dumps({
                "instrument_id": "SSE.600519", "timeframe": "30m",
                "bar_start": s.isoformat(), "bar_end": e.isoformat(),
                "available_at": e.isoformat(),
                "open": px, "high": px + 0.15, "low": px - 0.2,
                "close": px + 0.05, "volume": 1_000_000}))
    with open(os.path.join(snap, "bars_main.jsonl"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(os.path.join(snap, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"asof_date": days[-1].isoformat(),
                   "snapshot_id": "t12"}, f, ensure_ascii=False)
    return snap


class TestDoctorAndVersion:
    def test_doctor_exit_0(self):
        r = _run_cli("doctor")
        assert r.returncode == 0
        assert "OK" in r.stdout

    def test_version_has_commit_and_kernel(self):
        r = _run_cli("version")
        assert r.returncode == 0
        doc = json.loads(r.stdout)
        assert doc["kernel"] == "SessionOrchestrator"
        assert doc["commit"]
        assert doc["data_provider"]["status"] == "BLOCKED"

    def test_unknown_command_exit_usage(self):
        assert _run_cli("bogus").returncode == 1

    def test_no_args_shows_help(self):
        r = _run_cli()
        assert "commands:" in r.stdout


class TestScan:
    def test_scan_produces_run_manifest_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            snap = _make_snapshot(td)
            out = os.path.join(td, "runs_out")
            r = _run_cli("scan", "--snapshot", snap, "--out", out)
            assert r.returncode == 0, r.stdout + r.stderr
            mf = json.load(open(os.path.join(out, "run_manifest.json"),
                                encoding="utf-8"))
            assert mf["run_id"].startswith("run_")
            assert mf["commit"]
            assert mf["kernel"] == "SessionOrchestrator"
            plan = json.load(open(os.path.join(out, "daily_plan.json"),
                                  encoding="utf-8"))
            assert plan["schema"] == "daily_plan/v1"
            assert os.path.isfile(os.path.join(out, "daily_plan.md"))

    def test_scan_missing_manifest_exit_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            r = _run_cli("scan", "--snapshot", td)
            assert r.returncode == 2

    def test_scan_no_bars_exit_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "snap")
            os.makedirs(snap)
            with open(os.path.join(snap, "manifest.json"), "w") as f:
                json.dump({"asof_date": "2026-10-13"}, f)
            r = _run_cli("scan", "--snapshot", snap)
            assert r.returncode == 3      # BLOCKED 不算失败也不算成功


class TestBacktest:
    def test_backtest_same_kernel_with_versions(self):
        with tempfile.TemporaryDirectory() as td:
            snap = _make_snapshot(td, days=(date(2026, 10, 12),
                                            date(2026, 10, 13)))
            out = os.path.join(td, "bt_out")
            r = _run_cli("backtest", "--snapshot", snap, "--out", out)
            assert r.returncode == 0, r.stdout + r.stderr
            doc = json.load(open(os.path.join(out, "backtest.json"),
                                 encoding="utf-8"))
            assert doc["schema"] == "backtest/v1"
            assert doc["n_days"] == 2
            assert len(doc["nav_series"]) == 16
            assert "不构成收益证据" in doc["caveat"]

    def test_backtest_runs_from_any_directory(self):
        """仓库外任意目录可运行（不依赖 cwd）。"""
        with tempfile.TemporaryDirectory() as td:
            snap = _make_snapshot(td)
            out = os.path.join(td, "o")
            r = _run_cli("backtest", "--snapshot", snap, "--out", out,
                         cwd=td)
            assert r.returncode == 0
            assert os.path.isfile(os.path.join(out, "backtest.json"))


class TestPaperAndReconcile:
    def test_paper_blocked_external_dependency(self):
        r = _run_cli("paper")
        assert r.returncode == 3
        assert "BLOCKED" in r.stdout

    def test_reconcile_without_events_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "run1"))
            r = _run_cli("reconcile", "--run", os.path.join(td, "run1"))
            assert r.returncode == 3


class TestReport:
    def test_report_renders_existing_run(self):
        with tempfile.TemporaryDirectory() as td:
            snap = _make_snapshot(td)
            out = os.path.join(td, "runs_out")
            _run_cli("scan", "--snapshot", snap, "--out", out)
            r = _run_cli("report", "--run", out)
            assert r.returncode == 0
            assert "daily_plan.md" in r.stdout or "每日选股计划" in r.stdout

    def test_report_missing_run_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            r = _run_cli("report", "--run", os.path.join(td, "nope"))
            assert r.returncode == 2
