"""决策快照与规则解释协议（S1-08，任务书 §4 关键附加协议）。

每次 accept/reject/wait 都必须携带：rule_id、evidence_ids、reason_code。
序列化可重放：同一已知事实集合 → 同一决策。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple

from .models import DomainValidationError, require_non_empty_str


DECISION_OUTCOMES = frozenset({"accept", "reject", "wait"})

# 登记的 reason_code（新增必须在此登记，禁止裸字符串散落）
REASON_CODES = frozenset({
    "OK_STRUCTURE_CONFIRMED",          # 结构确认通过
    "REJ_INSUFFICIENT_EVIDENCE",       # F05：缺结构证据
    "REJ_PRICE_INVALID",               # 价格非法（stop>=entry 等）
    "REJ_DIRECTION_CONFLICT",          # 多空冲突
    "REJ_COUNTER_TREND",               # 强趋势逆势禁令（focus_config）
    "REJ_REGIME_MISMATCH",             # 环境错配（tr_fade 无 range 等）
    "REJ_RR_BELOW_MIN",                # RR 低于注册表 min_rr
    "REJ_NOT_LIVE_SIGNAL",             # 非生产信号面
    "REJ_STALE_CANDIDATE",             # 候选过期（S3-08 语义）
    "WAIT_TRIGGER_PENDING",            # setup 成立未触发（F06：预测≠成交）
    "WAIT_CONFIRMATION_PENDING",       # 等待确认棒
    "WAIT_RISK_BUDGET_EXHAUSTED",      # 组合风险预算不足
})


@dataclass(frozen=True)
class DecisionSnapshot:
    """一次规则裁决的完整留痕。"""
    outcome: str                      # accept / reject / wait
    rule_id: str                      # 裁决所用规则（注册表 ID 或引擎规则）
    reason_code: str                  # REASON_CODES 成员
    evidence_ids: Tuple[str, ...]      # 支撑证据（空元组仅允许显式无证据场景）
    decided_at: str                   # ISO8601（信息可用时刻之后的合法决策时刻）
    detail: dict = field(default_factory=dict)
    config_version: str = ""          # 决策时配置版本（可回放要求）

    def __post_init__(self):
        if self.outcome not in DECISION_OUTCOMES:
            raise DomainValidationError(f"outcome 非法: {self.outcome!r}")
        if self.reason_code not in REASON_CODES:
            raise DomainValidationError(
                f"reason_code 未登记: {self.reason_code!r}；新增须先登记 REASON_CODES")
        require_non_empty_str(self.rule_id, "rule_id")
        require_non_empty_str(self.decided_at, "decided_at")
        if not self.evidence_ids and self.outcome == "accept":
            raise DomainValidationError(
                "accept 决策必须有 evidence_ids（REJ_INSUFFICIENT_EVIDENCE 之外的 "
                "accept 不允许空证据）")

    def to_json(self) -> str:
        d = asdict(self)
        d["evidence_ids"] = list(self.evidence_ids)
        return json.dumps(d, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> "DecisionSnapshot":
        d = json.loads(s)
        d["evidence_ids"] = tuple(d.get("evidence_ids") or [])
        return cls(**d)
