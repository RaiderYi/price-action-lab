"""统一 setup 状态机（S4-06，F06）：预测不得直接成交。

任务书 §4 SignalEvent 协议：raw → qualified → armed → triggered，
WAIT 不成交；过期不复活；同结构不重复开仓；多空冲突显式输出。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set

from pal.domain.models import DomainValidationError, SignalState


class IllegalTransitionError(RuntimeError):
    """状态机非法跃迁（例如 expired → armed 复活）。"""


# 合法跃迁表
_TRANSITIONS: Dict[SignalState, Set[SignalState]] = {
    SignalState.RAW: {SignalState.QUALIFIED, SignalState.REJECTED, SignalState.EXPIRED},
    SignalState.QUALIFIED: {SignalState.ARMED, SignalState.REJECTED, SignalState.EXPIRED},
    SignalState.ARMED: {SignalState.TRIGGERED, SignalState.REJECTED, SignalState.EXPIRED},
    SignalState.TRIGGERED: set(),          # 终态：转手给订单域
    SignalState.REJECTED: set(),           # 终态
    SignalState.EXPIRED: set(),            # 终态（不复活，但既有成交不抹除）
}


@dataclass
class SignalStateMachine:
    """单个 setup 的信号生命周期。"""
    setup_id: str
    state: SignalState = SignalState.RAW
    expires_at: Optional[datetime] = None
    transition_log: list = field(default_factory=list)
    _cooldown_family: str = ""

    def transition(self, new_state: SignalState, at: datetime,
                   reason: str = "") -> None:
        if new_state not in _TRANSITIONS[self.state]:
            raise IllegalTransitionError(
                f"{self.setup_id}: 非法跃迁 {self.state.value} → {new_state.value}"
                + (f"（终态不可复活）" if not _TRANSITIONS[self.state] else ""))
        if new_state == SignalState.EXPIRED:
            if self.expires_at is not None and at < self.expires_at:
                # 允许提前失效（结构破坏），记录
                pass
        self.transition_log.append((self.state, new_state, at, reason))
        self.state = new_state

    def on_bar(self, at: datetime) -> None:
        """时间推进：过期自动迁移（EXPIRED 是终态，复活=新 setup 新ID）。"""
        if self.state in (SignalState.TRIGGERED, SignalState.REJECTED, SignalState.EXPIRED):
            return
        if self.expires_at is not None and at > self.expires_at:
            self.transition(SignalState.EXPIRED, self.expires_at, "timeout")


class SetupBook:
    """同票 setup 集合：去重、冷却、多空冲突。"""

    def __init__(self, cooldown_bars: int = 3):
        self.cooldown_bars = cooldown_bars
        self._setups: Dict[str, SignalStateMachine] = {}
        self._last_trigger_bar: Dict[str, int] = {}   # family → bar_idx

    def register(self, setup_id: str, expires_at: Optional[datetime]) -> SignalStateMachine:
        """幂等注册：同 ID 已存在返回既有实例（同结构不重复开仓）。"""
        if setup_id in self._setups:
            return self._setups[setup_id]
        sm = SignalStateMachine(setup_id=setup_id, expires_at=expires_at)
        self._setups[setup_id] = sm
        return sm

    def in_cooldown(self, family: str, bar_idx: int) -> bool:
        last = self._last_trigger_bar.get(family)
        return last is not None and (bar_idx - last) < self.cooldown_bars

    def mark_triggered(self, family: str, bar_idx: int) -> None:
        self._last_trigger_bar[family] = bar_idx

    def conflict_check(self, long_families: Set[str],
                       short_families: Set[str]) -> Optional[str]:
        """同票多空并存检测（显式输出，不静默择一）。"""
        both = long_families & short_families
        if both:
            return f"DIRECTION_CONFLICT: {sorted(both)} 同时 armed 多空两侧"
        return None

    def active_setups(self) -> list:
        return [s for s in self._setups.values()
                if s.state not in (SignalState.REJECTED, SignalState.EXPIRED)]
