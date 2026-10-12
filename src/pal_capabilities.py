"""Capability flags for optional external modules (S0-06, F13).

Rule: optional-module absence is a *capability*, reported explicitly, never a
silent fallback. Central registry so run reports can state which capabilities
were degraded. Only ImportError is treated as absence; any other exception is
a real error and must propagate.
"""
import importlib

# module name -> description of the capability lost when absent
OPTIONAL_MODULES = {
    "kb_rules": "knowledge-base rule engines (breakout_quality/climax/trend_maturity)",
    "brooks_ontology_registry": "ontology-backed signal filtering",
    "rule_guardrail": "hard rule guardrail enforcement",
}

_capacache: dict = {}


def capability_available(module: str) -> bool:
    """True if optional module importable. Cached per process; cache can be reset in tests."""
    if module not in _capacache:
        try:
            importlib.import_module(module)
            _capacache[module] = True
        except ImportError:
            _capacache[module] = False
    return _capacache[module]


def reset_cache() -> None:
    _capacache.clear()


def degrade_record() -> dict:
    """Snapshot of capability availability for run manifests."""
    return {m: capability_available(m) for m in OPTIONAL_MODULES}
