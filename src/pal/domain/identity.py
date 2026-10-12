"""统一 ID 体系（S1-07，任务书 §4 / 验收"重跑不重复创建订单"）。

原则：
- 所有实体 ID 是字符串前缀 + 内容寻址/序号，跨运行可追溯。
- run_id 显式携带时间与配置 hash，使 RunManifest 可复现定位。
- setup_id 区分同票不同结构；signal_id 区分同 setup 不同触发。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .models import DomainValidationError, require_non_empty_str

ID_PREFIXES = frozenset({
    "run",        # 一次引擎执行
    "cand",       # 候选
    "setup",      # 结构设置（同一票可多个并存 setup）
    "sig",        # 信号事件（状态机实例）
    "plan",       # 交易计划
    "ord",        # 订单意图/订单
    "fill",       # 成交
    "lot",        # 持仓批次
    "evd",        # 结构证据
    "exp",        # 实验
})


def _content_hash(*parts: str, length: int = 12) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8"))
    return h.hexdigest()[:length]


@dataclass(frozen=True)
class EntityId:
    """带类型前缀的实体 ID。"""
    prefix: str
    value: str

    def __post_init__(self):
        if self.prefix not in ID_PREFIXES:
            raise DomainValidationError(f"未知 ID 前缀: {self.prefix!r}")
        require_non_empty_str(self.value, "ID value")

    def __str__(self) -> str:
        return f"{self.prefix}_{self.value}"

    @classmethod
    def parse(cls, s: str) -> "EntityId":
        require_non_empty_str(s, "ID string")
        prefix, _, value = s.partition("_")
        return cls(prefix=prefix, value=value)


def make_run_id(created_at_iso: str, config_hash: str) -> EntityId:
    """run_id = run_<时间>_<config_hash 前8>。同配置同输入可复现定位。"""
    return EntityId("run", f"{created_at_iso}_{_content_hash(config_hash, length=8)}")


def make_setup_id(instrument_id: str, family: str, implementation: str,
                  formed_at: str) -> EntityId:
    """setup_id 内容寻址：同票同结构同形成时间 → 同 ID（幂等）。"""
    return EntityId("setup", _content_hash(instrument_id, family, implementation, formed_at))


def make_signal_id(setup_id: str, state_transition_marker: str) -> EntityId:
    return EntityId("sig", _content_hash(setup_id, state_transition_marker))


def make_order_id(plan_id: str, attempt: int) -> EntityId:
    """订单重试不换 ID 语义：attempt 单调递增，重跑复用 plan 时不重复下单。"""
    if attempt < 1:
        raise DomainValidationError("attempt 必须 ≥1")
    return EntityId("ord", f"{plan_id}-{attempt}")
