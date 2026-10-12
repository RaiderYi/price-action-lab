"""S7 测试：预注册/切分purge/指标公式/裁决。"""
import math
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.domain.models import DomainValidationError
from pal.research.framework import (
    ExperimentResult,
    PlanIncompleteError,
    PreregisteredPlan,
    PREREGISTERED_VARIANTS,
    TimeSplit,
    Verdict,
    cumulative_return,
    excess_return_diff,
    information_ratio,
    make_labels_purged,
    max_drawdown,
    nav_returns,
    r_multiple,
    release_gate,
    relative_wealth,
    validate_plan,
)


class TestPreregistration:
    def test_incomplete_plan_rejected(self):
        p = PreregisteredPlan(plan_version="v1", primary_metric="x",
                              primary_benchmark="csi300",
                              min_economic_threshold=None)
        with pytest.raises(PlanIncompleteError, match="min_economic"):
            validate_plan(p)

    def test_variants_registry(self):
        assert {"U0", "S0", "S1", "A-original", "B0", "B1", "B2", "B3", "B4"} \
            <= PREREGISTERED_VARIANTS


class TestTimeSplit:
    def test_valid_split(self):
        ts = TimeSplit(date(2020, 1, 1), date(2022, 12, 31),
                       date(2023, 1, 1), date(2024, 12, 31),
                       date(2025, 1, 1), date(2026, 6, 30), purge_days=10)
        assert ts.train_labels_allowed_through() == date(2022, 12, 22)

    def test_overlap_rejected(self):
        with pytest.raises(DomainValidationError):
            TimeSplit(date(2020, 1, 1), date(2023, 6, 30),
                      date(2023, 1, 1), date(2024, 12, 31),
                      date(2025, 1, 1), date(2026, 6, 30), purge_days=10)

    def test_purge_removes_boundary_labels(self):
        """S7-02 验收：训练标签不穿越验证时间。"""
        ts = TimeSplit(date(2020, 1, 1), date(2022, 12, 31),
                       date(2023, 1, 1), date(2024, 12, 31),
                       date(2025, 1, 1), date(2026, 6, 30), purge_days=10)
        labels = [date(2022, 12, 20), date(2022, 12, 25),   # 25日 > 12-22 应清除
                  date(2023, 1, 5)]
        kept = make_labels_purged(labels, ts, "train")
        assert date(2022, 12, 25) not in kept
        assert date(2022, 12, 20) in kept


class TestMetrics:
    def test_nav_returns(self):
        assert nav_returns([100, 110, 99]) == pytest.approx([0.10, -0.10])

    def test_cumulative(self):
        assert cumulative_return([100, 150]) == pytest.approx(0.5)

    def test_excess_diff_vs_relative_wealth_separate(self):
        """§5.3：两个指标分开命名，数值不同。"""
        nav = [100, 200]           # +100%
        bench = [100, 110]         # +10%
        d = excess_return_diff(nav, bench)          # 90pp
        rw = relative_wealth(nav, bench)            # (2/1.1)-1 ≈ 0.818
        assert d == pytest.approx(90.0)
        assert rw == pytest.approx(200 / 110 - 1)
        assert d / 100 != rw

    def test_information_ratio(self):
        nav = [100, 101, 102, 103, 104]
        bench = [100, 100.5, 101, 101.5, 102]
        ir = information_ratio(nav, bench)
        assert ir is not None and ir > 0

    def test_ir_zero_vol_returns_none(self):
        nav = [100, 101, 102, 103, 104]
        assert information_ratio(nav, nav) is None   # NA 不是 0

    def test_max_drawdown(self):
        assert max_drawdown([100, 120, 90, 110]) == pytest.approx(0.25)

    def test_r_multiple_initial_risk(self):
        """R 用初始风险（不随移动止损更新）。"""
        assert r_multiple(100, 95, 110) == pytest.approx(2.0)
        assert r_multiple(100, 95, 92) == pytest.approx(-1.6)   # 跳空超损

    def test_zero_risk_rejected(self):
        with pytest.raises(DomainValidationError):
            r_multiple(100, 100, 110)


GOOD_PLAN = PreregisteredPlan(
    plan_version="v1", primary_metric="cost_adjusted_daily_excess_mean",
    primary_benchmark="csi300", min_economic_threshold=0.0002,
    max_drawdown_tolerance=0.15, planned_sample=120,
    variants=("B3", "B0"), fail_conditions=("ci_lower<=0",))


class TestReleaseGate:
    def test_incomplete_plan_inconclusive(self):
        p = PreregisteredPlan("v1", "m", "b", None)
        assert release_gate(p, {"m": 1.0}, 100) == Verdict.INCONCLUSIVE

    def test_insufficient_samples_inconclusive(self):
        v = release_gate(GOOD_PLAN, {"cost_adjusted_daily_excess_mean": 0.001},
                         n_samples=50)
        assert v == Verdict.INCONCLUSIVE

    def test_below_threshold_fail(self):
        v = release_gate(GOOD_PLAN, {"cost_adjusted_daily_excess_mean": 0.0001},
                         n_samples=150)
        assert v == Verdict.FAIL

    def test_ci_lower_nonpositive_inconclusive(self):
        v = release_gate(GOOD_PLAN, {"cost_adjusted_daily_excess_mean": 0.001},
                         n_samples=150, ci_lower=-0.0001)
        assert v == Verdict.INCONCLUSIVE

    def test_full_pass(self):
        v = release_gate(GOOD_PLAN, {"cost_adjusted_daily_excess_mean": 0.001},
                         n_samples=150, ci_lower=0.0005)
        assert v == Verdict.PASS
