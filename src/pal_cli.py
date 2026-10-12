"""pal CLI entrypoint (S0-03 minimal).

Usage:
    pal --help
    pal doctor   # environment + module inventory self-check
"""
import importlib
import sys

LEGACY_MODULES = [
    "bar_counting_detector",
    "focus_config",
    "market_analyzer",
    "signal_predictor",
    "signal_registry",
    "strict_breakout_strength",
    "strict_pa_detector",
    "strict_pa_qualification",
    "strict_pa_actionability",
    "system_price_builder",
]

# Known optional external modules (private/other repo) — absence is reported,
# never silently ignored (F13).
KNOWN_OPTIONAL = ["kb_rules", "brooks_ontology_registry", "rule_guardrail"]


def _doctor() -> int:
    import platform

    print(f"python: {platform.python_version()}")
    print("--- core modules ---")
    failed = []
    for m in LEGACY_MODULES:
        try:
            importlib.import_module(m)
            print(f"  ok   {m}")
        except Exception as e:  # noqa: BLE001
            failed.append(m)
            print(f"  FAIL {m}: {type(e).__name__}: {e}")
    print("--- optional external modules (absence = capability disabled, not error) ---")
    for m in KNOWN_OPTIONAL:
        try:
            importlib.import_module(m)
            print(f"  present {m}")
        except ImportError:
            print(f"  absent  {m} (capability disabled)")
    print("--- result ---")
    if failed:
        print(f"INVALID: {len(failed)} core module(s) failed to import: {failed}")
        return 2
    print("OK: all core modules import; optional gaps reported above")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: doctor")
        return 0
    cmd = argv[0]
    if cmd == "doctor":
        return _doctor()
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
