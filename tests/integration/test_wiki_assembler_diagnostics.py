#!/usr/bin/env python3
"""
测试 wiki_assembler 诊断输出。

运行: python -m pytest tests/test_wiki_assembler_diagnostics.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest


class TestAssembleV2:
    """测试 assemble_wiki_context_v2 兼容性和新接口。"""

    def test_v2_returns_str_backward_compat(self):
        """v2 函数不传 directions 时返回纯字符串。"""
        from wiki_assembler import assemble_wiki_context_v2
        # 空输入也应正常返回字符串
        result = assemble_wiki_context_v2({}, {}, None, None)
        assert isinstance(result, str)

    def test_v2_with_diagnostics_returns_tuple(self):
        """新函数返回 (str, dict|None)。"""
        from wiki_assembler import assemble_wiki_context_v2_with_diagnostics
        text, diag = assemble_wiki_context_v2_with_diagnostics({}, {}, None, None)
        assert isinstance(text, str)

    def test_v2_with_directions_no_crash(self):
        """传 directions 不崩溃。"""
        from wiki_assembler import assemble_wiki_context_v2
        result = assemble_wiki_context_v2({}, {}, None, None, directions={})
        assert isinstance(result, str)

    def test_v2_with_signals_directions(self):
        """传 signals + directions 工作。"""
        from wiki_assembler import assemble_wiki_context_v2
        result = assemble_wiki_context_v2(
            {}, {}, None,
            predicted_signals={"600036": ["L2"]},
            directions={"600036": "short"}
        )
        assert isinstance(result, str)


class TestDiagnosticsNoContamination:
    """确保诊断不污染 prompt。"""

    def test_v2_output_no_debug_injection(self):
        """v2 输出不包含诊断内部字样。"""
        from wiki_assembler import assemble_wiki_context_v2
        result = assemble_wiki_context_v2({}, {}, None, None)
        # 不应包含诊断内部字段
        assert "diag" not in result.lower()
        assert "diagnostics" not in result.lower()

    def test_v2_with_diagnostics_separate(self):
        """diagnostics 作为独立输出，不混入 text。"""
        from wiki_assembler import assemble_wiki_context_v2_with_diagnostics
        text, diag = assemble_wiki_context_v2_with_diagnostics({}, {}, None, None)
        # text 中不应有诊断数据
        assert "used_budget" not in text
        assert "risk_profile" not in text


class TestGracefulFallback:
    """测试回退行为。"""

    def test_empty_input_no_crash(self):
        """空输入不崩溃。"""
        from wiki_assembler import assemble_wiki_context_v2_with_diagnostics
        text, diag = assemble_wiki_context_v2_with_diagnostics({}, {}, None, None)
        assert isinstance(text, str)

    def test_v1_still_works(self):
        """v1 接口不受影响。"""
        from wiki_assembler import assemble_wiki_context
        result = assemble_wiki_context({}, {}, None, None)
        assert isinstance(result, str)
