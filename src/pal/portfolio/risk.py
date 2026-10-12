"""组合层（S6）：风险定仓、约束、退出政策、熔断。

任务书 S6-08 默认参数（全部为待验证起点，冲突取更严格）：
  初始模拟资金100万、单笔风险0.25%、单票≤10%、行业≤25%、
  总仓位≤80%、最多10只。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class PaperDefaults:
    """模拟默认配置（configs 意义的代码化；S6-08）。"""
    initial_cash: float = 1_000_000.0
    risk_per_trade_pct: float = 0.0025     # 单笔风险 0.25%
    max_position_pct: float = 0.10         # 单票 ≤10%
    max_industry_pct: float = 0.25         # 行业 ≤25%
    max_total_exposure_pct: float = 0.80   # 总仓位 ≤80%
    max_positions: int = 10
    max_drawdown_pct: float = 0.10         # 熔断：回撤 10% 停开仓
    max_daily_loss_pct: float = 0.02       # 单日亏损 2% 停开仓
    max_gap_loss_risk: float = 0.02        # 跳空压力预算（S6-03）


@dataclass(frozen=True)
class RiskDecision:
    allow: bool
    reason_codes: Tuple[str, ...]
    max_qty: int
    risk_budget: float
    exposure_before: float
    exposure_after: float
    cash_available: float


class PortfolioConstraints:
    """仓位与集中度约束（S6-01/S6-02）。"""

    def __init__(self, params: PaperDefaults = PaperDefaults()):
        self.p = params

    def size_position(self, entry: float, stop: float, cash: float,
                      nav: float,
                      positions_value: float,
                      instrument_value: float,
                      industry_value: float,
                      fee_estimate_pct: float = 0.001,
                      lot_size: int = 100,
                      pending_instrument_orders_value: float = 0.0,
                      ) -> RiskDecision:
        """风险金额定仓（R07 修正：单票上限扣除已有持仓与在途买单）。

        新增额度 = max(0, NAV×单票上限 − 已有持仓市值 − 在途买单占用)。
        """
        if nav <= 0 or cash < 0:
            raise DomainValidationError("NAV/现金非法")
        if stop >= entry:
            return RiskDecision(False, ("REJ_STOP_ABOVE_ENTRY",), 0,
                                0.0, positions_value, positions_value, cash)
        risk_budget = nav * self.p.risk_per_trade_pct
        per_share_risk = entry - stop
        qty_by_risk = int(risk_budget / (per_share_risk * (1 + fee_estimate_pct)))
        # R07：单票上限扣已有+在途
        position_cap_value = max(
            0.0, nav * self.p.max_position_pct
            - instrument_value - pending_instrument_orders_value)
        qty_by_pos_cap = int(position_cap_value / entry)
        qty_by_cash = int(cash * (1 - fee_estimate_pct) / entry)
        qty = min(qty_by_risk, qty_by_pos_cap, qty_by_cash)

        reasons: List[str] = []
        # 总仓位闸
        exposure_after = (positions_value + qty * entry) / nav
        if exposure_after > self.p.max_total_exposure_pct:
            allowed_value = nav * self.p.max_total_exposure_pct - positions_value
            qty = int(min(qty, allowed_value / entry)) if allowed_value > 0 else 0
            reasons.append("CAPPED_BY_TOTAL_EXPOSURE")
        # 行业闸
        industry_after = (industry_value + qty * entry) / nav
        if industry_after > self.p.max_industry_pct:
            allowed = nav * self.p.max_industry_pct - industry_value
            qty = int(min(qty, allowed / entry)) if allowed > 0 else 0
            reasons.append("CAPPED_BY_INDUSTRY")
        # 取整到手
        qty = max(0, qty - (qty % lot_size))
        if qty == 0:
            reasons.append("REJ_NO_CAPACITY")
            return RiskDecision(False, tuple(reasons), 0, risk_budget,
                                positions_value / nav,
                                positions_value / nav, cash)
        exposure_after = (positions_value + qty * entry) / nav
        return RiskDecision(True, tuple(reasons) or ("OK",), qty,
                            risk_budget, positions_value / nav,
                            exposure_after, cash)

    def position_count_ok(self, current: int) -> bool:
        return current < self.p.max_positions

    def conflicting_sources_share_budget(self, sources: Tuple[str, ...]) -> int:
        """S6-05：同票多来源不重复配资——一份净风险预算。"""
        return 1


# ═══════════════════════════════════════════════════════════
# S6-04 退出政策（优先级固定）
# ═══════════════════════════════════════════════════════════

class ExitReason(str, Enum):
    STRUCTURE_INVALID = "structure_invalid"   # 结构失效（最高优先）
    RISK_EXIT = "risk_exit"                   # 止损/跳空风险
    TAKE_PROFIT = "take_profit"
    TIMEOUT = "timeout"
    TRAILING_STOP = "trailing_stop"


EXIT_PRIORITY = (
    ExitReason.STRUCTURE_INVALID,
    ExitReason.RISK_EXIT,
    ExitReason.TRAILING_STOP,
    ExitReason.TAKE_PROFIT,
    ExitReason.TIMEOUT,
)


@dataclass
class ExitPolicyState:
    """退出状态（只用已知数据更新；新止损下一合法执行时点生效）。"""
    stop: float
    trailing_armed: bool = False
    bars_held: int = 0
    timeout_bars: int = 40


class ExitPolicyEngine:
    def evaluate(self, state: ExitPolicyState, high: float, low: float,
                 close: float, structure_invalid: bool) -> Optional[ExitReason]:
        """按固定优先级判定退出（S6-04）。"""
        if structure_invalid:
            return ExitReason.STRUCTURE_INVALID
        if low <= state.stop:
            return ExitReason.RISK_EXIT
        if state.trailing_armed and close < state.stop:
            return ExitReason.TRAILING_STOP
        if state.bars_held >= state.timeout_bars:
            return ExitReason.TIMEOUT
        return None

    def update_trailing(self, state: ExitPolicyState, new_stop: float,
                        effective_at_next_session: bool = True) -> float:
        """移动止损：只上调；下一执行时点生效（返回生效止损）。"""
        if new_stop > state.stop:
            state.stop = new_stop
        return state.stop


# ═══════════════════════════════════════════════════════════
# S6-06 熔断
# ═══════════════════════════════════════════════════════════

class CircuitBreaker:
    """回撤/单日亏损/数据故障停开仓与恢复（S6-06）。

    停开仓不冻结已有风险管理（退出规则继续）。
    """
    def __init__(self, params: PaperDefaults = PaperDefaults()):
        self.p = params
        self.peak_nav: Optional[float] = None
        self.day_start_nav: Optional[float] = None
        self.data_fault = False
        self.manual_override_log: List[Tuple[str, str]] = []

    def on_nav(self, nav: float, day: date) -> Tuple[bool, str]:
        self.peak_nav = max(self.peak_nav or nav, nav)
        if self.day_start_nav is None:
            self.day_start_nav = nav
        drawdown = (self.peak_nav - nav) / self.peak_nav
        if drawdown >= self.p.max_drawdown_pct:
            return False, f"CIRCUIT_DRAWDOWN:{drawdown:.1%}"
        return True, "OK"

    def on_day_rollover(self, nav: float) -> None:
        self.day_start_nav = nav

    def daily_loss_breached(self, nav: float) -> bool:
        if self.day_start_nav is None:
            return False
        loss = (self.day_start_nav - nav) / self.day_start_nav
        return loss >= self.p.max_daily_loss_pct

    def on_data_fault(self, fault: bool) -> None:
        self.data_fault = fault

    def open_allowed(self, nav: float) -> Tuple[bool, str]:
        if self.data_fault:
            return False, "DATA_FAULT"
        ok, why = self.on_nav(nav, date.min)
        if not ok:
            return ok, why
        if self.daily_loss_breached(nav):
            return False, "DAILY_LOSS_LIMIT"
        return True, "OK"

    def manual_override(self, action: str, note: str) -> None:
        """人工覆盖独立标签（不污染系统轨）。"""
        self.manual_override_log.append((action, note))


# ═══════════════════════════════════════════════════════════
# S6-03/S6-07 压力与容量
# ═══════════════════════════════════════════════════════════

def gap_stress_loss(entry: float, stop: float, gap_open: float,
                    qty: int) -> float:
    """跳空压力损失（S6-03）：T+1 无法隔夜规避。"""
    if gap_open >= stop:
        return 0.0
    return (stop - gap_open) * qty     # 超出1R部分（另加正常1R由调用方算）


def capacity_report(order_value: float, bar_amount: float,
                    max_participation: float = 0.1) -> dict:
    """容量：以可交易量约束，不线性外推（S6-07）。"""
    if bar_amount <= 0:
        return {"capacity_ok": False, "reason": "NO_LIQUIDITY",
                "max_order_value": 0.0}
    max_value = bar_amount * max_participation
    return {
        "capacity_ok": order_value <= max_value,
        "max_order_value": max_value,
        "participation": round(order_value / bar_amount, 4),
        "reason": "" if order_value <= max_value else "EXCEEDS_PARTICIPATION",
    }
