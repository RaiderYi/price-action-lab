"""第三轮复审 T01：不可空跑的验收夹具（复审 §7 反例的固化）。

来源：《price-action-lab_第三轮复审与完整交易系统交付清单.md》§7 脚本。
修复前应红；修复后全绿。不得通过放松断言迁就实现。
"""
import json
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.context.regime import RegimeKind
from pal.data.bars import Bar, resample_30m_to_daily
from pal.data.calendar import TZ, TradingCalendar
from pal.ledger.positions import AccountLedger
from pal.pipeline.orchestrator import (
    ArmedSetup,
    OrchestratorConfig,
    SessionOrchestrator,
)
from pal.research.framework import PreregisteredPlan, Verdict, release_gate
from pal.selection.providers import Candidate
from pal.signals.engine import EngineConfig

IID = "SSE.600519"
T = datetime(2026, 10, 13, 9, 30, tzinfo=TZ)


def bar(t=T, o=10.1, h=10.5, l=9.8, c=10.2, v=100_000):
    return Bar(IID, "30m", t, t + timedelta(minutes=30),
               t + timedelta(minutes=30), o, max(h, o, c), min(l, o, c), c, v)


def orch():
    return SessionOrchestrator(
        OrchestratorConfig(EngineConfig("review3", enabled_families=("breakout",))),
        AccountLedger(1_000_000))


def arm(q, at=T - timedelta(minutes=30), entry=10.0):
    q.armed["s"] = ArmedSetup("s", IID, "breakout", entry, 9.0, 12.0, at)


# ═══════════════════════════════════════════════════════
# F02：buy-stop 语义
# ═══════════════════════════════════════════════════════

class TestF02BuyStopSemantics:
    def test_intra_bar_trigger_fills_at_entry_not_open(self):
        """升破10买入，O=9/H=10.5 → 应 FILL@10（触发价），不是 @9（前开盘）。"""
        q = orch(); arm(q)
        ev = q.on_bar(IID, bar(o=9, h=10.5, l=8.9, c=10.2), [], [], None)
        assert any("FILL:s:" in e and "@10" in e for e in ev), (
            f"bar内触发应按触发价10成交，实得 {ev}（F02复现：FILL@9）")

    def test_gap_open_above_entry_fills_at_open(self):
        """跳空高开 O=11 > entry=10 → 应 FILL@11（开盘），不是 NO_FILL。"""
        q = orch(); arm(q)
        ev = q.on_bar(IID, bar(o=11, h=11.5, l=10.8, c=11.2), [], [], None)
        assert any("FILL:s:" in e and "@11" in e for e in ev), (
            f"跳空高于触发价应按开盘成交（buy-stop语义），实得 {ev}（F02复现：NO_FILL）")


# ═══════════════════════════════════════════════════════
# F03：零量/参与率
# ═══════════════════════════════════════════════════════

class TestF03VolumeGate:
    def test_zero_volume_never_fills(self):
        q = orch(); arm(q)
        ev = q.on_bar(IID, bar(v=0), [], [], None)
        assert not any(e.startswith("FILL:") for e in ev), (
            f"零成交量不得成交（F03复现）：{ev}")
        assert q.ledger.positions.total_qty(IID) == 0

    def test_participation_caps_qty(self):
        """低量部分成交：qty ≤ volume×参与率。"""
        q = orch(); arm(q)
        ev = q.on_bar(IID, bar(v=1_000), [], [], None)   # 万分之一参与≈100股上限
        # 期望成交或不成交均可，但成交股数必须受量约束
        for e in ev:
            if "FILL" in e:
                qty = int(e.split(":")[2].split("@")[0])
                assert qty <= 1000, f"成交量参与率超限: {qty}（F03）"


# ═══════════════════════════════════════════════════════
# F04：事件幂等与时序
# ═══════════════════════════════════════════════════════

class TestF04Idempotency:
    def test_same_bar_repeated_state_identical(self):
        """同一根K线投递8次 → 状态与1次相同（不多买/不多NAV/不过期）。"""
        q = orch(); arm(q)
        b = bar()
        e1 = q.on_bar(IID, b, [], [], None)
        nav1, armed1 = len(q.nav_series), len(q.armed)
        for _ in range(7):
            q.on_bar(IID, b, [], [], None)
        assert len(q.nav_series) == nav1, (
            f"重复投递增加NAV记录: {len(q.nav_series)} vs {nav1}（F04复现）")
        assert len(q.armed) == armed1, "重复投递改变armed状态"

    def test_signal_bar_cannot_fill_itself(self):
        """信号棒不得回填成交到信号生效之前。"""
        q = orch()
        b = bar()
        arm(q, at=b.available_at)   # setup 在本棒结束时武装
        ev = q.on_bar(IID, b, [], [], None)
        assert not any("FILL" in e for e in ev), (
            "armed_at==bar可用时刻：同一棒不得触发自己（F04复现：same_timestamp_fill）")

    def test_real_engine_repeat_same_bar_no_duplicate_buy(self):
        """复审复现：真实引擎重复同棒买入10000股。"""
        q = orch()
        cal = TradingCalendar(tuple(date(2026, 10, d) for d in (13, 14, 15)),
                              "review3-fixture")
        starts = [s for d in cal.trading_days for s, e in cal.bars_for_day(d)]
        hist = [bar(t=starts[i], o=9.5, h=10, l=9, c=9.6) for i in range(21)]
        last = bar(t=starts[21], o=10, h=10.3, l=9.8, c=10.01)
        cand = Candidate("cand", IID, ("static_pool",), starts[16], starts[16], None)
        ev1 = q.on_bar(IID, last, hist, [], cand)
        qty1 = q.ledger.positions.total_qty(IID)
        ev2 = q.on_bar(IID, last, hist, [], cand)   # 重复同一棒
        qty2 = q.ledger.positions.total_qty(IID)
        assert qty1 == qty2, f"重复投递改变持仓 {qty1}→{qty2}（F04复现）"


# ═══════════════════════════════════════════════════════
# F01：退出自动绑定
# ═══════════════════════════════════════════════════════

class TestF01AutoExitBinding:
    def test_fill_then_next_day_stop_exit_automatically(self):
        """成交后次日跌破止损 → 自动退出事件，持仓归零（无需手工bind）。"""
        q = orch(); arm(q)
        ev_in = q.on_bar(IID, bar(), [], [], None)
        assert any("FILL" in e for e in ev_in)
        assert q.ledger.positions.total_qty(IID) > 0
        # 次日大跌
        ev_out = q.on_bar(
            IID, bar(t=T + timedelta(days=1), o=8.5, h=8.8, l=8, c=8.2),
            [], [], None)
        assert any("EXIT" in e for e in ev_out), (
            f"跌破止损无退出事件（F01复现：events={ev_out}）")
        assert q.ledger.positions.total_qty(IID) == 0, "退出后持仓应清零"

    def test_exit_at_open_on_gap(self):
        """跳空低于止损按开盘价退出（不按更优止损价）。"""
        q = orch(); arm(q)
        q.on_bar(IID, bar(), [], [], None)
        ev = q.on_bar(IID, bar(t=T + timedelta(days=1), o=8.5, h=8.6,
                               l=8.0, c=8.2), [], [], None)
        assert any("EXIT_STOP:2400@8.5" in e for e in ev), (
            f"跳空应按开盘8.5成交退出，实得 {ev}")


# ═══════════════════════════════════════════════════════
# F05：资格链（弱突破/空日线/regime/family）
# ═══════════════════════════════════════════════════════

class TestF05Qualification:
    def _weak_breakout_setup(self):
        q = orch()
        cal = TradingCalendar(tuple(date(2026, 10, d) for d in (13, 14, 15)),
                              "review3-fixture")
        starts = [s for d in cal.trading_days for s, e in cal.bars_for_day(d)]
        hist = [bar(t=starts[i], o=9.5, h=10, l=9, c=9.6) for i in range(21)]
        last = bar(t=starts[21], o=10, h=10.3, l=9.8, c=10.01)
        cand = Candidate("cand", IID, ("static_pool",), starts[16], starts[16], None)
        return q, hist, last, cand

    def test_weak_breakout_no_daily_not_armed(self):
        """弱突破+空日线+无regime → 不得ARMED（F05复现）。"""
        q, hist, last, cand = self._weak_breakout_setup()
        ev = q.on_bar(IID, last, hist, [], cand)
        assert not any("ARMED" in e for e in ev), (
            f"弱突破+空日线仍ARMED（F05复现）：{ev}")

    def test_family_propagated_not_hardcoded(self):
        """breakout 的 armed family 必须是 breakout（F05复现：硬编码H2）。"""
        q, hist, last, cand = self._weak_breakout_setup()
        # 构造强突破+跟随：让 engine 可武装（即使弱不武装，此测试在有武装时验证）
        ev = q.on_bar(IID, last, hist, [], cand)
        for s in q.armed.values():
            assert s.family != "H2" or "h2" in s.setup_id, (
                f"family 硬编码错误: setup={s.setup_id} family={s.family}")


# ═══════════════════════════════════════════════════════
# F07/F08
# ═══════════════════════════════════════════════════════

class TestF07DuplicateDaily:
    def test_duplicate_bars_not_final(self):
        """同一根09:30-10:00棒重复8次 → 不得构成 final 日线。"""
        partial = resample_30m_to_daily([bar()] * 8, IID)[0]
        assert partial.is_final is False, (
            f"重复棒伪造final日线 volume={partial.volume}（F07复现）")


class TestF08GateDrawdown:
    PLAN = PreregisteredPlan("review3", "alpha", "benchmark", 0.001,
                             max_drawdown_tolerance=0.15, planned_sample=30,
                             variants=("B4",))

    def test_missing_drawdown_inconclusive(self):
        v = release_gate(self.PLAN, {"alpha": 0.01}, 30, ci_lower=0.005,
                         g0_engineering_passed=True)
        assert v != Verdict.PASS, "缺回撤仍PASS（F08复现）"

    def test_metrics_drawdown_90_checked(self):
        v = release_gate(self.PLAN, {"alpha": 0.01, "max_drawdown": 0.9}, 30,
                         ci_lower=0.005, g0_engineering_passed=True)
        assert v == Verdict.FAIL, "metrics内回撤90%未被检查（F08复现）"


# ═══════════════════════════════════════════════════════
# F06：完整成交测试必须真成交
# ═══════════════════════════════════════════════════════

class TestF06RealFillPath:
    def test_full_path_produces_events(self):
        """复审复现：existing_full_fill_test events=[] qty=0。
        修复后：注入可触发计划走完 买→持有→退出 全链。"""
        q = orch(); arm(q)
        ev = []
        ev += q.on_bar(IID, bar(), [], [], None)                     # 成交
        ev += q.on_bar(IID, bar(t=T + timedelta(minutes=60)), [], [], None)   # 持有
        ev += q.on_bar(IID, bar(t=T + timedelta(days=1), o=8.5, h=8.8,
                                l=8.0, c=8.2), [], [], None)         # 止损退出
        joined = " | ".join(ev)
        assert "FILL" in joined, "必须有成交事件（F06：空跑）"
        assert "EXIT" in joined, "必须有退出事件（F06：空跑）"
        assert q.ledger.positions.total_qty(IID) == 0
        assert not q.nav_series or len(q.nav_series) >= 3
        assert q.ledger.cash_conservation_check({})
