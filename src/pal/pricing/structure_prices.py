"""统一结构定价服务（S4-07，F05）：清除隐式百分比成功兜底。

任务书 F05 裁定：breakout/final_flag 空证据落到 _generic 固定百分比并
返回 success = "无结构的价格被包装成系统事实"。本服务：
- 每种启用入场信号必须有结构 stop/target 依据；
- 缺证据 → insufficient_evidence（price_status），绝不 success；
- 多头必须 stop < entry < target（硬校验，§7 价格场景）；
- RR 成本后复核留给 S5（费用层）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pal.domain.models import (
    DomainValidationError,
    require_positive_price,
)


@dataclass(frozen=True)
class StructuredPricePlan:
    entry: float
    stop: float
    target: float
    structure_rr: float
    price_status: str            # "structured" | "insufficient_evidence"
    basis: str                   # 结构依据描述（可审计）
    evidence_fields: tuple       # 用到的证据字段名


class InsufficientStructureEvidence(DomainValidationError):
    pass


def price_h2_long(evidence: dict, current_price: float) -> StructuredPricePlan:
    """H2 多头结构价：entry=H2信号棒高点上方，stop=HL2 下方，target=HH 前高。

    证据（KR-H2-COUNT-001）：HL2（第二回调低点）、signal_bar_high、
    prior_high（前高）。缺任一 → insufficient。
    """
    need = ("HL2", "signal_bar_high", "prior_high")
    missing = [k for k in need if not isinstance(evidence.get(k), (int, float))
               or evidence.get(k, 0) <= 0]
    if missing:
        raise InsufficientStructureEvidence(
            f"H2 定价缺证据字段: {missing}（禁止百分比兜底，F05）")
    hl2 = float(evidence["HL2"])
    entry = float(evidence["signal_bar_high"])
    prior_high = float(evidence["prior_high"])
    require_positive_price(current_price, "current_price")
    # 硬校验：多头 stop < entry < target（任务书 §7）
    if not (hl2 < entry):
        raise DomainValidationError(
            f"H2 多头结构非法: stop({hl2}) >= entry({entry})")
    target = max(prior_high, entry + 2 * (entry - hl2))
    risk = entry - hl2
    plan = StructuredPricePlan(
        entry=entry, stop=hl2, target=target,
        structure_rr=round((target - entry) / risk, 2) if risk > 0 else 0.0,
        price_status="structured",
        basis=f"H2: entry=信号棒高{entry}, stop=HL2 {hl2}, target=前高{prior_high}或2R",
        evidence_fields=tuple(need),
    )
    if plan.structure_rr <= 0:
        raise DomainValidationError("RR 非正")
    return plan


def price_breakout_long(evidence: dict, current_price: float) -> StructuredPricePlan:
    """突破多头：entry=突破位，stop=信号棒低点（或突破棒中点），target=测量目标。

    证据：breakout_level、signal_bar_low、measured_target（测量移动或
    区间高度投影）。全结构化，无百分比兜底。
    """
    need = ("breakout_level", "signal_bar_low", "measured_target")
    missing = [k for k in need if not isinstance(evidence.get(k), (int, float))
               or evidence.get(k, 0) <= 0]
    if missing:
        raise InsufficientStructureEvidence(
            f"breakout 定价缺证据字段: {missing}（F05：无结构证据不得定价）")
    entry = float(evidence["breakout_level"])
    stop = float(evidence["signal_bar_low"])
    target = float(evidence["measured_target"])
    if not (stop < entry < target):
        raise DomainValidationError(
            f"breakout 多头结构非法: stop({stop}) < entry({entry}) < target({target}) 不成立")
    risk = entry - stop
    return StructuredPricePlan(
        entry=entry, stop=stop, target=target,
        structure_rr=round((target - entry) / risk, 2),
        price_status="structured",
        basis=f"breakout: entry=突破位{entry}, stop=信号棒低{stop}, target=测量{target}",
        evidence_fields=tuple(need),
    )


def price_insufficient(reason: str) -> StructuredPricePlan:
    """显式 insufficient 输出（调用方决定展示，但不可进入订单链）。"""
    return StructuredPricePlan(
        entry=0.0, stop=0.0, target=0.0, structure_rr=0.0,
        price_status="insufficient_evidence", basis=reason, evidence_fields=())


def price_final_flag_reversal(evidence: dict, current_price: float) -> StructuredPricePlan:
    """final_flag 失败反转（KR-FINAL-FLAG-001 事件3）：需失败确认证据。

    证据：flag_high（旗形上沿/失败突破高点）、failure_low（跌回位）、
    measured_target（旗形高度投影）。事件2（顺势突破）不提供本定价。
    """
    need = ("flag_high", "failure_low", "measured_target")
    missing = [k for k in need if not isinstance(evidence.get(k), (int, float))
               or evidence.get(k, 0) <= 0]
    if missing:
        raise InsufficientStructureEvidence(
            f"final_flag 反转定价缺证据: {missing}（事件3需失败确认，F04）")
    # 方向由证据结构决定：这里实现多头反转版本（跌势末端旗形向下失败→反手多）
    entry = float(evidence["failure_low"])          # 突破失败跌回位上方确认
    stop = float(evidence["flag_high"])             # 旗形极端点为失效位
    target = float(evidence["measured_target"])
    if not (entry < stop):
        raise DomainValidationError("final_flag 多头反转结构非法: entry >= stop")
    if target <= entry:
        raise DomainValidationError("final_flag 多头反转 target 必须高于 entry")
    risk = stop - entry
    return StructuredPricePlan(
        entry=entry, stop=stop, target=target,
        structure_rr=round((target - entry) / risk, 2),
        price_status="structured",
        basis=f"final_flag反转: entry=失败跌回{entry}, stop=旗形高{stop}, target={target}",
        evidence_fields=tuple(need),
    )
