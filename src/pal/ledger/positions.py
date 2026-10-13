"""持仓与账本（S5-05/S5-06）：T+1 分批 + 现金/费用/NAV。

红线：
- 当日买入不可当日卖（T+1，sellable_from 下一交易日）；
- 分批买入分批记录可卖量；
- 现金守恒；费用不双计；NAV = cash + Σ qty×mark。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from pal.domain.models import DomainValidationError
from pal.execution.market_rules import MarketRuleSet


@dataclass
class PositionLot:
    """一个买入批次（S5-05）。"""
    lot_id: str
    instrument_id: str
    qty: int
    cost_price: float            # 含费摊薄成本
    acquired_date: date
    sellable_from: date          # T+1：下一交易日

    def sellable_qty(self, on: date) -> int:
        return self.qty if on >= self.sellable_from else 0


@dataclass
class CashMovement:
    kind: str        # "buy" | "sell" | "commission" | "stamp_tax" | "dividend" ...
    amount: float    # 正=入账 负=出账
    note: str = ""


class PositionBook:
    """多票持仓（lot 级）。"""
    def __init__(self):
        self._lots: Dict[str, List[PositionLot]] = {}

    def add_lot(self, lot: PositionLot) -> None:
        if lot.qty <= 0:
            raise DomainValidationError("lot qty 必须为正")
        self._lots.setdefault(lot.instrument_id, []).append(lot)

    def total_qty(self, instrument_id: str) -> int:
        return sum(l.qty for l in self._lots.get(instrument_id, []))

    def sellable_qty(self, instrument_id: str, on: date) -> int:
        """T+1 可卖量：只计 sellable_from <= on 的批次。"""
        return sum(l.sellable_qty(on) for l in self._lots.get(instrument_id, []))

    def reduce(self, instrument_id: str, qty: int, on: date) -> List[PositionLot]:
        """卖出扣减（FIFO；不可卖出部分抛错——不能卖没有的量）。"""
        if qty <= 0:
            raise DomainValidationError("卖出数量必须为正")
        if qty > self.sellable_qty(instrument_id, on):
            raise DomainValidationError(
                f"T+1可卖量不足: 欲卖{qty}, 可卖{self.sellable_qty(instrument_id, on)} "
                f"@{on}（当日买入不可当日卖出）")
        remaining = qty
        consumed = []
        for lot in self._lots.get(instrument_id, []):
            if remaining == 0:
                break
            avail = lot.sellable_qty(on)
            take = min(avail, remaining)
            if take:
                lot.qty -= take
                remaining -= take
                consumed.append(lot)
        self._lots[instrument_id] = [l for l in self._lots[instrument_id] if l.qty > 0]
        return consumed

    def reduce_by_lot(self, instrument_id: str, qty: int, on: date,
                      lot_id: str) -> List[PositionLot]:
        """R6-05：按 lot_id 精确扣减——退出计划不串扣批次。"""
        if qty <= 0:
            raise DomainValidationError("卖出数量必须为正")
        lot = next((l for l in self._lots.get(instrument_id, [])
                    if l.lot_id == lot_id), None)
        if lot is None:
            raise DomainValidationError(f"lot 不存在: {lot_id}")
        avail = lot.sellable_qty(on)
        if qty > avail:
            raise DomainValidationError(
                f"本 lot 可卖量不足: 欲卖{qty}, lot {lot_id} 可卖{avail}"
                f" @{on}（T+1/不串扣其他批次）")
        lot.qty -= qty
        self._lots[instrument_id] = [l for l in self._lots.get(
            instrument_id, []) if l.qty > 0]
        return [lot]

    def reduce_batch(self, instrument_id: str, qty: int, on: date,
                     acquired_date: date) -> List[PositionLot]:
        """V07/AR07：按买入批次卖出——只动 acquired_date 匹配的 lot。

        新批计划不得串卖旧批；不可卖部分抛错（调用方保留计划）。
        """
        if qty <= 0:
            raise DomainValidationError("卖出数量必须为正")
        batch = [l for l in self._lots.get(instrument_id, [])
                 if l.acquired_date == acquired_date]
        avail = sum(l.sellable_qty(on) for l in batch)
        if qty > avail:
            raise DomainValidationError(
                f"本批次可卖量不足: 欲卖{qty}, 批次{acquired_date}可卖{avail}"
                f" @ {on}（V07：不串卖其他批次）")
        remaining = qty
        consumed = []
        for lot in batch:
            if remaining == 0:
                break
            take = min(lot.sellable_qty(on), remaining)
            if take:
                lot.qty -= take
                remaining -= take
                consumed.append(lot)
        self._lots[instrument_id] = [l for l in self._lots.get(
            instrument_id, []) if l.qty > 0]
        return consumed

    def mark_value(self, marks: Dict[str, float]) -> float:
        total = 0.0
        for iid, lots in self._lots.items():
            if not lots:
                continue    # 已清仓的 key 不要求市价
            px = marks.get(iid)
            if px is None:
                raise DomainValidationError(f"无 {iid} 市价，NAV 无法计算")
            total += sum(l.qty * px for l in lots)
        return total


class AccountLedger:
    """现金+持仓+费用账本（S5-06）。

    费用规则（以 MarketRuleSet 为准，示例）：
    - 买入：佣金 = max(成交额×commission_bps/10000, min_commission)
    - 卖出：佣金 + 印花税 = 成交额×stamp_tax_sell_bps/10000
    """
    def __init__(self, initial_cash: float):
        if initial_cash <= 0:
            raise DomainValidationError("初始资金必须为正")
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions = PositionBook()
        self.movements: List[CashMovement] = []
        self._fee_paid: Dict[str, float] = {"commission": 0.0, "stamp_tax": 0.0}

    def _record(self, kind: str, amount: float, note: str = "") -> None:
        self.cash += amount
        self.movements.append(CashMovement(kind, round(amount, 4), note))

    def buy(self, instrument_id: str, qty: int, price: float,
            trade_date: date, rules: MarketRuleSet,
            t1_next_trading_day: date,
            lot_id: str = "") -> None:
        if qty <= 0 or price <= 0:
            raise DomainValidationError("买入参数非法")
        # R10：T+1 边界强制——sellable_from 必须 > 买入日
        if t1_next_trading_day <= trade_date:
            raise DomainValidationError(
                f"非法 sellable_from({t1_next_trading_day}) ≤ 买入日"
                f"({trade_date})：T+1 约束由账本强制（R10）")
        gross = qty * price
        commission = max(gross * rules.commission_bps / 10000, rules.min_commission)
        total_cost = gross + commission
        if total_cost > self.cash:
            raise DomainValidationError(
                f"资金不足: 需{total_cost:.2f}, 现金{self.cash:.2f}（不隐含杠杆）")
        self._record("buy", -gross, f"{instrument_id} {qty}@{price}")
        self._record("commission", -commission, f"buy {instrument_id}")
        self._fee_paid["commission"] += commission
        # R6-05：lot_id 由唯一 fill 派生（调用方传入）；缺省保留
        # 旧格式（日期+数量）以兼容历史测试
        if not lot_id:
            lot_id = (f"lot_{instrument_id}_"
                      f"{trade_date.isoformat()}_{qty}")
        self.positions.add_lot(PositionLot(
            lot_id=lot_id,
            instrument_id=instrument_id, qty=qty,
            cost_price=total_cost / qty, acquired_date=trade_date,
            sellable_from=t1_next_trading_day))

    def sell(self, instrument_id: str, qty: int, price: float,
             trade_date: date, rules: MarketRuleSet) -> float:
        """卖出：先扣可卖量（T+1），再入账净额。返回净入账。"""
        if qty <= 0 or price <= 0:
            raise DomainValidationError("卖出参数非法")
        self.positions.reduce(instrument_id, qty, trade_date)
        return self._post_sell(instrument_id, qty, price, trade_date, rules)

    def sell_batch(self, instrument_id: str, qty: int, price: float,
                   trade_date: date, rules: MarketRuleSet,
                   acquired_date: date) -> float:
        """V07：按批次卖出（退出计划专用）。"""
        if qty <= 0 or price <= 0:
            raise DomainValidationError("卖出参数非法")
        self.positions.reduce_batch(instrument_id, qty, trade_date,
                                    acquired_date)
        return self._post_sell(instrument_id, qty, price, trade_date, rules)

    def sell_by_lot(self, instrument_id: str, qty: int, price: float,
                    trade_date: date, rules: MarketRuleSet,
                    lot_id: str) -> float:
        """R6-05：按 lot 卖出（退出计划专用——精确批次关联）。"""
        if qty <= 0 or price <= 0:
            raise DomainValidationError("卖出参数非法")
        self.positions.reduce_by_lot(instrument_id, qty, trade_date, lot_id)
        return self._post_sell(instrument_id, qty, price, trade_date, rules)

    def _post_sell(self, instrument_id: str, qty: int, price: float,
                   trade_date: date, rules: MarketRuleSet) -> float:
        gross = qty * price
        commission = max(gross * rules.commission_bps / 10000, rules.min_commission)
        stamp = gross * rules.stamp_tax_sell_bps / 10000
        net = gross - commission - stamp
        self._record("sell", gross, f"{instrument_id} {qty}@{price}")
        self._record("commission", -commission, f"sell {instrument_id}")
        self._record("stamp_tax", -stamp, f"sell {instrument_id}")
        self._fee_paid["commission"] += commission
        self._fee_paid["stamp_tax"] += stamp
        return net

    def nav(self, marks: Dict[str, float]) -> float:
        return self.cash + self.positions.mark_value(marks)

    def cash_conservation_check(self, marks: Dict[str, float]) -> bool:
        """现金守恒审计：Σmovements == cash - initial（精确到分）。"""
        s = sum(m.amount for m in self.movements)
        return abs((self.initial_cash + s) - self.cash) < 0.005
