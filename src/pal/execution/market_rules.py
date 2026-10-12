"""市场交易规则（S5-01）与订单状态机（S5-02）。

规则版本化：按交易所/板块/生效日（任务书：2026 修订版交易规则，
实施时以官方发布核验，不用早期常量代替全时期）。
首版实现主板核心约束（价格限制/T+1/最小单位），生效日显式。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from pal.domain.models import DomainValidationError


# ═══════════════════════════════════════════════════════════
# S5-01: 版本化市场规则
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MarketRuleSet:
    """某板块某生效区间的交易规则快照。"""
    exchange: str           # "SSE" | "SZSE"
    board: str              # "main" | "chinext" | "star"
    effective_from: date
    rules_version: str      # 官方规则版本标注（人工核验后登记）
    price_limit_pct: float  # 涨跌停幅度（主板10%；ST另算由 flag 承载）
    st_price_limit_pct: float
    min_price_tick: float   # 最小价位
    lot_size: int           # 申报数量单位（100股）
    t_plus: int             # 交收制度：1 = T+1
    commission_bps: float   # 佣金（双边，万分比示例值，实际以券商为准）
    min_commission: float
    stamp_tax_sell_bps: float   # 印花税（卖出单边）

    def __post_init__(self):
        if self.price_limit_pct <= 0 or self.t_plus < 1:
            raise DomainValidationError("规则参数非法")
        if self.lot_size < 1:
            raise DomainValidationError("lot_size 非法")


# 主板基准规则（生效区间示例；正式使用前须按 S5-01 验收核验官方来源
# 并登记 rules_version——此处版本号标注为未核验）
MAIN_BOARD = MarketRuleSet(
    exchange="*", board="main", effective_from=date(2026, 1, 1),
    rules_version="UNVERIFIED-2026-baseline",
    price_limit_pct=0.10, st_price_limit_pct=0.05,
    min_price_tick=0.01, lot_size=100, t_plus=1,
    commission_bps=2.5, min_commission=5.0, stamp_tax_sell_bps=5.0,
)


class RuleBook:
    """规则查询：as-of + 板块 → 规则集。"""
    def __init__(self):
        self._sets = []

    def register(self, rs: MarketRuleSet) -> None:
        self._sets.append(rs)
        self._sets.sort(key=lambda r: r.effective_from)

    def rules_for(self, board: str, asof: date) -> MarketRuleSet:
        cands = [r for r in self._sets
                 if r.board in (board, "*") and r.effective_from <= asof]
        if not cands:
            raise KeyError(f"无适用规则: board={board} asof={asof}")
        return cands[-1]


# ═══════════════════════════════════════════════════════════
# S5-02: 订单状态机（事件时钟）
# ═══════════════════════════════════════════════════════════

class OrderState(str, Enum):
    INTENT = "intent"          # 意图（引擎产出）
    SUBMITTED = "submitted"    # 已受理
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


_ORDER_TRANSITIONS = {
    OrderState.INTENT: {OrderState.SUBMITTED, OrderState.REJECTED, OrderState.CANCELLED},
    OrderState.SUBMITTED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED,
                           OrderState.CANCELLED, OrderState.REJECTED},
    OrderState.PARTIALLY_FILLED: {OrderState.FILLED, OrderState.CANCELLED,
                                  OrderState.REJECTED},
    OrderState.FILLED: set(),
    OrderState.CANCELLED: set(),
    OrderState.REJECTED: set(),
}


class OrderTransitionError(RuntimeError):
    pass


@dataclass
class Order:
    order_id: str
    plan_id: str
    side: str                # "buy" | "sell"
    order_type: str          # "market" | "limit" | "stop"
    qty: int
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    state: OrderState = OrderState.INTENT
    filled_qty: int = 0
    avg_fill_price: float = 0.0

    def __post_init__(self):
        if self.side not in ("buy", "sell"):
            raise DomainValidationError(f"side 非法: {self.side}")
        if self.order_type not in ("market", "limit", "stop"):
            raise DomainValidationError(f"order_type 非法: {self.order_type}")
        if self.qty <= 0:
            raise DomainValidationError("qty 必须为正")

    def transition(self, new_state: OrderState) -> None:
        if new_state not in _ORDER_TRANSITIONS[self.state]:
            raise OrderTransitionError(
                f"{self.order_id}: 非法订单跃迁 {self.state.value}→{new_state.value}")
        self.state = new_state

    def apply_fill(self, qty: int, price: float) -> None:
        """部分/全部成交累计（加权均价）。"""
        if qty <= 0 or price <= 0:
            raise DomainValidationError("成交数量/价格非法")
        if self.filled_qty + qty > self.qty:
            raise DomainValidationError(
                f"超量成交: {self.filled_qty}+{qty} > {self.qty}")
        total = self.filled_qty + qty
        self.avg_fill_price = (
            (self.avg_fill_price * self.filled_qty + price * qty) / total)
        self.filled_qty = total
        self.state = (OrderState.FILLED if self.filled_qty == self.qty
                      else OrderState.PARTIALLY_FILLED)

    def remaining(self) -> int:
        return self.qty - self.filled_qty
