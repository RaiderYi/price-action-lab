"""第三轮复审 T09：backtest=paper 同内核验收。"""
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.pipeline.orchestrator import (
    ArmedSetup,
    OrchestratorConfig,
    SessionOrchestrator,
)
from pal.ledger.positions import AccountLedger
from pal.research.backtest_runner import BacktestDay, BacktestRunner
from pal.selection.providers import Candidate
from pal.signals.engine import EngineConfig

IID = "SSE.600519"
CAL_DAYS = (date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 13))
from pal.data.calendar import TradingCalendar
CAL = TradingCalendar(CAL_DAYS, "t09-cal")


def bar30(d, i, o, h, l, c, v=1_000_000, iid=IID):
    slots = CAL.bars_for_day(d)
    s, e = slots[i]
    return Bar(iid, "30m", s, e, e, o, max(h, o, c), min(l, o, c), c, v)


def mk_cand(iid, eligible):
    return Candidate(
        candidate_id=f"cand_{iid.replace('.', '_')}", instrument_id=iid,
        source_models=("static_pool",),
        available_at=eligible - timedelta(hours=12),
        eligible_from=eligible, estimate=None)


class TestSameKernelBacktestPaper:
    def test_backtest_uses_session_orchestrator(self):
        """回放器内部就是同一 orchestrator（无独立交易路径）。"""
        cfg = OrchestratorConfig(EngineConfig("t09"), calendar=CAL)
        runner = BacktestRunner(cfg, 1_000_000.0)
        assert isinstance(runner.orch, SessionOrchestrator)

    def test_deterministic_replay_same_result(self):
        """同一冻结输入两次运行 → NAV/事件/现金完全一致。"""
        cfg = OrchestratorConfig(EngineConfig("t09"), calendar=CAL)

        def build_days():
            d1 = date(2026, 10, 9)
            cand = mk_cand(IID, datetime.combine(d1, time(9, 30), tzinfo=TZ))
            return [
                BacktestDay(d1, tuple(bar30(d1, i, 10 + i * 0.1,
                                            10 + i * 0.1 + 0.15,
                                            10 + i * 0.1 - 0.2,
                                            10 + i * 0.1 + 0.05)
                                      for i in range(8)),
                            candidates=(cand,)),
                BacktestDay(date(2026, 10, 12),
                            tuple(bar30(date(2026, 10, 12), i,
                                        11 + i * 0.1, 11 + i * 0.1 + 0.15,
                                        11 + i * 0.1 - 0.3,
                                        11 + i * 0.1 - 0.1)
                                  for i in range(8))),
            ]

        r1 = BacktestRunner(cfg, 1_000_000.0).run(build_days())
        r2 = BacktestRunner(cfg, 1_000_000.0).run(build_days())
        assert r1.nav_series == r2.nav_series
        assert r1.events == r2.events
        assert r1.final_cash == r2.final_cash
        assert r1.final_nav == r2.final_nav

    def test_bar_replay_after_completion_changes_nothing(self):
        """完成后重放全部 bar（模拟断点重传）→ 状态不变。"""
        cfg = OrchestratorConfig(EngineConfig("t09"), calendar=CAL)
        d1 = date(2026, 10, 9)
        cand = mk_cand(IID, datetime.combine(d1, time(9, 30), tzinfo=TZ))
        days = [BacktestDay(d1, tuple(bar30(d1, i, 10 + i * 0.1,
                                            10 + i * 0.1 + 0.15,
                                            10 + i * 0.1 - 0.2,
                                            10 + i * 0.1 + 0.05)
                                      for i in range(8)),
                            candidates=(cand,))]
        runner = BacktestRunner(cfg, 1_000_000.0)
        r1 = runner.run(days)
        # 再次整批投递（幂等）
        r2 = runner.run(days)
        assert r2.events == []          # 无新事件
        assert len(r2.nav_series) == 0  # 无新增 NAV
        assert runner.ledger.cash == r1.final_cash

    def test_open_position_marked_not_force_closed(self):
        """期末未平仓 → 估值标记（不虚构成交）。"""
        cfg = OrchestratorConfig(EngineConfig("t09"), calendar=CAL)
        runner = BacktestRunner(cfg, 1_000_000.0)
        d1 = date(2026, 10, 9)
        # 手工武装一个 setup，让第2根棒触发成交后不再退出
        runner.orch.armed["s1"] = ArmedSetup(
            "s1", IID, "breakout", entry=10.0, stop=8.0, target=15.0,
            armed_at=datetime.combine(d1, time(9, 30), tzinfo=TZ))
        bars = tuple(bar30(d1, i, 10 + i * 0.1, 10 + i * 0.1 + 0.3,
                           10 + i * 0.1 - 0.2, 10 + i * 0.1)
                     for i in range(8))
        res = runner.run([BacktestDay(d1, bars)])
        assert any("FILL" in e for e in res.events)
        assert IID in res.open_position_marks
        qty, mark = res.open_position_marks[IID]
        assert qty > 0
        assert mark == bars[-1].close    # 最后收盘估值
        # NAV = cash + qty×mark（有写入路径）
        expected_nav = res.final_cash + qty * mark
        assert res.final_nav == pytest.approx(expected_nav)

    def test_nav_series_written(self):
        """nav_series 非空且时间递增（复审：不再有无写入的 nav_series）。"""
        cfg = OrchestratorConfig(EngineConfig("t09"), calendar=CAL)
        d1 = date(2026, 10, 9)
        bars = tuple(bar30(d1, i, 10, 10.2, 9.8, 10.0) for i in range(8))
        res = BacktestRunner(cfg, 1_000_000.0).run([BacktestDay(d1, bars)])
        assert len(res.nav_series) == 8
        ts = [t for t, _ in res.nav_series]
        assert ts == sorted(ts)
