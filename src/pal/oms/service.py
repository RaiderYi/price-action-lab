"""AR09：订单管理服务（OMS）——生命周期、部分成交、撤单、占用。

职责（蓝图 §10.2 订单状态机 + §3 模块表）：
- 订单从 Intent 到终态的持久生命周期（不只是局部 Order 对象）；
- 一单多 fill（fill_id 去重，order_id 关联）；
- 撤单释放冻结额度；部分成交保留剩余量；
- 资金占用（reservation）与订单同生命周期。

首版实现：进程内 OMS（SQLite 事务化在 AR05 完整版落地前，
以 EventStore 持久化订单事件流）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from pal.domain.models import DomainValidationError
from pal.execution.market_rules import Order, OrderState


class OmsError(RuntimeError):
    pass


@dataclass
class Reservation:
    """资金/风险占用（AR08/蓝图 §6.1）。"""
    order_id: str
    instrument_id: str
    qty: int
    price: float           # 估价上界
    reserved_cash: float
    created_at: str
    released: bool = False
    converted_to_fill: int = 0     # 已转为成交的数量


class OrderManagementService:
    """OMS：订单生命周期 + 占用管理（AR09）。"""

    def __init__(self, store=None):
        self.store = store
        self.orders: Dict[str, Order] = {}
        self.reservations: Dict[str, Reservation] = {}

    # ── 提交 ──
    def submit(self, order: Order, reserve_cash: float,
               created_at: str = "") -> Reservation:
        """Intent → SUBMITTED + 冻结额度（本地事务提交点）。"""
        if order.state != OrderState.INTENT:
            raise OmsError(f"{order.order_id}: 只能提交 INTENT 订单")
        if order.order_id in self.orders:
            raise OmsError(f"重复订单: {order.order_id}")
        order.transition(OrderState.SUBMITTED)
        self.orders[order.order_id] = order
        r = Reservation(order.order_id, order.plan_id.split("_")[-1]
                        if "_" in order.plan_id else order.plan_id,
                        order.qty, order.stop_price or 0.0,
                        reserve_cash, created_at or datetime.utcnow().isoformat())
        self.reservations[order.order_id] = r
        if self.store is not None:
            self.store.append("order", {
                "order_id": order.order_id, "plan_id": order.plan_id,
                "side": order.side, "qty": order.qty,
                "order_type": order.order_type,
                "stop_price": order.stop_price,
                "limit_price": order.limit_price,
                "state": order.state.value}, ts=created_at)
        return r

    # ── 成交 ──
    def apply_fill(self, order_id: str, qty: int, price: float,
                   fill_id: str, event_at: str = "") -> None:
        """一单多 fill：fill_id 去重，占用转换。"""
        o = self.orders.get(order_id)
        if o is None:
            raise OmsError(f"未知订单: {order_id}")
        before = o.filled_qty
        o.apply_fill(qty, price, fill_id=fill_id, event_at=event_at)
        if o.filled_qty == before:
            return      # 幂等：重复 fill_id 已吞
        r = self.reservations.get(order_id)
        if r is not None:
            r.converted_to_fill = o.filled_qty

    # ── 撤单 ──
    def cancel(self, order_id: str) -> int:
        """撤余量：释放未成交占用，返回撤销量。"""
        o = self.orders.get(order_id)
        if o is None:
            raise OmsError(f"未知订单: {order_id}")
        remaining = o.remaining()
        if remaining <= 0:
            raise OmsError(f"{order_id}: 无余量可撤")
        o.transition(OrderState.CANCELLED)
        r = self.reservations.get(order_id)
        if r is not None:
            r.released = True
        return remaining

    # ── 查询 ──
    def reserved_cash_outstanding(self) -> float:
        """未释放且未完全成交的占用（可用现金扣减依据）。"""
        total = 0.0
        for r in self.reservations.values():
            if r.released:
                continue
            o = self.orders.get(r.order_id)
            if o is None or o.state in (OrderState.FILLED,
                                        OrderState.CANCELLED,
                                        OrderState.REJECTED):
                continue
            total += r.reserved_cash
        return total

    def pending_orders(self, instrument_id: Optional[str] = None
                       ) -> List[Order]:
        """在途订单（SUBMITTED/PARTIALLY_FILLED）。"""
        return [o for o in self.orders.values()
                if o.state in (OrderState.SUBMITTED,
                               OrderState.PARTIALLY_FILLED)
                and (instrument_id is None
                     or instrument_id in o.order_id)]
