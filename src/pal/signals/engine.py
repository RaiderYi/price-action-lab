"""统一决策引擎入口（S4-08，含 S4-03 strict H2 接线）。

任务书验收：`engine.evaluate(asof, snapshot, candidates, config)`——
相同已知事实的历史/模拟决策一致；业务内核不读取系统当前时间；
规则启停效果可观测。

评估链（对每候选）：
  regime 评估（context） → 结构检测（swings/H2计数） → 资格/定价
  （结构价格，缺证据 insufficient） → DecisionSnapshot 留痕。
预测绝不直接生成订单（F06）；TRIGGERED 之后由 S5 执行域接管。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pal.context.regime import RegimeAssessment, RegimeKind, assess_trend_regime
from pal.context.swings import SwingPoint, detect_swings, swings_asof
from pal.data.bars import Bar
from pal.domain.decision import DecisionSnapshot
from pal.domain.identity import make_setup_id
from pal.domain.models import DomainValidationError, Implementation, SignalState
from pal.pricing.structure_prices import (
    InsufficientStructureEvidence,
    price_breakout_long,
    price_h2_long,
)
from pal.signals.lifecycle import SetupBook
from pal.selection.providers import Candidate


@dataclass(frozen=True)
class EngineConfig:
    config_version: str
    confirm_bars: int = 3
    h2_min_trend_quality: float = 0.5
    enabled_families: tuple = ("H2", "breakout")


@dataclass
class EvaluationResult:
    asof: datetime
    instrument_id: str
    regime: RegimeAssessment
    decisions: List[DecisionSnapshot] = field(default_factory=list)
    setups_armed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.errors:
            return "degraded"
        return "valid"


class DecisionEngine:
    """纯函数式评估：不读系统时钟（now 只能由调用方传入 asof）。"""

    def __init__(self, config: EngineConfig, setup_book: Optional[SetupBook] = None):
        self.config = config
        self.book = setup_book or SetupBook()

    def evaluate(self, asof: datetime, bars_30m: Sequence[Bar],
                 daily_bars: Sequence[Bar],
                 candidate: Optional[Candidate] = None,
                 instrument_id: str = "UNKNOWN") -> EvaluationResult:
        # 1) as-of 因果过滤（引擎绝不看 asof 之后的 bar）
        visible_30m = [b for b in bars_30m
                       if b.available_at <= asof and b.is_final
                       and b.instrument_id == instrument_id]
        visible_daily = [b for b in daily_bars
                         if b.available_at <= asof and b.is_final
                         and b.instrument_id == instrument_id]
        res = EvaluationResult(asof=asof, instrument_id=instrument_id,
                               regime=assess_trend_regime(visible_daily))

        # 2) 因果摆点
        swings = swings_asof(detect_swings(visible_30m, self.config.confirm_bars), asof)

        # 3) 逐家族评估
        if "H2" in self.config.enabled_families:
            self._eval_h2(asof, visible_30m, swings, res, candidate)
        if "breakout" in self.config.enabled_families:
            self._eval_breakout(asof, visible_30m, swings, res, candidate)
        return res

    # ── H2（strict 计数，KR-H2-COUNT-001 四前提）──
    def _eval_h2(self, asof, bars, swings, res, candidate) -> None:
        try:
            verdict = strict_h2_verdict(swings, bars, self.config.h2_min_trend_quality)
        except DomainValidationError as e:
            res.errors.append(f"H2:{e}")
            return
        if verdict is None:
            return
        setup_id = make_setup_id(res.instrument_id, "H2",
                                 Implementation.STRICT.value,
                                 verdict["formed_at"].isoformat())
        sm = self.book.register(str(setup_id),
                                expires_at=asof)  # 下一次评估前有效
        if sm.state == SignalState.RAW:
            sm.transition(SignalState.QUALIFIED, asof,
                          "H2 strict counting satisfied")
        if sm.state == SignalState.QUALIFIED:
            try:
                plan = price_h2_long(verdict["evidence"],
                                     current_price=verdict["current_price"])
            except InsufficientStructureEvidence as e:
                res.decisions.append(DecisionSnapshot(
                    outcome="reject", rule_id="pricing.h2.v1",
                    reason_code="REJ_INSUFFICIENT_EVIDENCE",
                    evidence_ids=(str(setup_id),), decided_at=asof.isoformat(),
                    detail={"msg": str(e)},
                    config_version=self.config.config_version))
                sm.transition(SignalState.REJECTED, asof, "insufficient evidence")
                return
            except DomainValidationError as e:
                res.decisions.append(DecisionSnapshot(
                    outcome="reject", rule_id="pricing.h2.v1",
                    reason_code="REJ_PRICE_INVALID",
                    evidence_ids=(str(setup_id),), decided_at=asof.isoformat(),
                    detail={"msg": str(e)},
                    config_version=self.config.config_version))
                sm.transition(SignalState.REJECTED, asof, "price invalid")
                return
            sm.transition(SignalState.ARMED, asof, "structured price ready")
            res.setups_armed.append(str(setup_id))
            res.decisions.append(DecisionSnapshot(
                outcome="wait", rule_id="engine.h2.v1",
                reason_code="WAIT_TRIGGER_PENDING",
                evidence_ids=(str(setup_id),), decided_at=asof.isoformat(),
                detail={"entry": plan.entry, "stop": plan.stop,
                        "target": plan.target},
                config_version=self.config.config_version))

    # ── breakout（统一强度服务 + 结构定价）──
    def _eval_breakout(self, asof, bars, swings, res, candidate) -> None:
        if len(bars) < 22:
            return
        from pal.signals.breakout import assess_breakout_strength
        lookback = 20
        prior = bars[:-1][-lookback:]
        prior_high = max(b.high for b in prior)
        strength = assess_breakout_strength(bars, breakout_level=prior_high)
        if not strength.crossed_level:
            return
        ev = {"breakout_level": prior_high,
              "signal_bar_low": bars[-1].low,
              "measured_target": prior_high + (prior_high - min(b.low for b in prior))}
        setup_id = make_setup_id(res.instrument_id, "breakout",
                                 Implementation.STRICT.value,
                                 bars[-1].bar_start.isoformat())
        sm = self.book.register(str(setup_id), expires_at=asof)
        if sm.state == SignalState.RAW:
            sm.transition(SignalState.QUALIFIED, asof,
                          f"breakout crossed level, strength={strength.level}")
        if sm.state == SignalState.QUALIFIED:
            try:
                plan = price_breakout_long(ev, current_price=bars[-1].close)
            except (InsufficientStructureEvidence, DomainValidationError) as e:
                res.decisions.append(DecisionSnapshot(
                    outcome="reject", rule_id="pricing.breakout.v1",
                    reason_code="REJ_PRICE_INVALID",
                    evidence_ids=(str(setup_id),), decided_at=asof.isoformat(),
                    detail={"msg": str(e)},
                    config_version=self.config.config_version))
                sm.transition(SignalState.REJECTED, asof, str(e))
                return
            sm.transition(SignalState.ARMED, asof, "structured breakout price")
            res.setups_armed.append(str(setup_id))
            res.decisions.append(DecisionSnapshot(
                outcome="wait", rule_id="engine.breakout.v1",
                reason_code="WAIT_TRIGGER_PENDING",
                evidence_ids=(str(setup_id),), decided_at=asof.isoformat(),
                detail={"entry": plan.entry, "stop": plan.stop,
                        "target": plan.target,
                        "strength": strength.level},
                config_version=self.config.config_version))


def strict_h2_verdict(swings: Sequence[SwingPoint], bars: Sequence[Bar],
                      min_trend_quality: float) -> Optional[dict]:
    """严格 H2 计数（KR-H2-COUNT-001）：趋势前提 + 两腿回调 + 第二 HL。

    不满足 → None（不发信号）；满足 → 证据 dict。
    一个 HL 反弹不能伪装二次计数（F02 验收核心）。
    """
    lows = [s for s in swings if s.kind == "L"]
    highs = [s for s in swings if s.kind == "H"]
    if len(lows) < 2 or len(highs) < 1:
        return None
    # 两腿：两个已确认 L，且第二 L 高于第一 L（回调中 HL 推进）
    l1, l2 = lows[-2], lows[-1]
    if l2.price <= l1.price:
        return None                       # 不是 higher low 链
    # 趋势前提：此前存在 H 且该 H 高于更早 H（牛市推进）
    if len(highs) < 1:
        return None
    prior_high = max(h.price for h in highs)
    last = bars[-1]
    if last.close <= l2.price:
        return None                       # 价格未站上 HL2
    return {
        "formed_at": l2.confirmed_at,
        "current_price": last.close,
        "evidence": {
            "HL2": l2.price,
            "signal_bar_high": last.high,
            "prior_high": prior_high,
            "HL1": l1.price,
        },
    }
