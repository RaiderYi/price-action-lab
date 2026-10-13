"""AR11 验收：TradingRuntime 统一服务——各模式同内核。"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACK = os.path.join(ROOT, "tests", "fixtures", "acceptance_pack")


class TestUnifiedRuntime:
    def test_backtest_via_runtime_full_chain(self):
        """Runtime 服务跑验收包：全链 + 与 CLI 相同经济结果。"""
        from pal.runtime.service import TradingRuntime, load_snapshot
        si = load_snapshot(PACK)
        rt = TradingRuntime(si, 1_000_000.0)
        ev = rt.process_bars(si["bars"])
        chain = [e for e in ev if e.startswith(("ARMED:", "FILL:", "EXIT_"))]
        armed = [e for e in chain if e.startswith("ARMED:")]
        fills = [e for e in chain if e.startswith("FILL:")]
        exits = [e for e in chain if e.startswith("EXIT_")]
        assert len(armed) == 1 and len(fills) == 1 and len(exits) == 1
        assert fills[0].endswith(":8300@10.0")
        assert exits[0] == "EXIT_STOP:8300@8.5"
        # 与 CLI 同值（987476.3375）
        snap = rt.ledger_snapshot()
        assert abs(snap["cash"] - 987476.3375) < 0.01
        assert snap["positions"] == {"SSE.600519": 0}

    def test_chunked_equals_whole_via_runtime(self):
        """分块处理 = 整段处理（V03 语义在 Runtime 层同样成立）。"""
        from pal.runtime.service import TradingRuntime, load_snapshot
        si = load_snapshot(PACK)
        rt1 = TradingRuntime(si, 1_000_000.0)
        ev_whole = rt1.process_bars(si["bars"])
        rt2 = TradingRuntime(si, 1_000_000.0)
        ev_chunk = []
        by_day = {}
        for b in si["bars"]:
            by_day.setdefault(b.bar_start.date(), []).append(b)
        for d in sorted(by_day):
            ev_chunk += rt2.process_bars(by_day[d])
        assert ev_whole == ev_chunk
        assert abs(rt1.ledger.cash - rt2.ledger.cash) < 1e-9

    def test_runtime_respects_manifest_trading_days(self):
        """日历来自 manifest.trading_days（蓝图附录A 补充项）。"""
        from pal.runtime.service import TradingRuntime, load_snapshot
        si = load_snapshot(PACK)
        rt = TradingRuntime(si)
        assert len(rt.calendar.trading_days) == \
            len(si["manifest"]["trading_days"])

    def test_industry_mapping_wired(self):
        """AR08：manifest 行业映射注入主链。"""
        from pal.runtime.service import TradingRuntime, load_snapshot
        si = load_snapshot(PACK)
        rt = TradingRuntime(si)
        assert rt.orch._industries["SSE.600519"] == "consumer"
        assert rt.orch._industry_of("SSE.600519") == "consumer"

    def test_tampered_hash_rejected(self):
        """篡改快照 → Runtime 载入拒绝。"""
        import shutil
        from pal.runtime.service import load_snapshot, RuntimeError_
        with tempfile.TemporaryDirectory() as td:
            bad = os.path.join(td, "pack")
            shutil.copytree(PACK, bad)
            fp = os.path.join(bad, "bars_SSE_600519.jsonl")
            lines = open(fp, encoding="utf-8").readlines()
            d0 = json.loads(lines[0])
            for k in ("open", "high", "low", "close"):
                d0[k] += 0.01
            lines[0] = json.dumps(d0, ensure_ascii=False) + "\n"
            open(fp, "w", encoding="utf-8").writelines(lines)
            try:
                load_snapshot(bad)
                assert False, "篡改未拒绝"
            except RuntimeError_:
                pass
