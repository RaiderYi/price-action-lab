"""复权与企业行动分离（S2-05）。

红线（任务书 §4/Fill 协议）：
- 原始可成交价（raw）与研究调整价（adjusted）是两个坐标系；
- 账本/成交只允许 raw；结构分析可用 adjusted，但点位换算回 raw 才能下单；
- 除权信息按 ex-date 生效，禁止使用未来企业行动（as-of 因果）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Sequence

from pal.domain.models import DomainValidationError, require_positive_price


@dataclass(frozen=True)
class CorporateAction:
    kind: str               # "cash_dividend" | "split" | "bonus_share" | ...
    instrument_id: str
    ex_date: date          # 除权除息日（生效日）
    cash_per_share: float = 0.0
    share_factor: float = 1.0   # 拆股/送转：每 1 股变 share_factor 股

    def __post_init__(self):
        if self.share_factor <= 0:
            raise DomainValidationError("share_factor 必须为正")
        if self.cash_per_share < 0:
            raise DomainValidationError("现金分红不能为负")
        if self.kind not in ("cash_dividend", "split", "bonus_share"):
            raise DomainValidationError(f"未知企业行动类型: {self.kind}")


class AdjustmentSeries:
    """按 ex-date 排序的企业行动序列，支持 as-of 前向复权因子。"""

    def __init__(self, actions: Sequence[CorporateAction]):
        self._actions = sorted(actions, key=lambda a: a.ex_date)

    def actions_between(self, start: date, end: date) -> List[CorporateAction]:
        return [a for a in self._actions if start <= a.ex_date <= end]

    def forward_factor(self, asof: date) -> float:
        """研究调整因子：把 asof 之前的价格调整到可比口径。

        简化模型（前向）：cash_dividend 按 (p - d)/p 折算需当时价格，
        此处只对 split/bonus_share 给出确定性因子；现金分红调整
        需价格信息，由上层带价格调用 adjusted_price。
        """
        f = 1.0
        for a in self._actions:
            if a.ex_date <= asof:
                f *= a.share_factor
        return f

    def raw_to_research(self, price: float, asof: date) -> float:
        require_positive_price(price, "price")
        return price / self.forward_factor(asof)

    def research_to_raw(self, adjusted_price: float, asof: date) -> float:
        """研究点位 → 当时 raw 坐标（下单必须用这个）。"""
        require_positive_price(adjusted_price, "adjusted_price")
        return adjusted_price * self.forward_factor(asof)


def apply_action_to_position(qty: int, avg_cost: float,
                             action: CorporateAction) -> tuple:
    """企业行动对持仓的作用（账本侧，S5 将复用）。

    返回 (new_qty, new_avg_cost, cash_credit)。
    split/bonus_share：数量×factor，成本相应摊薄；
    cash_dividend：数量不变，现金入账（税按规则层另算，此处毛额）。
    """
    if qty <= 0:
        raise DomainValidationError("持仓数量必须为正")
    if action.kind in ("split", "bonus_share"):
        new_qty = int(qty * action.share_factor)
        new_cost = (qty * avg_cost) / new_qty if new_qty else 0.0
        return new_qty, new_cost, 0.0
    if action.kind == "cash_dividend":
        return qty, avg_cost, qty * action.cash_per_share
    raise DomainValidationError(f"未处理类型: {action.kind}")
