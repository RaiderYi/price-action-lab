"""S6 测试：风险定仓/约束/退出/熔断/压力/容量。"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.domain.models import DomainValidationError
from pal.portfolio.risk import (
    CircuitBreaker,
    ExitPolicyEngine,
    ExitPolicyState,
    ExitReason,
    PaperDefaults,
    PortfolioConstraints,
    capacity_report,
    gap_stress_loss,
)


class TestPositionSizing:
    """S6-01/S6-02：风险预算+资金双重上限；极窄止损不满仓。"""

    def setup_method(self):
        self.pc = PortfolioConstraints(PaperDefaults())

    def test_normal_sizing(self):
        rd = self.pc.size_position(
            entry=100.0, stop=95.0, cash=1_000_000.0, nav=1_000_000.0,
            positions_value=0.0, instrument_value=0.0, industry_value=0.0)
        # 风险预算 2500（含费系数）→ 499股 → 取整 400
        assert rd.allow and rd.max_qty == 400
        assert rd.risk_budget == pytest.approx(2500.0)

    def test_tight_stop_capped_by_position_pct(self):
        """极窄止损不能放大为满仓（单票10%上限封顶）。"""
        rd = self.pc.size_position(
            entry=100.0, stop=99.99, cash=1_000_000.0, nav=1_000_000.0,
            positions_value=0.0, instrument_value=0.0, industry_value=0.0)
        # 风险允许 250万/0.01=25万股，但单票上限10万/100=1000股
        assert rd.max_qty == 1000

    def test_cash_constraint(self):
        rd = self.pc.size_position(
            entry=100.0, stop=95.0, cash=10_000.0, nav=1_000_000.0,
            positions_value=0.0, instrument_value=0.0, industry_value=0.0)
        # 现金 1万 → 风险允许499但现金只够99股 → 不足一手(100) → 0
        assert rd.max_qty == 0 and not rd.allow
        rd2 = self.pc.size_position(
            entry=10.0, stop=9.5, cash=10_000.0, nav=1_000_000.0,
            positions_value=0.0, instrument_value=0.0, industry_value=0.0)
        # 低价股：现金够1000股，风险预算允许 → 至少一手
        assert rd2.max_qty >= 100

    def test_total_exposure_cap(self):
        rd = self.pc.size_position(
            entry=100.0, stop=95.0, cash=500_000.0, nav=1_000_000.0,
            positions_value=780_000.0, instrument_value=0.0, industry_value=0.0)
        # 80%上限：还剩2万 → 200股
        assert "CAPPED_BY_TOTAL_EXPOSURE" in rd.reason_codes
        assert rd.max_qty == 200

    def test_industry_cap(self):
        rd = self.pc.size_position(
            entry=100.0, stop=95.0, cash=500_000.0, nav=1_000_000.0,
            positions_value=0.0, instrument_value=0.0, industry_value=240_000.0)
        # 行业25%：还剩1万 → 100股
        assert "CAPPED_BY_INDUSTRY" in rd.reason_codes
        assert rd.max_qty == 100

    def test_stop_above_entry_rejected(self):
        rd = self.pc.size_position(
            entry=100.0, stop=101.0, cash=1e6, nav=1e6,
            positions_value=0, instrument_value=0, industry_value=0)
        assert not rd.allow and rd.reason_codes == ("REJ_STOP_ABOVE_ENTRY",)

    def test_no_capacity_explicit(self):
        rd = self.pc.size_position(
            entry=100.0, stop=95.0, cash=50.0, nav=1e6,
            positions_value=0, instrument_value=0, industry_value=0)
        assert not rd.allow and "REJ_NO_CAPACITY" in rd.reason_codes

    def test_max_positions(self):
        assert self.pc.position_count_ok(9)
        assert not self.pc.position_count_ok(10)

    def test_multi_source_one_budget(self):
        """S6-05：五模型同票→一份净风险预算。"""
        assert self.pc.conflicting_sources_share_budget(("m1", "m2", "m3")) == 1


class TestExitPolicy:
    def test_priority_structure_first(self):
        eng = ExitPolicyEngine()
        st = ExitPolicyState(stop=95.0, bars_held=100)   # 同时超时+触止损
        r = eng.evaluate(st, high=100, low=90, close=91,
                         structure_invalid=True)
        assert r == ExitReason.STRUCTURE_INVALID

    def test_risk_before_timeout(self):
        eng = ExitPolicyEngine()
        st = ExitPolicyState(stop=95.0, bars_held=100)
        r = eng.evaluate(st, high=100, low=90, close=91,
                         structure_invalid=False)
        assert r == ExitReason.RISK_EXIT

    def test_timeout(self):
        eng = ExitPolicyEngine()
        st = ExitPolicyState(stop=50.0, bars_held=41)
        assert eng.evaluate(st, 100, 90, 99, False) == ExitReason.TIMEOUT

    def test_no_exit(self):
        eng = ExitPolicyEngine()
        st = ExitPolicyState(stop=95.0, bars_held=10)
        assert eng.evaluate(st, 100, 96, 99, False) is None

    def test_trailing_never_lowers_and_pending(self):
        """R10：移动止损写 pending，advance_bar 后才激活且永不下调。"""
        st = ExitPolicyState(stop=95.0)
        eng = ExitPolicyEngine()
        eng.update_trailing(st, 98.0)
        assert st.stop == 95.0          # 本棒不生效（R10）
        assert st.pending_stop == 98.0
        eng.advance_bar(st)             # 下一棒激活
        assert st.stop == 98.0
        eng.update_trailing(st, 90.0)   # 试图下调
        assert st.pending_stop == 98.0  # 永不下调
        eng.advance_bar(st)
        assert st.stop == 98.0


class TestCircuitBreaker:
    def test_drawdown_locks_opening(self):
        cb = CircuitBreaker(PaperDefaults())
        ok, _ = cb.on_nav(1_000_000, date(2026, 10, 13))
        assert ok
        ok, why = cb.on_nav(890_000, date(2026, 10, 20))   # -11%
        assert not ok and "DRAWDOWN" in why
        # 已有持仓风险管理不受影响：退出引擎照常
        eng = ExitPolicyEngine()
        assert eng.evaluate(ExitPolicyState(stop=95.0), 100, 94, 99, False) \
            == ExitReason.RISK_EXIT

    def test_daily_loss_locks(self):
        cb = CircuitBreaker(PaperDefaults())
        cb.on_nav(1_000_000, date(2026, 10, 13))
        ok, _ = cb.open_allowed(978_000)   # -2.2% > 2%
        assert not ok

    def test_data_fault_locks_then_recovers(self):
        cb = CircuitBreaker(PaperDefaults())
        cb.on_data_fault(True)
        ok, why = cb.open_allowed(1_000_000)
        assert not ok and why == "DATA_FAULT"
        cb.on_data_fault(False)
        ok, _ = cb.open_allowed(1_000_000)
        assert ok

    def test_manual_override_logged(self):
        cb = CircuitBreaker(PaperDefaults())
        cb.manual_override("force_close", "user judgment")
        assert cb.manual_override_log == [("force_close", "user judgment")]


class TestStressAndCapacity:
    def test_gap_loss_beyond_1r(self):
        """S6-03：跳空超过初始风险。"""
        loss = gap_stress_loss(entry=100.0, stop=95.0, gap_open=92.0, qty=1000)
        assert loss == pytest.approx(3000.0)   # 超1R部分 (95-92)*1000

    def test_no_gap_no_extra_loss(self):
        assert gap_stress_loss(100.0, 95.0, 96.0, 1000) == 0.0

    def test_capacity_participation(self):
        rep = capacity_report(order_value=500_000, bar_amount=1_000_000,
                              max_participation=0.1)
        assert not rep["capacity_ok"] and rep["reason"] == "EXCEEDS_PARTICIPATION"
        rep2 = capacity_report(order_value=50_000, bar_amount=1_000_000)
        assert rep2["capacity_ok"]

    def test_no_liquidity(self):
        rep = capacity_report(1000, bar_amount=0)
        assert not rep["capacity_ok"] and rep["reason"] == "NO_LIQUIDITY"
