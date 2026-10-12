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
    # R09：结构目标 = 前高（真实障碍位）。不为通过 RR 门强抬到 2R；
    # 若前高空间不足（prior_high <= entry），结构不成立——拒绝而非造目标。
    if prior_high <= entry:
        raise DomainValidationError(
            f"H2 结构空间不足: prior_high({prior_high}) <= entry({entry})；"
            f"不得人为抬高目标（R09）。固定2R退出属另一策略，须分开实验")
    target = prior_high
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

    R09 修正：本函数实现**空头反转**（上升趋势末端的旗形向下突破失败？
    否——事件3语义：上升趋势末端旗形**顺势向上突破失败后反转做空**
    不适配 A 股第一版（long-only）。多头反转版本要求方向自洽：
    entry（跌回位上方确认）> stop（旗形低点失效位），即熊市末端向下
    旗形向上失败 → 反手做多。字段语义改为：
      flag_low：向下旗形的低点（失效位=stop）
      failure_high：突破失败跌回前的高点（确认位=entry 上方触发）
      measured_target：旗形高度投影（必须 > entry）
    旧字段名 flag_high/failure_low 属方向错误——保留拒绝行为。
    """
    need = ("flag_low", "failure_high", "measured_target")
    missing = [k for k in need if not isinstance(evidence.get(k), (int, float))
               or evidence.get(k, 0) <= 0]
    if not missing:
        entry = float(evidence["failure_high"])       # 突破失败后回升确认位
        stop = float(evidence["flag_low"])            # 旗形极端点失效位
        target = float(evidence["measured_target"])
        if not (stop < entry):
            raise DomainValidationError(
                f"final_flag 多头反转结构非法: stop({stop}) >= entry({entry})")
        if target <= entry:
            raise DomainValidationError(
                f"final_flag 多头反转 target 必须高于 entry（R09 方向自洽）")
        risk = stop - entry if stop > entry else entry - stop
        # 多头：risk = entry - stop 不成立（stop<entry → risk=entry-stop 为负）？
        # 正确多头结构：stop < entry，risk = entry - stop > 0
        risk = entry - stop
        return StructuredPricePlan(
            entry=entry, stop=stop, target=target,
            structure_rr=round((target - entry) / risk, 2),
            price_status="structured",
            basis=f"final_flag多头反转: entry=失败回升{entry}, stop=旗形低{stop}, target={target}",
            evidence_fields=tuple(need),
        )
    # 旧字段（flag_high/failure_low）或缺失 → 拒绝（R09：方向倒挂禁止）
    raise InsufficientStructureEvidence(
        f"final_flag 反转定价证据缺失或方向字段非法（R09：需 "
        f"flag_low<failure_high<measured_target 的多头自洽结构）: "
        f"missing={missing or ['旧字段命名']}")
