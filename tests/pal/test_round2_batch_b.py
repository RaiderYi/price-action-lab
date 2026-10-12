"""第二轮复审批次 B 反例测试：R03/R06/R07/R08/R10-T1。

先红后绿：本文件测试按复审清单 §7 的复现描述编写，修复前应失败。
"""
import math
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar, resample_30m_to_daily
from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError
from pal.execution.market_rules import MAIN_BOARD, Order, OrderState
from pal.ledger.positions import AccountLedger, PositionLot
from pal.portfolio.risk import PaperDefaults, PortfolioConstraints
from pal.research.framework import (
    PreregisteredPlan,
    Verdict,
    max_drawdown,
    release_gate,
)

T0 = datetime(2026, 10, 13, 9, 30, tzinfo=TZ)


def bar30(i, o=10.0, h=10.5, l=9.5, c=10.2, vol=1000.0, iid="SSE.600519",
          at=None):
    s = T0 + timedelta(minutes=30 * i)
    return Bar(instrument_id=iid, timeframe="30m", bar_start=s,
               bar_end=s + timedelta(minutes=30),
               available_at=at or s + timedelta(minutes=30),
               open=o, high=max(h, o, c), low=min(l, o, c), close=c,
               volume=vol)


class TestR03DailyResample:
    """R03：单根上午bar不得产出"最终日线"；多证券不得混入。"""

    def test_single_morning_bar_not_final_daily(self):
        bars = [bar30(0)]   # 只有 09:30-10:00 一根
        out = resample_30m_to_daily(bars, "SSE.600519")
        # 复现：当前产出 1 根 is_final=True 的日线
        assert out == [] or out[0].is_final is False, (
            "未完成的交易日不得产出 final 日线（复审复现：n=1、is_final=True）")

    def test_partial_day_needs_full_grid(self):
        bars = [bar30(i) for i in range(4)]   # 只有上午4根
        out = resample_30m_to_daily(bars, "SSE.600519")
        assert all(b.is_final is False for b in out) or out == []

    def test_full_day_final(self):
        bars = [bar30(i) for i in range(8)]   # 完整8根（含下午）
        out = resample_30m_to_daily(bars, "SSE.600519")
        assert len(out) == 1 and out[0].is_final is True

    def test_foreign_instrument_excluded(self):
        """R03：不按 instrument 过滤导致他票数据混入。"""
        bars = [bar30(i) for i in range(8)] \
            + [bar30(i, iid="SZSE.000001", c=99.0) for i in range(8)]
        out = resample_30m_to_daily(bars, "SSE.600519")
        assert all(b.instrument_id == "SSE.600519" for b in out)
        if out:
            assert out[0].close == pytest.approx(10.2)   # 不被 99 污染


class TestR06OrderTerminalFill:
    """R06：CANCELLED/REJECTED/未提交 订单不得被 apply_fill 复活。"""

    def test_cancelled_then_fill_rejected(self):
        o = Order("o", "p", "buy", "limit", 100, limit_price=10)
        o.transition(OrderState.CANCELLED)
        with pytest.raises((DomainValidationError, Exception)):
            o.apply_fill(100, 10.0)

    def test_rejected_fill_rejected(self):
        o = Order("o", "p", "buy", "limit", 100, limit_price=10)
        o.transition(OrderState.REJECTED)
        with pytest.raises((DomainValidationError, Exception)):
            o.apply_fill(100, 10.0)

    def test_unsubmitted_fill_rejected(self):
        o = Order("o", "p", "buy", "limit", 100, limit_price=10)
        with pytest.raises((DomainValidationError, Exception)):
            o.apply_fill(100, 10.0)   # INTENT 状态未受理

    def test_fill_idempotent(self):
        """fill_id 重复导入不重复记账。"""
        o = Order("o", "p", "buy", "limit", 100, limit_price=10)
        o.transition(OrderState.SUBMITTED)
        o.apply_fill(50, 10.0, fill_id="f1")
        o.apply_fill(50, 10.0, fill_id="f1")   # 重复同一笔
        assert o.filled_qty == 50   # 不重复计

    def test_multi_partial_then_full(self):
        o = Order("o", "p", "buy", "limit", 100, limit_price=10)
        o.transition(OrderState.SUBMITTED)
        o.apply_fill(30, 10.0, fill_id="f1")
        o.apply_fill(70, 10.5, fill_id="f2")
        assert o.state == OrderState.FILLED
        assert o.filled_qty == 100
        assert o.avg_fill_price == pytest.approx((300 + 735) / 100)


class TestR07PositionCapDeductsExisting:
    """R07：单票上限必须扣除已有持仓（与在途买单）。"""

    def test_existing_9pct_position_capped_to_1pct(self):
        """复现：已有9万（9%），entry10/stop9/cash91万 → 允许2400股=11.4%。"""
        pc = PortfolioConstraints(PaperDefaults())
        rd = pc.size_position(
            entry=10.0, stop=9.0, cash=910_000.0, nav=1_000_000.0,
            positions_value=90_000.0,
            instrument_value=90_000.0,      # 该票已有9%
            industry_value=0.0)
        after = (90_000 + rd.max_qty * 10.0) / 1_000_000.0
        assert after <= 0.10 + 1e-9, (
            f"已有9%后新增{rd.max_qty}股，合计{after:.1%} 突破10%上限（R07复现）")

    def test_pending_order_occupies_budget(self):
        """在途买单占用额度。"""
        pc = PortfolioConstraints(PaperDefaults())
        rd = pc.size_position(
            entry=10.0, stop=9.0, cash=910_000.0, nav=1_000_000.0,
            positions_value=0.0, instrument_value=0.0, industry_value=0.0,
            pending_instrument_orders_value=95_000.0)   # 在途9.5万
        assert rd.max_qty * 10.0 <= 100_000 - 95_000 + 100 + 1e-6


class TestR08ReleaseGate:
    PLAN = PreregisteredPlan(
        plan_version="v1", primary_metric="excess_mean",
        primary_benchmark="csi300", min_economic_threshold=0.0002,
        max_drawdown_tolerance=0.15, planned_sample=120, variants=("B3",))

    def test_missing_ci_is_inconclusive(self):
        """复现：ci_lower=None + 主指标达标 → 当前 PASS。必须 INCONCLUSIVE。"""
        v = release_gate(self.PLAN, {"excess_mean": 0.001}, n_samples=150)
        assert v == Verdict.INCONCLUSIVE, "缺置信区间不得 PASS（R08复现1）"

    def test_drawdown_breach_is_fail(self):
        """复现：回撤90% > 容忍15% 仍 PASS。必须 FAIL。"""
        v = release_gate(self.PLAN, {"excess_mean": 0.001}, n_samples=150,
                         ci_lower=0.0005, realized_max_drawdown=0.90,
                         g0_engineering_passed=True)
        assert v == Verdict.FAIL, "超回撤容忍必须 FAIL（R08复现2）"

    def test_nan_metrics_inconclusive_or_fail(self):
        """复现：NaN 主指标比较恒 False → PASS。必须非 PASS。"""
        v = release_gate(self.PLAN, {"excess_mean": float("nan")},
                         n_samples=150, ci_lower=0.0005)
        assert v != Verdict.PASS, "NaN 指标不得 PASS（R08复现3）"
        v2 = release_gate(self.PLAN, {"excess_mean": 0.001}, n_samples=150,
                          ci_lower=float("nan"))
        assert v2 != Verdict.PASS

    def test_g0_engineering_gate_required(self):
        """缺 G0 工程证据 → INCONCLUSIVE。"""
        v = release_gate(self.PLAN, {"excess_mean": 0.001}, n_samples=150,
                         ci_lower=0.0005, realized_max_drawdown=0.05,
                         g0_engineering_passed=False)
        assert v != Verdict.PASS


class TestR10T1Boundary:
    """R10：buy 传入非法 sellable_from（≤当日）必须拒绝。"""

    def test_same_day_sellable_rejected(self):
        """复现：t1_next_trading_day=买入当日 → 当日买卖成功。必须拒绝。"""
        led = AccountLedger(100_000.0)
        d = date(2026, 10, 13)
        with pytest.raises(DomainValidationError, match="T\\+1|sellable"):
            led.buy("X", 1000, 10.0, d, MAIN_BOARD,
                    t1_next_trading_day=d)   # 非法：当日可卖
