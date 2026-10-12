"""领域层：枚举、标识符、校验错误（任务书 §4 / S1-01）。

核心原则：
- 方向三层分立（任务书 §4 关键附加协议）：价格方向(up/down)、
  交易动作(buy/sell)、持仓方向(long/short) 不再互相冒充。
- 非法值在构造时即拒绝，不再以自由字符串在模块间传递。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DomainValidationError(ValueError):
    """领域对象校验失败。"""


# ═══════════════════════════════════════════════════════════
# 方向枚举（三层分立，任务书 §4 附加协议第1条）
# ═══════════════════════════════════════════════════════════

class PriceDirection(str, Enum):
    """价格/结构方向：描述市场结构朝向，不是交易动作。"""
    UP = "up"
    DOWN = "down"


class TradeAction(str, Enum):
    """交易动作：订单层面买/卖。"""
    BUY = "buy"
    SELL = "sell"


class PositionDirection(str, Enum):
    """持仓方向：第一版只做多（任务书 §1.1）。"""
    LONG = "long"
    # SHORT = "short"  # A股第一版禁止开空仓（任务书 §4），预留枚举位但不启用


class SignalState(str, Enum):
    """信号状态机（任务书 §4 SignalEvent.state）。

    raw / qualified / armed / triggered / rejected / expired 不混用。
    """
    RAW = "raw"                    # 检测到结构候选，未审核
    QUALIFIED = "qualified"        # 资格审核通过
    ARMED = "armed"                # 等待触发条件（setup 已成立未触发）
    TRIGGERED = "triggered"        # 触发条件已出现（≠成交）
    REJECTED = "rejected"          # 资格/冲突审核拒绝
    EXPIRED = "expired"            # 超时失效（不抹除既有成交，§4）


class Implementation(str, Enum):
    """同一 family 的具体实现血统（F01/F02：legacy proxy 与 strict 分立）。"""
    LEGACY_PROXY = "legacy_proxy"      # signal_predictor 旧代理路径
    STRICT = "strict"                  # strict_pa_detector 三层链路
    RESEARCH = "research"              # 研究中实现，禁止进入交易路径


class Maturity(str, Enum):
    """成熟度：研究→生产晋级状态（与 enabled 分开，S1-02）。"""
    RESEARCH_ONLY = "research_only"
    CANDIDATE = "candidate"
    PRODUCTION = "production"


class RunStatus(str, Enum):
    """运行状态（S0-06/F13）：失败不是 no_signal。"""
    VALID = "valid"
    INVALID = "invalid"          # 关键错误，本轮结果不可用于结论
    DEGRADED = "degraded"        # 能力降级但核心路径完整


# ═══════════════════════════════════════════════════════════
# 标识符（S1-07 统一 ID 体系的前置类型；完整 ID 生成见 identity.py）
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class InstrumentId:
    """证券标识：code 必须字符串（保前导零），exchange/board 分立。"""
    code: str
    exchange: str  # "SSE" | "SZSE"
    board: str     # "main" | "chinext" | "star" | ...

    def __post_init__(self):
        if not isinstance(self.code, str) or not self.code.strip():
            raise DomainValidationError("code 必须为非空字符串（保前导零，禁止 int）")
        if not self.code.isdigit():
            raise DomainValidationError(f"code 应为数字字符串: {self.code!r}")
        if not self.exchange or not self.board:
            raise DomainValidationError("exchange/board 不能为空")

    @property
    def instrument_id(self) -> str:
        return f"{self.exchange}.{self.code}"


# ═══════════════════════════════════════════════════════════
# 领域基类与通用校验
# ═══════════════════════════════════════════════════════════

def require_positive_price(value, name: str) -> float:
    v = float(value)
    if not (v > 0) or v != v or v in (float("inf"), float("-inf")):
        raise DomainValidationError(f"{name} 必须为正有限数, got {value!r}")
    return v


def require_non_negative(value, name: str) -> float:
    v = float(value)
    if v < 0 or v != v or v in (float("inf"), float("-inf")):
        raise DomainValidationError(f"{name} 不能为负, got {value!r}")
    return v


def require_non_empty_str(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{name} 必须为非空字符串")
    return value


@dataclass(frozen=True)
class TimeWindow:
    """时间窗（含 available_at 语义的最小载体；完整 Bar 见 data 层）。"""
    start: str   # ISO8601
    end: str     # ISO8601

    def __post_init__(self):
        from datetime import datetime
        s = datetime.fromisoformat(self.start)
        e = datetime.fromisoformat(self.end)
        if e <= s:
            raise DomainValidationError(f"时间窗倒置: start={self.start} end={self.end}")
