"""数据新鲜度与失败闭锁（S2-08）：昨日缓存不能标"今日完成"。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class DataStaleError(RuntimeError):
    """数据陈旧/不完整：阻断新订单，但已有持仓管理仍可用（任务书 S2-08）。"""


@dataclass(frozen=True)
class FreshnessPolicy:
    max_lag_minutes: int = 35       # 收盘后数据到位容差（15:00 + 35min）
    require_final_bar: bool = True  # 必须有当日最终bar


@dataclass
class FreshnessState:
    last_bar_available_at: Optional[datetime]
    expected_latest_bar_end: Optional[datetime]
    source_error: Optional[str] = None

    def status(self, policy: FreshnessPolicy,
               now: datetime) -> tuple:
        """返回 (ok, reason)。ok=False 时新订单闭锁。"""
        if self.source_error:
            return False, f"SOURCE_ERROR:{self.source_error}"
        if self.last_bar_available_at is None:
            return False, "NO_DATA"
        if self.expected_latest_bar_end is None:
            return False, "NO_EXPECTATION"
        if self.last_bar_available_at < self.expected_latest_bar_end:
            return False, (
                f"STALE: 最新可用 {self.last_bar_available_at} < "
                f"期望最终bar {self.expected_latest_bar_end}")
        lag = (now - self.last_bar_available_at).total_seconds() / 60
        if lag > policy.max_lag_minutes * 24:  # 粗界：隔日仍未更新
            return False, f"EXCESSIVE_LAG: {lag:.0f}min"
        return True, "FRESH"


def gating_for_orders(state: FreshnessState, policy: FreshnessPolicy,
                      now: datetime) -> None:
    """新订单闭锁门：不新鲜 → DataStaleError。

    注意：只阻断新开仓；已有持仓的退出管理不经过本门（S2-08 验收：
    阻断新订单同时按有效行情管理已有持仓）。
    """
    ok, reason = state.status(policy, now)
    if not ok:
        raise DataStaleError(
            f"数据不满足开仓条件（{reason}）；新订单闭锁。"
            f"已有持仓按最新可得行情继续执行退出规则。")
