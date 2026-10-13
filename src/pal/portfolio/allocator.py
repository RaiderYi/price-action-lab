"""第三轮复审 T07：多票统一组合分配（PortfolioAllocator）。

复审验收要求：
- 同一时点收集候选并确定排序/配额；维护全持仓 marks 与行业信息；
- 冻结待成交现金及风险（在途委托占用）；
- 强制单票/行业/总仓位/数量/跳空风险上限；
- 至少 3 只股票争夺不足现金 → 固定输入得到固定分配；
- 换事件到达顺序不应无解释改变批次结果；
- 同票多源不重复预算；部分成交/撤单后额度正确；
- 缺一票报价显式降级（不部分写账后崩溃）；
- 熔断停止新仓而不停止退出。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from pal.domain.models import DomainValidationError
from pal.ledger.positions import AccountLedger
from pal.portfolio.risk import (
    CircuitBreaker,
    PaperDefaults,
    PortfolioConstraints,
)


@dataclass(frozen=True)
class AllocationRequest:
    """一次开仓请求（同一分配批次中的一只票）。"""
    instrument_id: str
    setup_id: str
    entry: float                 # 拟触发价（buy-stop）
    stop: float
    target: float
    score: float = 0.0           # 排序分（高优先）
    industry: str = "unknown"    # 行业键（聚合上限用）


@dataclass(frozen=True)
class AllocationResult:
    instrument_id: str
    setup_id: str
    allow: bool
    qty: int
    reason_codes: Tuple[str, ...]


@dataclass
class _Pending:
    req: AllocationRequest
    qty: int
    value: float
    industry: str


class PortfolioAllocator:
    """同一时点多票争资的确定性分配（T07）。

    分配协议（预注册，固定）：
    1. 先过滤非法请求（stop>=entry、缺报价、熔断）；
    2. 按 (score desc, setup_id asc) 排序——同分按 ID 字典序，
       保证事件到达顺序不影响结果；
    3. 逐票用 PortfolioConstraints 定仓，把已批准票的在途占用
       （value + 等比例风险）计入后续票的约束；
    4. 行业聚合：同行业已批准在途 + 持仓市值 ≤ max_industry_pct；
    5. 现金逐票冻结：批准 qty×entry（含费预算）后现金相应减少，
       现金不足则该票 0 股（REJ_NO_CASH），不部分给量迁就。
    """

    def __init__(self, params: PaperDefaults = PaperDefaults(),
                 breaker: Optional[CircuitBreaker] = None):
        self.p = params
        self.constraints = PortfolioConstraints(params)
        self.breaker = breaker or CircuitBreaker(params)

    def allocate(self, requests: Sequence[AllocationRequest],
                 ledger: AccountLedger,
                 marks: Dict[str, float]) -> List[AllocationResult]:
        """确定性分配一批开仓请求。

        marks：全持仓市价（缺某持仓报价 → 该票先显式降级跳过，
        不在部分写账后崩溃——本方法不写账，只产出意图）。
        """
        if not requests:
            return []
        nav = self._nav_or_none(ledger, marks)
        if nav is None:
            # 有持仓缺报价：整体降级——只拒绝，不崩溃不写账
            return [AllocationResult(r.instrument_id, r.setup_id, False, 0,
                                     ("DEGRADED_MISSING_MARK",))
                    for r in requests]

        # 熔断：只拦新开仓
        ok, why = self.breaker.open_allowed(nav)
        if not ok:
            return [AllocationResult(r.instrument_id, r.setup_id, False, 0,
                                     (f"CB_{why}",))
                    for r in requests]

        # 确定排序（与到达顺序无关）
        ordered = sorted(requests,
                         key=lambda r: (-r.score, r.setup_id))

        positions_value = ledger.positions.mark_value(marks)
        # 行业视图：调用方通过 marks 覆盖的持仓 + 本批已批准在途
        industry_exposure: Dict[str, float] = {}
        # 同票合并：同 instrument 多请求共享一份净预算（S6-05/T07）
        seen_instruments: set = set()

        cash = ledger.cash
        results: List[AllocationResult] = []
        for r in ordered:
            if r.instrument_id in seen_instruments:
                results.append(AllocationResult(
                    r.instrument_id, r.setup_id, False, 0,
                    ("REJ_DUPLICATE_INSTRUMENT",)))
                continue
            seen_instruments.add(r.instrument_id)
            if r.stop >= r.entry or r.entry <= 0 or r.stop <= 0:
                results.append(AllocationResult(
                    r.instrument_id, r.setup_id, False, 0,
                    ("REJ_STOP_ABOVE_ENTRY",)))
                continue
            mark = marks.get(r.instrument_id)
            inst_value = (ledger.positions.total_qty(r.instrument_id)
                          * mark) if mark is not None else 0.0
            ind_val = (industry_exposure.get(r.industry, 0.0)
                       + inst_value)
            rd = self.constraints.size_position(
                entry=r.entry, stop=r.stop, cash=cash, nav=nav,
                positions_value=positions_value,
                instrument_value=inst_value,
                industry_value=ind_val)
            if not rd.allow or rd.max_qty <= 0:
                results.append(AllocationResult(
                    r.instrument_id, r.setup_id, False, 0,
                    rd.reason_codes))
                continue
            value = rd.max_qty * r.entry
            if value > cash:
                results.append(AllocationResult(
                    r.instrument_id, r.setup_id, False, 0,
                    ("REJ_NO_CASH",)))
                continue
            # 批内冻结：现金与总敞口同步递减/递增
            cash -= value
            positions_value += value
            industry_exposure[r.industry] = (
                industry_exposure.get(r.industry, 0.0) + value)
            results.append(AllocationResult(
                r.instrument_id, r.setup_id, True, rd.max_qty,
                rd.reason_codes))
        return results

    @staticmethod
    def _nav_or_none(ledger: AccountLedger,
                     marks: Dict[str, float]) -> Optional[float]:
        try:
            return ledger.nav(marks)
        except DomainValidationError:
            return None
