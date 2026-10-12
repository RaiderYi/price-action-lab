"""研究框架（S7）：预注册、时间切分、指标、裁决。

红线（任务书 §5）：
- 预注册先于运行；阈值未填完整不自动 PASS；
- 标签不穿越（purge/隔离）；
- 变体 U0/S0/S1/A-original/B0-B4 注册制；
- PASS/FAIL/INCONCLUSIVE 分立；缺数据≠零收益。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from pal.domain.models import DomainValidationError


# ═══════════════════════════════════════════════════════════
# S7-01 预注册
# ═══════════════════════════════════════════════════════════

class Variant(str, Enum):
    U0 = "U0"            # 可交易池基线
    S0 = "S0"            # 透明选股器
    S1 = "S1"            # 五模型候选
    A_ORIGINAL = "A-original"
    B0 = "B0"            # 冻结候选+基础执行
    B1 = "B1"            # +regime门
    B2 = "B2"            # +结构门
    B3 = "B3"            # +双门
    B4 = "B4"            # +价格/退出/组合


PREREGISTERED_VARIANTS = frozenset(v.value for v in Variant)


@dataclass(frozen=True)
class PreregisteredPlan:
    """研究计划（运行前冻结；S7-01）。"""
    plan_version: str
    primary_metric: str          # 主检验指标（如 "cost_adjusted_daily_excess_mean"）
    primary_benchmark: str       # 主基准
    min_economic_threshold: Optional[float]   # 最小经济增益（None=未填→禁PASS）
    confidence_level: float = 0.95
    max_drawdown_tolerance: Optional[float] = None
    planned_sample: Optional[int] = None
    fail_conditions: Tuple[str, ...] = ()
    variants: Tuple[str, ...] = ()


class PlanIncompleteError(RuntimeError):
    """预注册不完整 → 不得输出正式 PASS（任务书 S7-01 红线）。"""


def validate_plan(plan: PreregisteredPlan) -> None:
    missing = []
    if plan.min_economic_threshold is None:
        missing.append("min_economic_threshold")
    if plan.max_drawdown_tolerance is None:
        missing.append("max_drawdown_tolerance")
    if not plan.planned_sample:
        missing.append("planned_sample")
    if not plan.variants:
        missing.append("variants")
    if missing:
        raise PlanIncompleteError(
            f"预注册不完整: {missing}；未填完整不得自动 PASS（S7-01）")


# ═══════════════════════════════════════════════════════════
# S7-02 时间切分 + purge
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TimeSplit:
    train_start: date
    train_end: date
    valid_start: date
    valid_end: date
    test_start: date
    test_end: date
    purge_days: int              # 标签穿越隔离
    embargo_days: int = 0

    def __post_init__(self):
        if not (self.train_start < self.train_end < self.valid_start
                <= self.valid_end < self.test_start <= self.test_end):
            raise DomainValidationError(f"切分时间非法: {self}")
        if self.purge_days < 0:
            raise DomainValidationError("purge_days 非负")

    def train_labels_allowed_through(self) -> date:
        """训练标签截止：valid_start - purge（跨越切分边界的样本清除）。"""
        from datetime import timedelta
        return self.valid_start - timedelta(days=self.purge_days)

    def valid_labels_allowed_through(self) -> date:
        from datetime import timedelta
        return self.test_start - timedelta(days=self.purge_days)


def make_labels_purged(label_dates: Sequence[date], split: TimeSplit,
                       which: str = "train") -> List[date]:
    """清除跨边界标签（S7-02 验收：训练标签不穿越验证时间）。"""
    if which == "train":
        limit = split.train_labels_allowed_through()
        return [d for d in label_dates
                if split.train_start <= d <= limit]
    if which == "valid":
        limit = split.valid_labels_allowed_through()
        return [d for d in label_dates
                if split.valid_start <= d <= limit]
    return [d for d in label_dates if split.test_start <= d <= split.test_end]


# ═══════════════════════════════════════════════════════════
# S7-04 指标（任务书 §5.3 公式）
# ═══════════════════════════════════════════════════════════

def nav_returns(nav_series: Sequence[float]) -> List[float]:
    """日收益（无外部资金流时 r_t = NAV_t/NAV_{t-1}-1）。"""
    if len(nav_series) < 2:
        raise DomainValidationError("NAV 序列过短")
    return [nav_series[i] / nav_series[i - 1] - 1
            for i in range(1, len(nav_series)) if nav_series[i - 1] > 0]


def cumulative_return(nav_series: Sequence[float]) -> float:
    return nav_series[-1] / nav_series[0] - 1


def excess_return_diff(nav_series: Sequence[float],
                       bench_series: Sequence[float]) -> float:
    """累计收益差（百分点，任务书 §5.3：与相对财富分开命名）。"""
    if len(nav_series) != len(bench_series):
        raise DomainValidationError("时间轴不对齐")
    return (cumulative_return(nav_series) - cumulative_return(bench_series)) * 100


def relative_wealth(nav_series: Sequence[float],
                    bench_series: Sequence[float]) -> float:
    """相对财富 = (NAV_T/NAV_0)/(B_T/B_0)-1（与收益差分开命名）。"""
    return ((nav_series[-1] / nav_series[0])
            / (bench_series[-1] / bench_series[0])) - 1


def information_ratio(nav_series: Sequence[float],
                      bench_series: Sequence[float],
                      annualization: int = 244) -> Optional[float]:
    """日超额均值/标准差 × 年化平方根；样本不足或零波动 → None（NA）。"""
    if len(nav_series) != len(bench_series) or len(nav_series) < 3:
        return None
    r = nav_returns(nav_series)
    b = nav_returns(bench_series)
    excess = [x - y for x, y in zip(r, b)]
    n = len(excess)
    mean = sum(excess) / n
    var = sum((x - mean) ** 2 for x in excess) / (n - 1)
    sd = var ** 0.5
    if sd == 0:
        return None
    return mean / sd * (annualization ** 0.5)


def max_drawdown(nav_series: Sequence[float]) -> float:
    peak = nav_series[0]
    mdd = 0.0
    for v in nav_series:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak)
    return mdd


def r_multiple(entry: float, stop: float, exit_price: float,
               direction: str = "long") -> float:
    """R = 净盈亏 / 初始风险金额（初始风险不随移动止损更新）。"""
    risk = abs(entry - stop)
    if risk <= 0:
        raise DomainValidationError("初始风险为零")
    pnl = (exit_price - entry) if direction == "long" else (entry - exit_price)
    return pnl / risk


# ═══════════════════════════════════════════════════════════
# S7-08 裁决
# ═══════════════════════════════════════════════════════════

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"     # 缺数据不算零收益


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: str
    variant: str
    split: str
    metrics: Dict[str, float]
    status: Verdict
    limitations: Tuple[str, ...] = ()


def release_gate(plan: PreregisteredPlan, result_metrics: Dict[str, float],
                 n_samples: int, ci_lower: Optional[float] = None) -> Verdict:
    """G1/G2 裁决（S7-08）。

    - 计划不完整 → INCONCLUSIVE（不是 FAIL）
    - 样本 < planned_sample → INCONCLUSIVE
    - 主指标 < 阈值 → FAIL
    - CI 下界 <= 0 → INCONCLUSIVE（统计不可信，扩样本）
    - 全过 → PASS
    """
    try:
        validate_plan(plan)
    except PlanIncompleteError:
        return Verdict.INCONCLUSIVE
    if n_samples < (plan.planned_sample or 0):
        return Verdict.INCONCLUSIVE
    pm = result_metrics.get(plan.primary_metric)
    if pm is None:
        return Verdict.INCONCLUSIVE
    if pm < (plan.min_economic_threshold or 0.0):
        return Verdict.FAIL
    if ci_lower is not None and ci_lower <= 0:
        return Verdict.INCONCLUSIVE
    return Verdict.PASS
