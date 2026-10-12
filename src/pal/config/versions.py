"""配置版本化（S1-04）：阈值/规则/研究配置必须有版本和 hash。

问题：focus_config.py 的魔法常量散落（CHANNEL_FILTER/TR_FADE_GATE），
修改无版本追踪，无法满足"同一版本可复跑、运行中改配置不得改变已发信号"。

方案：
1. 冻结快照：frozen_config() 返回配置内容寻址 hash + 完整键值；
2. 运行期校验：引擎启动时记录 config_version，之后任何 drift 检测失败
   即抛错（不做静默部分重载）；
3. git tag 可选：config_version 足以在仓库历史中定位修改。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

from pal.domain.models import DomainValidationError

# 受版本管控的配置域（新增域必须登记在此）
GOVERNED_DOMAINS = frozenset({
    "channel_filter",      # 精选突破阈值（F03 修复后：extreme>=0.7）
    "tr_fade_gate",        # 区间门控
    "signal_face",         # LIVE/TOOL/RESEARCH 信号面
})


@dataclass(frozen=True)
class ConfigSnapshot:
    """一份冻结的配置快照。"""
    config_version: str            # 内容寻址 hash 前12位
    domains: Dict[str, Any]        # 各域完整键值（可 JSON 序列化）

    def __post_init__(self):
        if not self.config_version:
            raise DomainValidationError("config_version 不能为空")
        missing = GOVERNED_DOMAINS - set(self.domains)
        if missing:
            raise DomainValidationError(f"配置快照缺域: {sorted(missing)}")


def _hash_domains(domains: Dict[str, Any]) -> str:
    canonical = json.dumps(domains, ensure_ascii=False, sort_keys=True,
                           default=_jsonable)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def _jsonable(obj):
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    raise TypeError(f"不可序列化的配置类型: {type(obj)}")


def frozen_config_from_focus() -> ConfigSnapshot:
    """从 legacy focus_config 构建冻结快照（S1 阶段的适配入口）。"""
    import focus_config as fc

    domains = {
        "channel_filter": {
            "enabled": fc.CHANNEL_FILTER["enabled"],
            "breakout_min_range_atr": fc.CHANNEL_FILTER["breakout_min_range_atr"],
            "breakout_close_extreme_pct": fc.CHANNEL_FILTER["breakout_close_extreme_pct"],
            "breakout_lookback_bars": fc.CHANNEL_FILTER["breakout_lookback_bars"],
            "strong_trend_confidence": fc.CHANNEL_FILTER["strong_trend_confidence"],
            "strong_trend_allowed_counter": sorted(fc.CHANNEL_FILTER["strong_trend_allowed_counter"]),
        },
        "tr_fade_gate": dict(fc.TR_FADE_GATE),
        "signal_face": {
            "live": sorted(fc.LIVE_SIGNALS),
            "tool": sorted(fc.TOOL_SIGNALS),
            "research_only": sorted(fc.RESEARCH_ONLY),
        },
    }
    return ConfigSnapshot(config_version=_hash_domains(domains), domains=domains)


class ConfigDriftError(RuntimeError):
    """运行期配置漂移：已开始的 run 不允许热改配置。"""


class ActiveConfigGuard:
    """运行期守卫：run 开始时绑定快照，期间 focus_config 若被改动即抛错。"""

    def __init__(self, snapshot: ConfigSnapshot):
        self._snapshot = snapshot
        self._active = False

    def __enter__(self) -> ConfigSnapshot:
        self._active = True
        return self._snapshot

    def verify(self) -> None:
        """显式校验：当前 focus_config 仍与快照一致。"""
        if not self._active:
            raise ConfigDriftError("guard 未激活（未进入 with 块）")
        current = frozen_config_from_focus()
        if current.config_version != self._snapshot.config_version:
            raise ConfigDriftError(
                f"配置漂移: run 绑定 {self._snapshot.config_version}, "
                f"当前 {current.config_version}；运行中改配置不得改变已发信号（任务书 S1-04）")

    def __exit__(self, *exc) -> None:
        self._active = False
