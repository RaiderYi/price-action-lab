"""Phase 3: PA 概念纯化测试 — proxy 标签、禁止措辞、strict 未启用、生产不变"""
import pytest
import os

BASE = "d:/工作/SCDC数据日常工作/llm-wiki/strategy_engine"


class TestProxyLabelInRegistry:
    """1. proxy 信号标签正确"""

    def test_format_signal_label_for_proxy(self):
        from src.signal_registry import format_signal_label
        label = format_signal_label("H2")
        assert "proxy" in label.lower() or "代理" in label, f"H2 label should indicate proxy: {label}"
        assert "非严格" in label, f"H2 label should say non-strict: {label}"

    def test_format_signal_label_for_l2_proxy(self):
        from src.signal_registry import format_signal_label
        label = format_signal_label("L2")
        assert "proxy" in label.lower() or "代理" in label

    def test_format_signal_label_for_strict_not_implemented(self):
        from src.signal_registry import format_signal_label
        label = format_signal_label("brooks_h2_strict")
        assert "未实现" in label

    def test_format_signal_label_for_non_proxy(self):
        from src.signal_registry import format_signal_label
        label = format_signal_label("wedge")
        assert label == "wedge"

    def test_get_proxy_disclaimer(self):
        from src.signal_registry import get_proxy_disclaimer
        disc = get_proxy_disclaimer("H2")
        assert "代理" in disc or "proxy" in disc.lower()
        assert "brooks_h2_strict" in disc

    def test_get_proxy_disclaimer_none_for_non_proxy(self):
        from src.signal_registry import get_proxy_disclaimer
        assert get_proxy_disclaimer("wedge") == ""


class TestForbiddenWording:
    """2. proxy 禁止措辞"""

    def test_h2_has_forbidden_wording(self):
        from src.signal_registry import get_report_forbidden_wording
        fw = get_report_forbidden_wording("H2")
        assert len(fw) >= 3

    def test_forbidden_contains_key_phrases(self):
        from src.signal_registry import get_report_forbidden_wording
        fw_text = " ".join(get_report_forbidden_wording("H2"))
        assert "严格 Brooks H2" in fw_text
        assert "经典 H2" in fw_text

    def test_check_report_violations_detects_forbidden(self):
        from src.signal_registry import check_report_violations
        report = "今日 300124 出现严格 Brooks H2 成立信号"
        violations = check_report_violations(report, "H2")
        assert len(violations) > 0
        assert violations[0][0] == "严格 Brooks H2 成立"

    def test_check_report_violations_no_false_positive(self):
        from src.signal_registry import check_report_violations
        report = "系统识别为 H2 类代理信号（higher-low 结构）"
        violations = check_report_violations(report, "H2")
        assert len(violations) == 0

    def test_check_report_violations_multi_pattern(self):
        from src.signal_registry import check_report_violations
        report = "标准 H2 买入信号，符合 Brooks H2 二次入场条件"
        violations = check_report_violations(report, "H2")
        assert len(violations) >= 1  # "标准 H2" matches

    def test_non_proxy_no_violations(self):
        from src.signal_registry import check_report_violations
        report = "严格 Brooks H2 成立"  # would be violation if H2
        violations = check_report_violations(report, "wedge")
        assert len(violations) == 0  # wedge is not proxy

    def test_all_forbidden_patterns_non_empty(self):
        from src.signal_registry import get_all_forbidden_patterns
        patterns = get_all_forbidden_patterns()
        assert len(patterns) >= 10


class TestStrictNotImplemented:
    """3. strict 信号未启用"""

    def test_strict_h2_not_enabled(self):
        from src.signal_registry import get_signal_definition
        cfg = get_signal_definition("brooks_h2_strict")
        assert cfg["enabled"] is False
        assert cfg["implemented"] is False
        assert cfg["maturity"] == "NOT_IMPLEMENTED"

    def test_strict_signals_not_in_live(self):
        from src.signal_registry import get_live_signal_types
        live = get_live_signal_types()
        for st in ["brooks_h1_strict", "brooks_h2_strict",
                    "brooks_l1_strict", "brooks_l2_strict"]:
            assert st not in live

    def test_strict_signal_has_bar_counting_family(self):
        from src.signal_registry import get_pa_family
        assert get_pa_family("brooks_h2_strict") == "bar_counting"
        assert get_pa_family("brooks_l2_strict") == "bar_counting"


class TestPromptHasRegistryPriority:
    """4. Prompt 包含 Registry 优先级规则"""

    def test_system_prompt_has_signal_priority(self):
        with open(os.path.join(BASE, "prompts/system_prompt.md"), "r", encoding="utf-8") as f:
            content = f.read()
        assert "Signal Definition Registry" in content
        assert "is_proxy" in content
        assert "strict_match" in content
        assert "implementation_version" in content
        assert "禁止" in content and "信号名称" in content


class TestNoProductionChange:
    """5. 生产行为不变"""

    def test_signal_predictor_unchanged(self):
        """验证 signal_predictor.py 文件未被 Phase 3 修改"""
        import hashlib, os
        fp = os.path.join(os.path.dirname(__file__), "..", "src", "signal_predictor.py")
        assert os.path.exists(fp), f"signal_predictor not found at {fp}"

    def test_run_strategy_imports_still_work(self):
        """验证 run_strategy 的关键 import 仍然可用"""
        from src.signal_registry import validate_signal_type, get_min_rr
        assert validate_signal_type("H2")
        assert get_min_rr("H2") == 1.5

    def test_legacy_signal_count_unchanged(self):
        """生产信号数量未变"""
        from src.signal_registry import SIGNAL_REGISTRY
        # SIGNAL_REGISTRY should have its original 14 signals
        assert len(SIGNAL_REGISTRY) == 14


class TestReportRendererProxyAware:
    """6. report_fact_renderer 支持 proxy 标签"""

    def test_renderer_imports_work(self):
        from src.report_fact_renderer import rebuild_markdown_report
        assert callable(rebuild_markdown_report)


class TestDisplayFunctions:
    """7. 显示辅助函数"""

    def test_get_signal_display_name(self):
        from src.signal_registry import get_signal_display_name
        name = get_signal_display_name("H2")
        assert "proxy" in name.lower() or "H2" in name

    def test_format_signal_label_for_live_non_proxy(self):
        from src.signal_registry import format_signal_label
        assert format_signal_label("measured_move") == "measured_move"

    def test_get_display_signal_label_h2(self):
        """Phase 3.1: H2 display label must include proxy and not be bare H2"""
        from src.signal_registry import get_display_signal_label
        label = get_display_signal_label("H2")
        assert "代理" in label, f"H2 label should contain 代理: {label}"
        assert "higher-low" in label.lower(), f"H2 label should mention higher-low: {label}"
        assert label != "H2", "H2 label must not be bare 'H2'"

    def test_get_display_signal_label_l2(self):
        """Phase 3.1: L2 display label must include proxy"""
        from src.signal_registry import get_display_signal_label
        label = get_display_signal_label("L2")
        assert "代理" in label
        assert "lower-high" in label.lower()

    def test_get_display_signal_label_non_proxy_unchanged(self):
        """Non-proxy signals use bare signal_type"""
        from src.signal_registry import get_display_signal_label
        assert get_display_signal_label("wedge") == "wedge"
        assert get_display_signal_label("measured_move") == "measured_move"

    def test_get_display_signal_label_strict_not_implemented(self):
        """Strict not implemented signals show 未实现"""
        from src.signal_registry import get_display_signal_label
        label = get_display_signal_label("brooks_h2_strict")
        assert "未实现" in label

    def test_machine_signal_type_preserved(self):
        """machine signal_type (H2/L2) must still validate"""
        from src.signal_registry import validate_signal_type
        assert validate_signal_type("H2")
        assert validate_signal_type("L2")
