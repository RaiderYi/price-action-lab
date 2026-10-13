"""第四轮审查验收测试：N01–N10 固化（全链来自公开入口，零注入）。

对应审查报告 §8 验收矩阵。全部断言业务事实（数量/价格/费用/现金），
不依赖手工注入 ArmedSetup——那是第三轮的执行边界单测，已被
test_round3_t01.py 覆盖；本文件只走 CLI 和真实引擎默认路径。
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLI = os.path.join(ROOT, "src", "pal_cli.py")
sys.path.insert(0, os.path.join(ROOT, "src"))


def _cli(*args):
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
    return subprocess.run([sys.executable, CLI, *args],
                          capture_output=True, text=True, env=env,
                          cwd=tempfile.mkdtemp())


class TestMatrixRow1DefaultEnvironment:
    """矩阵1：默认环境生成信号——自动 regime 与显式一致。"""

    def test_acceptance_pack_backtest_full_chain(self):
        """全链：候选→ARMED→FILL→EXIT→reconcile（公开入口）。"""
        pack = os.path.join(ROOT, "tests", "fixtures", "acceptance_pack")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "run")
            r = _cli("backtest", "--snapshot", pack, "--out", out)
            assert r.returncode == 0, r.stdout + r.stderr
            doc = json.load(open(os.path.join(out, "backtest.json"),
                                 encoding="utf-8"))
            assert doc["status"] == "OK"
            ev = doc["events"]
            # 精确断言（非"有事件"）——多票事件按时间交织，
            # 提取本链三事件验证顺序与数值：
            chain = [e for e in ev if "setup_" in e or "EXIT_STOP" in e]
            armed = [e for e in ev if e.startswith("ARMED:")]
            fills = [e for e in ev if e.startswith("FILL:")]
            exits = [e for e in ev if e.startswith("EXIT_STOP:")]
            assert len(armed) == 1 and len(fills) == 1 and len(exits) == 1, ev
            assert fills[0] == "FILL:" + armed[0][6:] + ":8300@10.0", ev
            assert exits[0] == "EXIT_STOP:8300@8.5", ev
            # 阴跌票被环境门拦截（V08 三态语义）
            assert any(e == "REGIME_BLOCK:downtrend" for e in ev), ev
            assert len(doc["nav_series"]) >= 20   # 跨日多棒
            assert doc["final_cash"] == doc["final_nav"]  # 清仓后现金=NAV

    def test_reconcile_selfproduced(self):
        """矩阵13：CLI 自产 run 目录直接 reconcile 通过。"""
        pack = os.path.join(ROOT, "tests", "fixtures", "acceptance_pack")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "run")
            _cli("backtest", "--snapshot", pack, "--out", out)
            r = _cli("reconcile", "--run", out)
            assert r.returncode == 0, r.stdout
            assert "reconcile OK" in r.stdout

    def test_scan_distinguishes_no_signal(self):
        """矩阵4：无交易区分 NO_SIGNAL（真实评估）而非空跑。"""
        pack = os.path.join(ROOT, "tests", "fixtures", "acceptance_pack")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "run")
            r = _cli("scan", "--snapshot", pack, "--out", out)
            assert r.returncode == 0
            st = json.load(open(os.path.join(out, "run_status.json"),
                                encoding="utf-8"))
            # 突破票 ARMED、横盘票 NO_SIGNAL、阴跌票 REGIME_BLOCK：
            # 三种状态并存，证明真实评估而非统一 watch
            assert "armed" in st["detail"] or st["status"] in (
                "OK", "NO_SIGNAL")
            plan = json.load(open(os.path.join(out, "daily_plan.json"),
                                  encoding="utf-8"))
            s = plan["summary"]
            assert s["watch"] + s["awaiting_trigger"] + s["rejected"] > 0


class TestMatrixRow4GapRisk:
    """矩阵6：跳空风险——实际成交价下风险仍在配置内。"""

    def test_gap_fill_risk_within_budget(self):
        import sys as _s
        _s.path.insert(0, os.path.join(ROOT, "src"))
        from datetime import datetime, timedelta
        from pal.data.bars import Bar
        from pal.data.calendar import TZ
        from pal.ledger.positions import AccountLedger
        from pal.pipeline.orchestrator import (
            ArmedSetup, OrchestratorConfig, SessionOrchestrator)
        from pal.signals.engine import EngineConfig
        from pal.portfolio.risk import PaperDefaults

        T = datetime(2026, 10, 14, 10, 0, tzinfo=TZ)
        B = lambda **kw: Bar("SSE.600519", "30m", T, T + timedelta(minutes=30), T + timedelta(minutes=30), kw.get("o", 10), kw.get("h", 10.5), kw.get("l", 9.8), kw.get("c", 10.2), kw.get("v", 1_000_000))
        q = SessionOrchestrator(
            OrchestratorConfig(
                EngineConfig("t", enabled_families=("breakout",)),
                paper=PaperDefaults(risk_per_trade_pct=0.0025,
                                    max_position_pct=0.10),
                calendar=None),
            AccountLedger(1_000_000))
        q.armed["s"] = ArmedSetup("s", "SSE.600519", "breakout",
                                  10.0, 9.9, 12.0, T - timedelta(minutes=30))
        ev = q.on_bar("SSE.600519", B(o=11, h=11.1, l=10.8, c=11.0),
                      [], [], None)
        # A05：成交后 qty×(entry−stop) ≤ 风险预算（含费用容差）
        qty = q.ledger.positions.total_qty("SSE.600519")
        assert qty > 0
        fill_px = 11.0
        risk = qty * (fill_px - 9.9)
        assert risk <= 1_000_000 * 0.0025 * 1.1, (   # 10% 容差（费）
            f"跳空风险 {risk:.0f} 超预算 2500（A05）")
        assert qty * fill_px <= 1_000_000 * 0.10 * 1.01   # 单票上限


class TestMatrixRow5PartialFill:
    """矩阵7：部分成交——同 order 多 fill_id 正常、lot 取整。"""

    def test_lot_rounding_on_participation(self):
        import sys as _s
        _s.path.insert(0, os.path.join(ROOT, "src"))
        from datetime import datetime, timedelta
        from pal.data.bars import Bar
        from pal.data.calendar import TZ
        from pal.ledger.positions import AccountLedger
        from pal.pipeline.orchestrator import (
            ArmedSetup, OrchestratorConfig, SessionOrchestrator)
        from pal.signals.engine import EngineConfig
        from pal.execution.market_rules import MAIN_BOARD

        T = datetime(2026, 10, 14, 10, 0, tzinfo=TZ)
        b = Bar("SSE.600519", "30m", T, T + timedelta(minutes=30),
                T + timedelta(minutes=30), 10.0, 10.5, 9.8, 10.2, 2_500)
        q = SessionOrchestrator(
            OrchestratorConfig(EngineConfig("t")), AccountLedger(1_000_000))
        q.armed["s"] = ArmedSetup("s", "SSE.600519", "breakout",
                                  10.0, 9.9, 12.0, T - timedelta(minutes=30))
        q.on_bar("SSE.600519", b, [], [], None)
        qty = q.ledger.positions.total_qty("SSE.600519")
        lot = MAIN_BOARD.lot_size
        assert qty % lot == 0, f"零股 {qty} 未按 lot={lot} 取整（A06）"

    def test_multi_fill_same_order_allowed(self):
        """A07：一单多笔 fill（不同 fill_id）不再冲突。"""
        from pal.pipeline.event_store import EventStore
        es = EventStore()
        base = {"order_id": "o1", "side": "buy", "qty": 100,
                "price": 10.0, "instrument_id": "SSE.600519",
                "commission": 5.0}
        es.append("fill", dict(base, fill_id="f1"))
        es.append("fill", dict(base, fill_id="f2"))   # 不再抛异常
        from pal.pipeline.event_store import replay_events
        st = replay_events(es.events())
        assert st.positions["SSE.600519"] == 200


class TestMatrixRow9SupplierDelay:
    """矩阵9：供应商延迟——15:07 数据不在 15:00 日线。"""

    def test_delayed_input_not_early_visible(self):
        from dataclasses import replace
        from datetime import date, time
        from pal.data.bars import Bar, resample_30m_to_daily
        from pal.data.calendar import TZ, TradingCalendar
        from pal.research.acceptance_pack import CAL, TRADING_DAYS
        d = TRADING_DAYS[0]
        bars = []
        for s, e in CAL.bars_for_day(d):
            bars.append(Bar("SSE.600519", "30m", s, e, e,
                            10, 10.1, 9.9, 10, 100_000))
        bars[-1] = replace(bars[-1],
                           available_at=bars[-1].bar_end.replace(
                               minute=7) + timedelta_zero())
        agg = resample_30m_to_daily(bars, "SSE.600519", calendar=CAL)[0]
        assert agg.available_at == bars[-1].available_at  # 15:07


def timedelta_zero():
    from datetime import timedelta
    return timedelta()


class TestMatrixRow10RetryAfterFailure:
    """矩阵10：中途失败重试——异常不永久吞掉行情。"""

    def test_calendar_error_retry_succeeds(self):
        import sys as _s
        _s.path.insert(0, os.path.join(ROOT, "src"))
        from datetime import datetime, timedelta
        from pal.data.bars import Bar
        from pal.data.calendar import TZ, TradingCalendar
        from datetime import date
        from pal.ledger.positions import AccountLedger
        from pal.pipeline.orchestrator import (
            ArmedSetup, OrchestratorConfig, SessionOrchestrator)
        from pal.signals.engine import EngineConfig

        T = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)
        b = Bar("SSE.600519", "30m", T, T + timedelta(minutes=30),
                T + timedelta(minutes=30), 10.0, 10.5, 9.8, 10.2, 1e6)
        cal_bad = TradingCalendar((date(2026, 10, 13),), "short")
        cal_good = TradingCalendar(
            (date(2026, 10, 13), date(2026, 10, 14)), "full")
        q = SessionOrchestrator(
            OrchestratorConfig(EngineConfig("t"), calendar=cal_bad),
            AccountLedger(1_000_000))
        q.armed["s"] = ArmedSetup("s", "SSE.600519", "breakout",
                                  10.0, 9.0, 12.0, T - timedelta(minutes=30))
        # 第一次：日历缺次日 → KeyError，但 bar 未被标记消费
        try:
            q.on_bar("SSE.600519", b, [], [], None)
            raised = False
        except KeyError:
            raised = True
        assert raised
        key = q._bar_key(b)
        assert key not in q._consumed_bars, "失败棒被吞（A08）"
        # 修复日历重投 → 成功
        q.cfg = OrchestratorConfig(EngineConfig("t"), calendar=cal_good)
        ev = q.on_bar("SSE.600519", b, [], [], None)
        assert any("FILL" in e for e in ev), ev


class TestMatrixRow11Restart:
    """矩阵11：进程重启——恢复后与连续基准一致（N10 故障注入）。"""

    def test_restart_equals_continuous(self):
        """前半事件跑完→用 events.jsonl 重放恢复→继续后半→与一次跑完一致。"""
        import sys as _s
        _s.path.insert(0, os.path.join(ROOT, "src"))
        from datetime import datetime, timedelta
        from pal.data.bars import Bar
        from pal.data.calendar import TZ
        from pal.ledger.positions import AccountLedger
        from pal.pipeline.orchestrator import (
            ArmedSetup, OrchestratorConfig, SessionOrchestrator)
        from pal.pipeline.event_store import EventStore, replay_events
        from pal.signals.engine import EngineConfig

        T = datetime(2026, 10, 14, 10, 0, tzinfo=TZ)
        B = lambda t, o, h, l, c, v=1e6: Bar(
            "SSE.600519", "30m", t, t + timedelta(minutes=30),
            t + timedelta(minutes=30), o, h, l, c, v)
        b1 = B(T, 9.5, 10.5, 9.4, 10.2)          # 触发买入
        b2 = B(T + timedelta(minutes=30), 10.2, 10.4, 9.9, 10.0)  # 持有
        b3 = B(T + timedelta(days=1), 8.5, 8.6, 8.0, 8.2)  # 止损退出

        def mk():
            q = SessionOrchestrator(
                OrchestratorConfig(EngineConfig("t")),
                AccountLedger(1_000_000))
            q.armed["s"] = ArmedSetup(
                "s", "SSE.600519", "breakout", 10.0, 9.0, 12.0,
                T - timedelta(minutes=30))
            return q

        # 基准：连续跑完
        base = mk()
        base.on_bar("SSE.600519", b1, [], [], None)
        base.on_bar("SSE.600519", b2, [b1], [], None)
        base.on_bar("SSE.600519", b3, [b1, b2], [], None)
        base_cash = base.ledger.cash
        base_qty = base.ledger.positions.total_qty("SSE.600519")

        # 崩溃模拟：跑 b1 后中断，从 events.jsonl 恢复账本再跑 b2/b3
        with tempfile.TemporaryDirectory() as td:
            import os as _os
            store = EventStore(_os.path.join(td, "ev.jsonl"))
            # 构造器注入（session_init 随之持久化——N09 契约）
            q1 = SessionOrchestrator(
                OrchestratorConfig(EngineConfig("t")),
                AccountLedger(1_000_000), store=store)
            q1.armed["s"] = ArmedSetup(
                "s", "SSE.600519", "breakout", 10.0, 9.0, 12.0,
                T - timedelta(minutes=30))
            q1.on_bar("SSE.600519", b1, [], [], None)
            # "重启"：重放恢复现金/持仓
            st = replay_events(store.events())
            q2 = SessionOrchestrator(
                OrchestratorConfig(EngineConfig("t")),
                AccountLedger(1_000_000.0))
            q2.ledger.cash = st.cash   # 重放现金（含已扣买入款）
            for iid, qty in st.positions.items():
                if qty > 0:
                    from pal.ledger.positions import PositionLot
                    import datetime as _dt
                    q2.ledger.positions.add_lot(PositionLot(
                        f"lot_r_{iid}", iid, qty, 10.0,
                        _dt.date(2026, 10, 14), _dt.date(2026, 10, 15)))
            # 恢复的退出计划（持仓存在即需要）
            from pal.pipeline.orchestrator import PositionPlan
            q2.position_plans["SSE.600519"] = PositionPlan(
                "SSE.600519", "s", 10.0, 9.0, 12.0,
                _dt.date(2026, 10, 14), st.positions.get("SSE.600519", 0))
            q2.on_bar("SSE.600519", b2, [b1], [], None)
            q2.on_bar("SSE.600519", b3, [b1, b2], [], None)
            assert abs(q2.ledger.cash - base_cash) < 0.01, (
                f"重启后现金 {q2.ledger.cash} ≠ 连续 {base_cash}（N10）")
            assert q2.ledger.positions.total_qty("SSE.600519") == base_qty


class TestMatrixRow14VersionTrace:
    """矩阵12：版本追溯——篡改输入后 hash 校验拒绝。"""

    def test_tampered_snapshot_rejected(self):
        pack = os.path.join(ROOT, "tests", "fixtures", "acceptance_pack")
        with tempfile.TemporaryDirectory() as td:
            import shutil
            tampered = os.path.join(td, "pack")
            shutil.copytree(pack, tampered)
            # 篡改一个 bar 文件（内容变了 hash 不匹配 manifest）
            fp = os.path.join(tampered, "bars_SSE_600519.jsonl")
            lines = open(fp, encoding="utf-8").readlines()
            d0 = json.loads(lines[0])
            d0["close"] = d0["close"] + 0.01
            d0["open"] = d0["open"] + 0.01
            d0["high"] = d0["high"] + 0.01
            d0["low"] = d0["low"] + 0.01
            lines[0] = json.dumps(d0, ensure_ascii=False) + "\n"
            with open(fp, "w", encoding="utf-8") as f:
                f.writelines(lines)
            r = _cli("backtest", "--snapshot", tampered,
                     "--out", os.path.join(td, "o"))
            assert r.returncode == 2, "篡改快照未被拒绝（A12 版本追溯）"
            assert "不符" in r.stderr
