"""估计层：质量分与概率分离（S1-06，F14/F20）。

规则（任务书 §4 SourceEstimate / §5.3）：
- heuristic_score：规则启发式质量分，0~1，可排序，不是概率。
- p_win：实证胜率。未校准时必须为 None——禁止用 0.55/0.60/0.65 之类
  常量冒充（F14：signal_predictor 的 confidence 是规则置信，不是胜率）。
- 来源先验（如知识库"60%胜率"）进 SourceEstimate.probability_status=
  "uncalibrated_prior"，永不伪装成 empirical。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import DomainValidationError, require_non_negative


PROBABILITY_STATUS = frozenset({
    "uncalibrated_prior",   # 书中/知识库百分比，未经本系统样本校准
    "calibrated",           # 训练期校准 + 时间外验证通过
    "shrunk",               # 罕见形态收缩估计
})


@dataclass(frozen=True)
class HeuristicScore:
    """规则质量分。字段名刻意不叫 confidence/probability。"""
    score: float          # 0..1
    components: dict      # 分解：{"range_expansion": ..., "extreme_close": ...}
    rule_version: str

    def __post_init__(self):
        if not (0.0 <= self.score <= 1.0):
            raise DomainValidationError(f"heuristic score 超出[0,1]: {self.score}")
        if not self.rule_version:
            raise DomainValidationError("rule_version 不能为空（可复现要求）")


@dataclass(frozen=True)
class EmpiricalProbability:
    """实证概率。只能由 calibration 层（S7-07）构造成功实例。"""
    p_win: float
    n_samples: int
    method: str                     # e.g. "train_window_finished_labels"
    validation: str                 # 时间外验证描述
    calibrated_at: str              # ISO8601

    def __post_init__(self):
        if not (0.0 < self.p_win < 1.0):
            raise DomainValidationError(f"p_win 越界: {self.p_win}")
        if self.n_samples <= 0:
            raise DomainValidationError("实证概率必须有正样本数")
        require_non_negative(self.n_samples, "n_samples")


@dataclass(frozen=True)
class SourceEstimate:
    """外部候选源（如私有五模型）的原始估计——保留原样，不重算。"""
    source_id: str
    source_ev: Optional[float]          # 源 EV 分（原样保留）
    source_wr: Optional[float]          # 源胜率先验（原样保留）
    probability_status: str             # PROBABILITY_STATUS 成员
    source_method: str
    source_version: str

    def __post_init__(self):
        if self.probability_status not in PROBABILITY_STATUS:
            raise DomainValidationError(
                f"probability_status 非法: {self.probability_status!r}; "
                f"合法值: {sorted(PROBABILITY_STATUS)}")


def uncalibrated_pwin_is_none() -> None:
    """接口约定自查：未校准时 p_win 必须为 None（供测试引用的文档化锚点）。"""
    return None
