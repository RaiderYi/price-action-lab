"""证券主数据（S2-02，F22）。

问题：688120 被回测报告写成"华大九天"（实为华海清科）——名称靠人工
填写出错。主数据缺失还导致"以今天成分股回测过去"的幸存者偏差无法
防范。

设计：
- SecurityMaster 是唯一名称/板块/风险状态出口（报告层禁止手填名称）；
- 属性带历史生效区间（list/delist/ST/行业），查询一律 as-of；
- 未知代码显式 UnknownSecurity 错误，不静默猜名称。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from pal.domain.models import DomainValidationError, InstrumentId


class UnknownSecurityError(KeyError):
    """主数据中无此代码——报告层不得自行编造名称。"""


@dataclass(frozen=True)
class SecurityProfile:
    """单一时点的证券属性。"""
    instrument: InstrumentId
    name: str                    # 官方证券简称
    is_st: bool = False
    industry: Optional[str] = None
    suspended: bool = False      # 停牌（as-of）

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise DomainValidationError("证券名称不能为空（F22：禁止无主数据名称）")


@dataclass(frozen=True)
class SecurityLifecycle:
    instrument: InstrumentId
    list_date: date
    delist_date: Optional[date]     # None = 仍在市（as-of 主数据版本时点）
    name: str
    board: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise DomainValidationError("证券名称不能为空（F22：禁止无主数据名称）")
        if self.delist_date is not None and self.delist_date <= self.list_date:
            raise DomainValidationError("退市日期必须晚于上市日期")

    def listed_on(self, d: date) -> bool:
        if d < self.list_date:
            return False
        return self.delist_date is None or d < self.delist_date


class SecurityMaster:
    """as-of 主数据仓：名称、板块、生命周期、风险状态。"""

    def __init__(self, version: str):
        self.version = version
        self._by_code: Dict[str, SecurityLifecycle] = {}

    def register(self, lc: SecurityLifecycle) -> None:
        key = lc.instrument.code
        if key in self._by_code:
            raise DomainValidationError(f"重复注册: {lc.instrument.instrument_id}")
        self._by_code[key] = lc

    def get(self, code: str) -> SecurityLifecycle:
        try:
            return self._by_code[code]
        except KeyError:
            raise UnknownSecurityError(
                f"主数据无此代码: {code!r}；禁止手填名称（F22），"
                f"先补主数据再出报告") from None

    def name_of(self, code: str, asof: date) -> str:
        lc = self.get(code)
        if not lc.listed_on(asof):
            raise UnknownSecurityError(
                f"{code} 在 {asof} 未上市/已退市（list={lc.list_date}, "
                f"delist={lc.delist_date}）；历史回测不得纳入")
        return lc.name

    def tradable_universe(self, asof: date) -> List[str]:
        """as-of 可交易股票池（退市样本在历史时点仍保留）。"""
        return sorted(c for c, lc in self._by_code.items() if lc.listed_on(asof))

    def size(self) -> int:
        return len(self._by_code)
