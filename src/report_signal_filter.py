"""
report_signal_filter.py — P0 Brooks Strict Entry Signal Production Cutover

Classifies signals as:
  brooks_production:     Brooks entry signals eligible for main report
  legacy_proxy:          H1/H2/L1/L2 proxies — appendix only
  strict_research_only:  Brooks strict signals not yet production-ready
  not_entry_signal:      Pattern/Context/Target — should not appear as signals

[S0-06/F12] brooks_ontology_registry 不在本仓库（外部模块）。导入改为
capability 门控：模块存在时正常使用；缺失时本模块的筛选能力显式禁用，
调用方得到明确错误而不是 ModuleNotFoundError 或静默错误结果。
"""

import pal_capabilities

_capability_ok = pal_capabilities.capability_available("brooks_ontology_registry")

if _capability_ok:
    from brooks_ontology_registry import (
        is_brooks_entry_signal, is_legacy_proxy_signal, get_brooks_category,
        BROOKS_ENTRY_SIGNAL_REGISTRY, BROOKS_LEGACY_PROXY_REGISTRY,
    )

IMPLEMENTED_STRICT = {
    "brooks_h1_strict", "brooks_h2_strict",
    "brooks_l1_strict", "brooks_l2_strict",
    "climax_reversal",
}


class ReportFilterUnavailable(RuntimeError):
    """Raised when the report filter is used without brooks_ontology_registry."""


def _require_registry():
    if not _capability_ok:
        raise ReportFilterUnavailable(
            "brooks_ontology_registry 未安装（外部模块，不在本仓库）。"
            "报告筛选能力禁用；安装该模块后重试，或使用不依赖 ontology 的报告路径。"
        )


def classify_signal(signal_type: str) -> str:
    """Classify a signal for report routing."""
    _require_registry()
    cat = get_brooks_category(signal_type)

    if cat == "EntrySignal":
        if signal_type in IMPLEMENTED_STRICT:
            return "brooks_production"
        return "strict_research_only"

    if cat == "LegacyProxy":
        return "legacy_proxy"

    if cat in ("PatternExpression", "ContextFactor", "TargetTool", "RiskWarning"):
        return "not_entry_signal"

    return "unknown"


def filter_signals_for_main_report(guardrail_signals: list) -> dict:
    """
    Split guardrail_signals into main report groups.

    Returns dict with:
      brooks_signals:     Brooks entry signals for main report
      legacy_proxies:     Legacy proxy signals for appendix
      strict_research:    Strict signals not yet production-ready
      not_signals:        Pattern/Context signals (should not appear)
    """
    groups = {
        "brooks_signals": [],
        "legacy_proxies": [],
        "strict_research": [],
        "not_signals": [],
    }
    for gs in guardrail_signals:
        cls = classify_signal(gs.signal_type)
        if cls == "brooks_production":
            groups["brooks_signals"].append(gs)
        elif cls == "legacy_proxy":
            groups["legacy_proxies"].append(gs)
        elif cls == "strict_research_only":
            groups["strict_research"].append(gs)
        else:
            groups["not_signals"].append(gs)
    return groups
