"""报告层（S8-02/S8-05）：每日计划与复盘 JSON+Markdown。

从统一决策对象渲染（不自行计算交易事实）；LLM 不参与（S8-06 的
无 LLM 模式完成同一决策输出的前提）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pal.domain.decision import DecisionSnapshot


@dataclass(frozen=True)
class DailyPlanEntry:
    """每日选股表条目（S8-02：准入/待触发/观察/拒绝及原因）。"""
    instrument_id: str
    display_name: str          # 来自 SecurityMaster（禁止手填）
    category: str              # "admitted" | "awaiting_trigger" | "watch" | "rejected"
    reason_codes: List[str]
    detail: Dict[str, object]

    def __post_init__(self):
        if self.category not in ("admitted", "awaiting_trigger", "watch", "rejected"):
            raise ValueError(f"category 非法: {self.category}")


def render_daily_plan(plan_date: str, entries: Sequence[DailyPlanEntry],
                      run_id: str, config_version: str) -> Dict[str, object]:
    """S8-02：全部可执行候选保留（展示层 Top-K 不反向裁掉研究日志）。"""
    categorized: Dict[str, List] = {"admitted": [], "awaiting_trigger": [],
                                    "watch": [], "rejected": []}
    for e in entries:
        categorized[e.category].append(asdict(e))
    doc = {
        "schema": "daily_plan/v1",
        "plan_date": plan_date,          # 文案语义：次日计划
        "run_id": run_id,
        "config_version": config_version,
        "generated_for_next_session": True,
        "summary": {k: len(v) for k, v in categorized.items()},
        "entries": categorized,
        "disclaimer": "盘后产物：次日计划；不构成投资建议",
    }
    return doc


def daily_plan_markdown(doc: Dict[str, object]) -> str:
    """Markdown 渲染（同一数据源，不重算）。"""
    s = doc["summary"]
    lines = [
        f"# 每日选股计划（{doc['plan_date']}，次日生效）",
        "",
        f"- run: `{doc['run_id']}` | config: `{doc['config_version']}`",
        f"- 准入 {s['admitted']} | 待触发 {s['awaiting_trigger']} | "
        f"观察 {s['watch']} | 拒绝 {s['rejected']}",
        "",
    ]
    for cat, label in (("admitted", "准入"), ("awaiting_trigger", "待触发"),
                       ("watch", "观察"), ("rejected", "拒绝")):
        rows = doc["entries"][cat]
        if not rows:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for r in rows:
            reasons = ",".join(r["reason_codes"])
            lines.append(f"- **{r['display_name']}** ({r['instrument_id']}) [{reasons}]")
        lines.append("")
    lines.append("> " + doc["disclaimer"])
    return "\n".join(lines)


def write_outputs(doc: Dict[str, object], json_path: str, md_path: str) -> None:
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(daily_plan_markdown(doc))
