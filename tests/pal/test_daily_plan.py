"""S8 测试：每日计划渲染。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.reporting.daily_plan import (
    DailyPlanEntry,
    daily_plan_markdown,
    render_daily_plan,
    write_outputs,
)


def entry(cat="admitted", iid="SSE.600519", name="贵州茅台"):
    return DailyPlanEntry(
        instrument_id=iid, display_name=name, category=cat,
        reason_codes=["OK_STRUCTURE_CONFIRMED"],
        detail={"entry": 101.0})


class TestDailyPlan:
    def test_categories_preserved(self):
        entries = [entry("admitted"), entry("awaiting_trigger"),
                   entry("watch"), entry("rejected")]
        doc = render_daily_plan("2026-10-13", entries, "run_x", "cfg_v1")
        assert doc["summary"] == {"admitted": 1, "awaiting_trigger": 1,
                                  "watch": 1, "rejected": 1}
        # 研究日志不因展示裁剪（S8-02）
        assert all(len(doc["entries"][c]) == 1 for c in doc["entries"])

    def test_bad_category_rejected(self):
        with pytest.raises(ValueError):
            entry("maybe")

    def test_markdown_contains_all_sections(self):
        entries = [entry("admitted"), entry("rejected")]
        doc = render_daily_plan("2026-10-13", entries, "run_x", "cfg_v1")
        md = daily_plan_markdown(doc)
        assert "次日生效" in md
        assert "贵州茅台" in md
        assert "不构成投资建议" in md

    def test_write_outputs_roundtrip(self, tmp_path):
        entries = [entry()]
        doc = render_daily_plan("2026-10-13", entries, "run_x", "cfg_v1")
        j, m = tmp_path / "plan.json", tmp_path / "plan.md"
        write_outputs(doc, str(j), str(m))
        import json
        loaded = json.loads(j.read_text(encoding="utf-8"))
        assert loaded["schema"] == "daily_plan/v1"
        assert "每日选股计划" in m.read_text(encoding="utf-8")

    def test_empty_plan_is_valid_state(self):
        """空仓/无候选不是故障（任务书 §7 运营场景）。"""
        doc = render_daily_plan("2026-10-13", [], "run_x", "cfg_v1")
        assert doc["summary"]["admitted"] == 0
