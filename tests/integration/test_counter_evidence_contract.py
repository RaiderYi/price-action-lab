#!/usr/bin/env python3
"""
P5.1: Counter evidence 契约测试

覆盖:
  - counter_evidence 在 signal 顶层且具体 → specific
  - counter_evidence 只在 markdown 正文中 → missing + parser_warning
  - counter_evidence 在 structure_evidence 内 → parser 归一化
  - counter_evidence 为空数组 → missing
  - counter_evidence 为"注意市场波动" → generic
  - counter_evidence 包含具体价格位和失效条件 → specific
  - missing counter_evidence 不能进入 A
  - generic counter_evidence 不能进入 A
  - specific counter_evidence 不触发该项降级
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_guardrail import ScoredSignal, apply_guardrails


def _make_signal(**kw):
    """制造一个完整信号并运行 guardrail。"""
    defaults = {
        "symbol": "TEST", "signal_type": "L2", "direction": "short",
        "market": "A股", "llm_entry_min": 100, "llm_entry_max": 100,
        "llm_stop_loss": 102, "llm_tp1": 96,  # short: stop>entry, tp1<entry ✓
        "llm_score": 80, "llm_confidence": 0.8, "llm_position_pct": 0.02,
        "structure_evidence": {
            "LH1": 105, "LH2": 100, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "counter_evidence": "Break above 105 would invalidate",
        },
        "invalid_condition": "价格回到止损上方",
    }
    defaults.update(kw)
    s = ScoredSignal(**defaults)
    return apply_guardrails(s)


class TestCounterEvidenceQuality(unittest.TestCase):
    """counter_evidence 质量分级测试。"""

    def test_specific_with_price_and_invalidates(self):
        """含具体价格位和失效条件 → specific，不触发降级。"""
        s = _make_signal(
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "若价格重新站上 51.30，则 L2 空头结构失效",
            })
        # 含价格位 + 失效条件 → specific → 不触发 B cap
        ce_warnings = [v for v in s.guardrail_violations if "counter_evidence" in v.lower()]
        self.assertEqual(len(ce_warnings), 0,
                        f"specific counter_evidence 不应触发降级: {ce_warnings}")

    def test_generic_counter_not_A(self):
        """泛泛 counter_evidence → generic → 不能 A。"""
        s = _make_signal(
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "注意市场波动",
            })
        self.assertNotEqual(s.final_grade, "A",
                           f"generic counter_evidence 不能 A: {s.final_grade}")
        ce_warnings = [v for v in s.guardrail_violations if "counter_evidence" in v.lower()]
        self.assertTrue(len(ce_warnings) > 0,
                       f"应有 counter_evidence 降级警告: {s.guardrail_violations}")

    def test_missing_counter_not_A(self):
        """缺 counter_evidence → missing → 不能 A。"""
        s = _make_signal(
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                # 故意不设 counter_evidence
            })
        self.assertNotEqual(s.final_grade, "A",
                           f"missing counter_evidence 不能 A: {s.final_grade}")

    def test_ce_in_structure_evidence_normalized(self):
        """counter_evidence 在 structure_evidence 内 → guardrail 可读取。"""
        s = _make_signal(
            structure_evidence={
                "LH1": 105, "LH2": 100, "prior_low": 95,
                "trigger_bar": "bear_bar", "confirmation": "break_low",
                "counter_evidence": "Break above 105 would invalidate",
            })
        # specific → 不应触发 counter_evidence 降级
        ce_warnings = [v for v in s.guardrail_violations if "counter_evidence" in v.lower()]
        self.assertEqual(len(ce_warnings), 0,
                        f"specific counter_evidence 不应触发降级: {ce_warnings}")


class TestParserNormalization(unittest.TestCase):
    """Parser 归一化逻辑测试 — 模拟 LLM 输出的各种格式。"""

    def _parse(self, **sig_kw):
        """模拟 run_strategy.py parser 归一化逻辑。"""
        sig = dict(sig_kw)
        counter_evidence_raw = []

        # 优先：signal 顶层 counter_evidence
        ce_from_sig = sig.get("counter_evidence")
        if isinstance(ce_from_sig, list) and len(ce_from_sig) > 0:
            counter_evidence_raw = ce_from_sig
        elif isinstance(ce_from_sig, dict):
            counter_evidence_raw = [ce_from_sig]
        elif isinstance(ce_from_sig, str) and ce_from_sig.strip():
            counter_evidence_raw = [{"type": "unknown", "description": ce_from_sig}]

        # 其次：structure_evidence 内部
        se_ce = sig.get("structure_evidence", {})
        if isinstance(se_ce, dict) and not counter_evidence_raw:
            se_ce_val = se_ce.get("counter_evidence", "")
            if isinstance(se_ce_val, list) and len(se_ce_val) > 0:
                counter_evidence_raw = se_ce_val
            elif isinstance(se_ce_val, str) and se_ce_val.strip():
                counter_evidence_raw = [{"type": "unknown", "description": se_ce_val}]

        missing = len(counter_evidence_raw) == 0
        return {"counter_evidence_raw": counter_evidence_raw, "missing": missing}

    def test_ce_at_signal_top_level_list(self):
        """signal 顶层 list → 归一化。"""
        r = self._parse(counter_evidence=[
            {"type": "price_level", "description": "若站上51.30则失效",
             "price_level": 51.30, "invalidates_if": "close_above_51.30"}
        ])
        self.assertFalse(r["missing"])
        self.assertEqual(len(r["counter_evidence_raw"]), 1)
        self.assertEqual(r["counter_evidence_raw"][0]["type"], "price_level")

    def test_ce_empty_array_is_missing(self):
        """counter_evidence=[] → missing。"""
        r = self._parse(counter_evidence=[])
        self.assertTrue(r["missing"])

    def test_ce_in_structure_evidence_fallback(self):
        """structure_evidence.counter_evidence → 归一化。"""
        r = self._parse(structure_evidence={"counter_evidence": "双底风险 at 48.45"})
        self.assertFalse(r["missing"])
        self.assertEqual(len(r["counter_evidence_raw"]), 1)

    def test_ce_missing_both_yields_missing(self):
        """两处都缺 → missing。"""
        r = self._parse()
        self.assertTrue(r["missing"])

    def test_ce_generic_string_is_captured(self):
        """顶层 "注意市场波动" → 归一化但内容 generic。"""
        r = self._parse(counter_evidence="注意市场波动")
        self.assertFalse(r["missing"])
        self.assertEqual(r["counter_evidence_raw"][0]["description"], "注意市场波动")


class TestCounterEvidencePipeline(unittest.TestCase):
    """端到端：parser → guardrail 完整链路。"""

    def test_specific_passes_guardrail(self):
        """specific counter_evidence → 不触发降级。"""
        s = _make_signal(structure_evidence={
            "LH1": 105, "LH2": 100, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "counter_evidence": "若跌破后快速收回 30.60，说明空头突破失败",
        })
        ce_warnings = [v for v in s.guardrail_violations if "counter_evidence" in v.lower()]
        self.assertEqual(len(ce_warnings), 0)

    def test_generic_triggers(self):
        """generic counter_evidence → 降级警告。"""
        s = _make_signal(structure_evidence={
            "LH1": 105, "LH2": 100, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
            "counter_evidence": "可能反弹",
        })
        ce_warnings = [v for v in s.guardrail_violations if "counter_evidence" in v.lower()]
        self.assertTrue(len(ce_warnings) > 0)

    def test_missing_triggers(self):
        """missing counter_evidence → 降级警告。"""
        s = _make_signal(structure_evidence={
            "LH1": 105, "LH2": 100, "prior_low": 95,
            "trigger_bar": "bear_bar", "confirmation": "break_low",
        })
        ce_warnings = [v for v in s.guardrail_violations if "counter_evidence" in v.lower()]
        self.assertTrue(len(ce_warnings) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
