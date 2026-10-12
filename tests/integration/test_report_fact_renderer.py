"""
R1: report_fact_renderer v8 测试
覆盖：8节结构 / 系统事实 / 观察清单 / 低质量专区 / 风险地图 / 占位符检查 / 一致性
"""

import sys, os, json, unittest
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@dataclass
class MockScoredSignal:
    symbol: str = "600000"
    signal_type: str = "H2"
    direction: str = "long"
    market: str = "A股"
    llm_entry_min: float = 100.0
    llm_entry_max: float = 102.0
    llm_stop_loss: float = 98.0
    llm_tp1: float = 108.0
    llm_tp2: float = None
    llm_score: int = 80
    llm_confidence: float = 0.8
    llm_rr: float = 1.5
    rr: float = 3.0
    stop_loss_pct: float = 0.02
    current_price: float = 101.0
    label: str = "OBSERVE"
    final_grade: str = "C"
    signal_variant: str = "standard"
    structure_evidence: dict = field(default_factory=lambda: {"_price_source": "system:candidate_pool"})
    guardrail_violations: list = field(default_factory=list)
    parser_warnings: list = field(default_factory=list)


def _make_gs(**kw):
    defaults = {
        "symbol": "600276", "signal_type": "H2", "direction": "long",
        "llm_entry_min": 48.0, "llm_entry_max": 49.0, "llm_stop_loss": 47.0,
        "llm_tp1": 51.0, "llm_tp2": None, "rr": 2.5, "llm_rr": 1.5,
        "stop_loss_pct": 0.02, "current_price": 48.5, "label": "OBSERVE",
        "final_grade": "C",
    }
    defaults.update(kw)
    return MockScoredSignal(**defaults)


SAMPLE_MD_HEADER = "# Hermes 策略日报 · 2026-01-01\n"
SAMPLE_SECTION_0 = "## 0. 今日交易结论\n市场震荡偏多。\n"
SAMPLE_SECTION_1 = "## 1. 市场环境与板块温度\n> 震荡偏多\n"
SAMPLE_AUDIT = {
    "report_id": "DAILY_20260101_daily",
    "guardrail_summary": {
        "total_signals": 2, "recorded": 2, "rejected": 0, "duplicates": 0,
        "funnel": {"total_candidates": 10, "main_shortlist": 5, "llm_output": 3,
                    "guardrail_pass": 2, "low_quality_archived": 0, "final_display": 2},
    },
    "contract_compliance": {"total_signals": 2, "complete_signals": 2},
    "evidence_summary": {
        "by_variant": {"standard": 1, "weak": 1, "invalid": 0, "incomplete": 0},
        "rr_diffs": [["600276/H2", 1.5, 3.0, 1.5]],
        "temporal": {"verified_count": 2, "passed_count": 2, "confirmed_swing_count": 4},
    },
    "reject_log": [],
}

_SAMPLE_CARD = """### 600276 恒瑞医药｜医药

**等级**：OBSERVE
**结构结论**：突破前高，量能配合良好，HL序列有效。
**成立条件**：站稳入场区上沿
**失效条件**：跌破47.00
**操作**：观察为主
---
"""


# ═══════════════════════════════════════════════════════════════════
# R1 核心测试
# ═══════════════════════════════════════════════════════════════════

class TestR1EightSections(unittest.TestCase):
    """8 节结构完整性测试。"""

    def setUp(self):
        from report_fact_renderer import rebuild_markdown_report
        self.fn = rebuild_markdown_report

    def test_all_sections_present(self):
        gs = _make_gs(symbol="600276")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        rebuilt = self.fn(md, [gs], SAMPLE_AUDIT)
        for sec in ["## 0.", "## 1.", "## 2. 信号漏斗", "## 3. 明日观察清单",
                     "## 4. 重点信号卡片", "## 5. 回避", "## 6. 风险地图",
                     "## 7. 今日结算", "## 8. 系统状态"]:
            self.assertIn(sec, rebuilt, f"缺少: {sec}")

    def test_observation_list_has_abc(self):
        gs1 = _make_gs(symbol="600276", label="FOCUS", final_grade="A")
        gs2 = _make_gs(symbol="000001", label="OBSERVE", final_grade="C",
                        direction="short")
        gs3 = _make_gs(symbol="300750", label="LOW_QUALITY", final_grade="D",
                        direction="short", stop_loss_pct=0.002, rr=22.0)
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1
        rebuilt = self.fn(md, [gs1, gs2, gs3], {
            "report_id": "x", "guardrail_summary": {
                "total_signals": 3, "recorded": 3, "rejected": 0, "duplicates": 0,
                "funnel": {"total_candidates": 5, "main_shortlist": 3, "llm_output": 3,
                            "guardrail_pass": 3, "low_quality_archived": 0, "final_display": 3},
            },
            "contract_compliance": {"total_signals": 3, "complete_signals": 3},
            "evidence_summary": {"by_variant": {}, "rr_diffs": [],
                                  "temporal": {"verified_count": 3, "passed_count": 3, "confirmed_swing_count": 6}},
            "reject_log": [],
        })
        self.assertIn("A 类", rebuilt)
        self.assertIn("B 类", rebuilt)
        self.assertIn("C 类", rebuilt)

    def test_low_quality_in_section_5(self):
        gs = _make_gs(symbol="300750", label="LOW_QUALITY", final_grade="D",
                       direction="short", stop_loss_pct=0.002, rr=22.0)
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1
        rebuilt = self.fn(md, [gs], {
            "report_id": "x", "guardrail_summary": {
                "total_signals": 1, "recorded": 1, "rejected": 0, "duplicates": 0,
                "funnel": {"total_candidates": 5, "main_shortlist": 1, "llm_output": 1,
                            "guardrail_pass": 1, "low_quality_archived": 1, "final_display": 1},
            },
            "contract_compliance": {"total_signals": 1, "complete_signals": 1},
            "evidence_summary": {"by_variant": {}, "rr_diffs": [],
                                  "temporal": {"verified_count": 1, "passed_count": 1, "confirmed_swing_count": 2}},
            "reject_log": [],
        })
        self.assertIn("## 5. 回避与低质量信号", rebuilt)

    def test_risk_map_present(self):
        gs = _make_gs(symbol="600276")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        rebuilt = self.fn(md, [gs], SAMPLE_AUDIT)
        self.assertIn("## 6. 风险地图", rebuilt)

    def test_no_placeholder(self):
        """禁止出现占位符。"""
        gs = _make_gs(symbol="600276")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        rebuilt = self.fn(md, [gs], SAMPLE_AUDIT)
        for bad in ["关键价位", "样本关键价位"]:
            self.assertNotIn(bad, rebuilt, f"含占位符: {bad}")

    def test_system_facts_table(self):
        """每个信号卡片包含系统事实表。"""
        gs = _make_gs(symbol="600276")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        rebuilt = self.fn(md, [gs], SAMPLE_AUDIT)
        self.assertIn("系统事实", rebuilt)
        self.assertIn("| 方向 |", rebuilt)
        self.assertIn("| 系统 RR |", rebuilt)

    def test_judgment_present(self):
        """每个信号卡片包含判断。"""
        gs = _make_gs(symbol="600276")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        rebuilt = self.fn(md, [gs], SAMPLE_AUDIT)
        self.assertIn("**判断**：", rebuilt)

    def test_low_quality_says_avoid(self):
        """LOW_QUALITY 信号操作建议包含回避。"""
        gs = _make_gs(symbol="300750", label="LOW_QUALITY", final_grade="D",
                       direction="short", stop_loss_pct=0.002, rr=22.0)
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1
        rebuilt = self.fn(md, [gs], {
            "report_id": "x", "guardrail_summary": {
                "total_signals": 1, "recorded": 1, "rejected": 0, "duplicates": 0,
                "funnel": {"total_candidates": 5, "main_shortlist": 1, "llm_output": 1,
                            "guardrail_pass": 1, "low_quality_archived": 1, "final_display": 1},
            },
            "contract_compliance": {"total_signals": 1, "complete_signals": 1},
            "evidence_summary": {"by_variant": {}, "rr_diffs": [],
                                  "temporal": {"verified_count": 1, "passed_count": 1, "confirmed_swing_count": 2}},
            "reject_log": [],
        })
        self.assertIn("回避", rebuilt)
        self.assertIn("🔴", rebuilt)

    def test_observe_not_buy(self):
        """OBSERVE 信号不出现无条件买入。"""
        gs = _make_gs(symbol="600276", label="OBSERVE")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        rebuilt = self.fn(md, [gs], SAMPLE_AUDIT)
        self.assertNotIn("直接买入", rebuilt)
        self.assertNotIn("无条件", rebuilt)

    def test_empty_signals_no_crash(self):
        from report_fact_renderer import rebuild_markdown_report
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0
        rebuilt = rebuild_markdown_report(md, [], {})
        self.assertEqual(rebuilt, md)


class TestR1Idempotent(unittest.TestCase):
    """幂等性测试。"""

    def test_rebuild_idempotent(self):
        from report_fact_renderer import rebuild_markdown_report
        gs = _make_gs(symbol="600276")
        md = SAMPLE_MD_HEADER + SAMPLE_SECTION_0 + SAMPLE_SECTION_1 + _SAMPLE_CARD
        r1 = rebuild_markdown_report(md, [gs], SAMPLE_AUDIT)
        r2 = rebuild_markdown_report(r1, [gs], SAMPLE_AUDIT)
        # 幂等性：核心内容不丢失，结构完整
        self.assertIn("## 0.", r2)
        self.assertIn("## 4. 重点信号卡片", r2)
        self.assertIn("## 8. 系统状态", r2)
        self.assertNotIn("关键价位", r2)


class TestR1Consistency(unittest.TestCase):
    """一致性校验测试。"""

    def test_placeholder_detected(self):
        from report_fact_renderer import validate_report_consistency
        gs = _make_gs(symbol="600276")
        md = "### 600276\n关键价位\n"
        json_data = {"strategy_id": "x", "watchlist": [{"symbol": "600276"}]}
        audit = {"report_id": "x", "guardrail_summary": {"total_signals": 1, "rejected": 0}, "reject_log": []}
        issues = validate_report_consistency(md, json_data, audit, [gs])
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("占位符" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
