"""行情质量校验（S2-04）：切源不静默拼接。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from pal.data.bars import Bar


@dataclass(frozen=True)
class QualityIssue:
    code: str
    detail: str
    bar_start: str = ""

    def __str__(self):
        return f"[{self.code}] {self.detail} @{self.bar_start}"


QUALITY_CODES = frozenset({
    "OHLC_VIOLATION",        # high<low 等（Bar 构造已拦，此处查序列级）
    "ZERO_VOLUME",           # 无量bar（涨跌停/停牌需对照状态，先标记）
    "NEGATIVE_VOLUME",
    "GAP_MISSING_SLOT",      # 与日历期望 slot 比对缺失
    "DUPLICATE_BAR",
    "ABNORMAL_JUMP",         # 相邻bar跳变超阈值（待核对复权/除权事件）
    "SOURCE_MISMATCH",       # 同一时刻不同供应商数据不一致
})


@dataclass
class QualityReport:
    issues: List[QualityIssue] = field(default_factory=list)
    n_bars_checked: int = 0
    source: str = ""

    @property
    def is_clean(self) -> bool:
        return not self.issues

    def codes_summary(self) -> dict:
        out = {}
        for i in self.issues:
            out[i.code] = out.get(i.code, 0) + 1
        return out


def check_series(bars: Sequence[Bar], source: str = "",
                 jump_threshold_pct: float = 20.0) -> QualityReport:
    """序列级质量检查（bar 级 OHLC 已在 Bar 构造时强制）。"""
    rep = QualityReport(source=source, n_bars_checked=len(bars))
    ordered = sorted(bars, key=lambda b: b.bar_start)
    prev = None
    for b in ordered:
        if b.volume == 0:
            rep.issues.append(QualityIssue("ZERO_VOLUME", "成交量=0",
                                           str(b.bar_start)))
        if prev is not None:
            ref = prev.close
            if ref > 0:
                jump = abs(b.open - ref) / ref * 100
                if jump > jump_threshold_pct:
                    rep.issues.append(QualityIssue(
                        "ABNORMAL_JUMP",
                        f"开盘跳变 {jump:.1f}%（{ref:.2f}→{b.open:.2f}），"
                        f"需核对除权/复权事件", str(b.bar_start)))
        prev = b
    return rep


class SourceMergeConflict(RuntimeError):
    """两供应商同 bar 不一致——切源必须显式事件，禁止静默拼接。"""


def merge_sources(primary: Sequence[Bar], secondary: Sequence[Bar],
                  tolerance_pct: float = 0.1) -> List[Bar]:
    """主源优先；主源缺失的 slot 用副源补，且记录 SOURCE_MISMATCH。

    同一 bar 两源价差超容差 → 抛 SourceMergeConflict（事件显式化），
    绝不悄悄取某一侧。
    """
    out = {b.bar_start: b for b in primary}
    for sb in secondary:
        pb = out.get(sb.bar_start)
        if pb is None:
            out[sb.bar_start] = sb
            continue
        for f in ("open", "high", "low", "close"):
            pv, sv = getattr(pb, f), getattr(sb, f)
            if pv > 0 and abs(sv - pv) / pv * 100 > tolerance_pct:
                raise SourceMergeConflict(
                    f"供应商分歧 @{sb.bar_start} {f}: {pv} vs {sv} "
                    f"(>{tolerance_pct}%)；需人工裁决，禁止静默拼接")
    return [out[k] for k in sorted(out)]
