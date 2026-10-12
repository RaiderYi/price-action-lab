"""统一信号注册表（S1-02，F15）——唯一事实源适配层。

问题（任务书 F15）：旧 SIGNAL_REGISTRY（14 类，无 breakout）与
SIGNAL_DEFINITION_REGISTRY（19 类）两套字典并存；enabled 集合与
focus_config.LIVE_SIGNALS 当前一致只是巧合，不是运行期唯一事实源。

本模块收敛为唯一读取接口：
1. family（形态家族，如 H2）与 implementation（legacy_proxy/strict）分立；
2. maturity（研究成熟度）与 enabled（是否进入生产）分立；
3. 未知信号类型默认拒绝（KeyError），不静默 fallback 到通用定义；
4. legacy_proxy 与 strict 是**不同 implementation**，ID 永不合并（F01/F02）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pal.domain.models import DomainValidationError, Implementation, Maturity

# ═══════════════════════════════════════════════════════════
# 唯一注册表：family × implementation 矩阵
# 数据来源：src/signal_registry.py 两个旧字典的合并审计 + focus_config
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SignalImplementationEntry:
    """一个 (family, implementation) 条目。"""
    family: str                        # H2 / L2 / breakout / wedge / final_flag / tr_fade / ...
    implementation: Implementation     # legacy_proxy / strict / research
    maturity: Maturity
    enabled: bool                      # 是否允许进入生产信号面
    detector: Optional[str]            # 检测器模块（None=未实现）
    evidence_fields: tuple             # 必需结构证据字段
    pricing_builder: Optional[str]     # 定价 builder 键（None=禁止无证据定价）
    detector_callable: Optional[str] = None  # legacy 旧键名兼容标注


# focus_config.LIVE_SIGNALS 的血统标注（F01 审计结论：回测走的是 legacy proxy）
_LIVE_FAMILIES = {
    "H2":         Implementation.LEGACY_PROXY,
    "L2":         Implementation.LEGACY_PROXY,
    "breakout":   Implementation.LEGACY_PROXY,
    "wedge":      Implementation.LEGACY_PROXY,
    "final_flag": Implementation.LEGACY_PROXY,
    "tr_fade":    Implementation.LEGACY_PROXY,
}

_RESEARCH_FAMILIES = {
    "H1": Implementation.LEGACY_PROXY,
    "L1": Implementation.LEGACY_PROXY,
    "climax_reversal": Implementation.LEGACY_PROXY,
    "eighty_twenty": Implementation.RESEARCH,
    "double_bottom": Implementation.RESEARCH,
    "double_top": Implementation.RESEARCH,
    "buy_the_close": Implementation.RESEARCH,
    "sell_the_close": Implementation.RESEARCH,
    "measured_move": Implementation.RESEARCH,   # 工具层，不出信号
}

_STRICT_RESEARCH = {
    "H1": Implementation.STRICT,
    "H2": Implementation.STRICT,
    "L1": Implementation.STRICT,
    "L2": Implementation.STRICT,
}

REGISTRY: Dict[tuple, SignalImplementationEntry] = {}


def _register(family, impl, maturity, enabled, detector, evidence, pricing):
    REGISTRY[(family, impl)] = SignalImplementationEntry(
        family=family, implementation=impl, maturity=maturity, enabled=enabled,
        detector=detector, evidence_fields=tuple(evidence), pricing_builder=pricing)


# ── legacy proxy（被 legacy 回测实际执行的路径，F01 审计）──
for fam in _LIVE_FAMILIES:
    _register(fam, Implementation.LEGACY_PROXY, Maturity.PRODUCTION, True,
              "signal_predictor", ["swing_points_or_breakout_evidence"],
              pricing=None if fam in ("breakout", "final_flag") else fam)
    # ↑ F05：breakout/final_flag 在旧 system_price_builder 无专用 builder，
    #   定价能力显式为 None（缺证据必须 insufficient，不许 _generic 兜底）

for fam in _RESEARCH_FAMILIES:
    _register(fam, _RESEARCH_FAMILIES[fam], Maturity.RESEARCH_ONLY, False,
              "signal_predictor", ["any"], pricing=None)

# ── strict（三层链路存在但从未进入回测路径，F01）──
for fam in _STRICT_RESEARCH:
    _register(fam, Implementation.STRICT, Maturity.RESEARCH_ONLY, False,
              "strict_pa_detector", ["bar_counting_chain"], pricing=None)


# ═══════════════════════════════════════════════════════════
# 唯一读取接口
# ═══════════════════════════════════════════════════════════

def get_entry(family: str, implementation: Implementation) -> SignalImplementationEntry:
    """读取唯一注册表条目。未知 (family, implementation) 一律 KeyError 拒绝。"""
    try:
        return REGISTRY[(family, implementation)]
    except KeyError:
        raise KeyError(
            f"未注册信号: family={family!r} implementation={implementation!r}. "
            f"已注册: {sorted({f for f, _ in REGISTRY})} "
            f"(family, impl) 组合数={len(REGISTRY)}；新增须显式注册，禁止静默 fallback") from None


def get_enabled_entries() -> List[SignalImplementationEntry]:
    """当前生产信号面（enabled=True），按 (family, impl) 排序保证确定性。"""
    return [e for k, e in sorted(REGISTRY.items()) if e.enabled]


def get_families(implementation: Optional[Implementation] = None) -> List[str]:
    items = list(REGISTRY)
    if implementation is not None:
        items = [k for k in items if k[1] == implementation]
    return sorted({f for f, _ in items})


def consistency_check() -> Dict[str, object]:
    """与 focus_config 的一致性审计（替代旧的"两套字典各自为政"）。

    返回结构化差异报告；不一致不抛异常（审计工具用），但调用方
    必须处理 non-empty diffs。
    """
    import focus_config  # legacy 单一事实源（本函数审计对象）

    live_cfg = set(focus_config.LIVE_SIGNALS)
    enabled_legacy = {e.family for e in get_enabled_entries()
                      if e.implementation == Implementation.LEGACY_PROXY}
    return {
        "focus_config_live": sorted(live_cfg),
        "registry_enabled_legacy_proxy": sorted(enabled_legacy),
        "diff_cfg_not_registry": sorted(live_cfg - enabled_legacy),
        "diff_registry_not_cfg": sorted(enabled_legacy - live_cfg),
        "consistent": live_cfg == enabled_legacy,
        "n_registered_combos": len(REGISTRY),
    }
