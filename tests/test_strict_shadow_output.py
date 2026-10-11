"""Phase 4.1: shadow output tests — production isolation, schema, no DB writes"""
import pytest
import json
import os
import sys
from pathlib import Path

# Ensure src/ is importable
SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ═══ Production Isolation ═══

class TestProductionIsolation:
    """Verify shadow modules do NOT import production modules."""

    def test_bar_counting_no_forbidden_imports(self):
        """T19-T21: bar_counting_detector has no forbidden imports"""
        import bar_counting_detector
        src_code = (Path(bar_counting_detector.__file__).read_text() if hasattr(bar_counting_detector, '__file__')
                     else "")
        if not src_code:
            src_code = open(str(SRC / "bar_counting_detector.py"), 'r', encoding='utf-8').read()

        forbidden = [
            "import signal_predictor", "from signal_predictor",
            "import candidate_pool", "from candidate_pool",
            "import rule_guardrail", "from rule_guardrail",
            "import run_strategy", "from run_strategy",
            "import system_price_builder", "from system_price_builder",
            "import sqlite3",
        ]
        for f in forbidden:
            assert f not in src_code, f"Found forbidden import: {f}"

    def test_strict_pa_no_forbidden_imports(self):
        """T19-T21: strict_pa_detector has no forbidden imports"""
        src_code = open(str(SRC / "strict_pa_detector.py"), 'r', encoding='utf-8').read()
        forbidden = [
            "import signal_predictor", "from signal_predictor",
            "import candidate_pool", "from candidate_pool",
            "import rule_guardrail", "from rule_guardrail",
            "import run_strategy", "from run_strategy",
            "import system_price_builder", "from system_price_builder",
            "import sqlite3",
        ]
        for f in forbidden:
            assert f not in src_code, f"Found forbidden import: {f}"

    def test_run_strict_shadow_no_forbidden_imports(self):
        """T19-T21: run_strict_shadow has no forbidden imports"""
        shadow_path = Path(__file__).parent.parent / "scripts" / "run_strict_shadow.py"
        src_lines = open(str(shadow_path), 'r', encoding='utf-8').readlines()
        # Filter out docstrings and comment lines to only check real imports
        in_docstring = False
        real_lines = []
        for line in src_lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if in_docstring or stripped.startswith('#'):
                continue
            real_lines.append(stripped)
        src_code = "\n".join(real_lines)
        forbidden = [
            "import signal_predictor", "from signal_predictor",
            "import candidate_pool", "from candidate_pool",
            "import rule_guardrail", "from rule_guardrail",
            "import run_strategy", "from run_strategy",
            "import system_price_builder", "from system_price_builder",
        ]
        for f in forbidden:
            assert f not in src_code, f"Found forbidden import in run_strict_shadow: {f}"


# ═══ Shadow Output Schema ═══

class TestShadowOutputSchema:
    """T18: shadow JSON schema completeness."""

    def test_result_has_all_required_fields(self):
        """ShadowSignalResult has required top-level fields."""
        from strict_pa_detector import ShadowSignalResult
        sr = ShadowSignalResult(symbol="TEST", direction="long")
        sr.shadow_signal_type = "brooks_h2_strict"

        d = {
            "symbol": sr.symbol,
            "timeframe": sr.timeframe,
            "shadow_signal_type": sr.shadow_signal_type,
            "direction": sr.direction,
            "detected": sr.detected,
            "context_type": sr.context_type,
            "signal_bar_time": sr.signal_bar_time,
            "signal_bar_high": sr.signal_bar_high,
            "signal_bar_low": sr.signal_bar_low,
            "count_index": sr.count_index,
            "count_rule": sr.count_rule,
            "triggered": sr.triggered,
            "trigger_bar_time": sr.trigger_bar_time,
            "trigger_rule": sr.trigger_rule,
            "invalid_level": sr.invalid_level,
            "invalid_reason": sr.invalid_reason,
            "bars_since_signal": sr.bars_since_signal,
            "range_position": sr.range_position,
            "extended_count_warning": sr.extended_count_warning,
            "proxy_comparison": sr.proxy_comparison,
        }

        required = [
            "symbol", "timeframe", "shadow_signal_type", "direction", "detected",
            "signal_bar_time", "signal_bar_high", "signal_bar_low",
            "count_index", "count_rule", "triggered", "trigger_bar_time",
            "trigger_rule", "invalid_level", "invalid_reason",
            "bars_since_signal", "range_position", "extended_count_warning",
            "proxy_comparison",
        ]
        for field in required:
            assert field in d, f"Missing required field: {field}"

    def test_json_serializable(self):
        """ShadowSignalResult dict is JSON-serializable."""
        from strict_pa_detector import ShadowSignalResult
        sr = ShadowSignalResult(symbol="TEST", direction="long")
        sr.shadow_signal_type = "brooks_h2_strict"
        sr.detected = True
        sr.count_index = 2
        sr.signal_bar_high = 10.5
        sr.signal_bar_low = 10.0
        sr.proxy_comparison = {"current_proxy_signal_type": "H2", "proxy_detected": False,
                                "proxy_display_label": "H2代理", "strict_matches_proxy": False,
                                "difference_reason": ""}

        d = {
            "symbol": sr.symbol,
            "timeframe": sr.timeframe,
            "shadow_signal_type": sr.shadow_signal_type,
            "direction": sr.direction,
            "detected": sr.detected,
            "context_type": sr.context_type,
            "context_confidence": sr.context_confidence,
            "context_details": sr.context_details,
            "signal_bar_time": sr.signal_bar_time,
            "signal_bar_high": sr.signal_bar_high,
            "signal_bar_low": sr.signal_bar_low,
            "signal_bar_close": sr.signal_bar_close,
            "count_index": sr.count_index,
            "count_rule": sr.count_rule,
            "bar_count_sequence": sr.bar_count_sequence,
            "triggered": sr.triggered,
            "trigger_bar_time": sr.trigger_bar_time,
            "trigger_rule": sr.trigger_rule,
            "trigger_delay_bars": sr.trigger_delay_bars,
            "shadow_entry": sr.shadow_entry,
            "shadow_stop": sr.shadow_stop,
            "invalid_level": sr.invalid_level,
            "invalid_reason": sr.invalid_reason,
            "signal_quality": sr.signal_quality,
            "bars_since_signal": sr.bars_since_signal,
            "range_position": sr.range_position,
            "extended_count_warning": sr.extended_count_warning,
            "proxy_comparison": sr.proxy_comparison,
        }

        # Should not raise
        json_str = json.dumps(d, ensure_ascii=False, default=str)
        back = json.loads(json_str)
        assert back["symbol"] == "TEST"
        assert back["detected"] is True
        assert back["count_index"] == 2


# ═══ No Fixed Trigger Expiry ═══

class TestNoFixedTriggerExpiry:
    """T25: no hard 5-bar trigger expiry window."""

    def test_trigger_allowed_beyond_5_bars(self):
        """Trigger detection searches up to 20 bars, not limited to 5."""
        from strict_pa_detector import _detect_trigger
        from bar_counting_detector import build_bar_info_list
        from strict_pa_detector import ShadowSignalResult

        n = 30
        highs = [10.0] * 10 + [10.1] + [10.0] * 5 + [10.5] + [10.0] * 13
        lows  = [9.5] * n
        bars = build_bar_info_list(highs, lows, highs, highs)

        sr = ShadowSignalResult(symbol="TEST", direction="long")
        _detect_trigger(sr, bars, signal_bar_index=10, direction="long")
        # trigger at bar 16 (6 bars after signal, > 5)
        assert sr.triggered
        assert sr.trigger_delay_bars == 6


# ═══ No DB Writes ═══

class TestNoDBWrites:
    """T19: shadow output does NOT write signals.db."""

    def test_no_sqlite3_in_bar_counting(self):
        import bar_counting_detector
        if hasattr(bar_counting_detector, '__file__'):
            lines = Path(bar_counting_detector.__file__).read_text().splitlines()
        else:
            lines = open(str(SRC / "bar_counting_detector.py"), 'r', encoding='utf-8').readlines()
        # Filter docstrings
        in_doc = False
        real = []
        for line in lines:
            s = line.strip()
            if s.startswith('"""') or s.startswith("'''"):
                in_doc = not in_doc
                continue
            if in_doc or s.startswith('#'):
                continue
            real.append(s)
        code = "\n".join(real)
        assert "sqlite3" not in code

    def test_no_sqlite3_in_strict_pa(self):
        src = open(str(SRC / "strict_pa_detector.py"), 'r', encoding='utf-8').readlines()
        in_doc = False
        real = []
        for line in src:
            s = line.strip()
            if s.startswith('"""') or s.startswith("'''"):
                in_doc = not in_doc
                continue
            if in_doc or s.startswith('#'):
                continue
            real.append(s)
        code = "\n".join(real)
        assert "sqlite3" not in code

    def test_no_db_in_run_script(self):
        src = open(str(Path(__file__).parent.parent / "scripts" / "run_strict_shadow.py"),
                   'r', encoding='utf-8').readlines()
        in_doc = False
        real = []
        for line in src:
            s = line.strip()
            if s.startswith('"""') or s.startswith("'''"):
                in_doc = not in_doc
                continue
            if in_doc or s.startswith('#'):
                continue
            real.append(s)
        code = "\n".join(real)
        assert "sqlite3" not in code


# ═══ Module Existence ═══

class TestModuleExistence:
    def test_bar_counting_importable(self):
        from bar_counting_detector import build_bar_info_list, count_bars_strict
        assert callable(build_bar_info_list)
        assert callable(count_bars_strict)

    def test_strict_pa_importable(self):
        from strict_pa_detector import (
            detect_bull_pullback_context,
            detect_bear_rally_context,
            detect_strict_bar_counting_signals,
        )
        assert callable(detect_bull_pullback_context)
        assert callable(detect_bear_rally_context)
        assert callable(detect_strict_bar_counting_signals)

    def test_run_script_readable(self):
        script = Path(__file__).parent.parent / "scripts" / "run_strict_shadow.py"
        assert script.exists()
        src = script.read_text()
        assert "def run_shadow" in src or "def main" in src
