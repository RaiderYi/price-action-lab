"""S3-05 候选多源去重合并 + S3-07 排序 + S3-08 生命周期。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Sequence, Tuple

from pal.selection.providers import Candidate
from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class MergedCandidate:
    """同票多源合并结果：一份净意图，保留支持/冲突关系。"""
    instrument_id: str
    sources: Tuple[str, ...]          # 支持该票的全部来源（去重）
    conflicts: Tuple[str, ...]        # 方向冲突的来源（记录不丢弃）
    first_available_at: datetime
    estimate: object = None           # 保留最强估计（不重复占用风险预算）
    direction_votes: Tuple[str, ...] = ()


def merge_candidates(cands: Sequence[Candidate]) -> List[MergedCandidate]:
    """同票合并：一个证券不因五个来源获得五份仓位（任务书 S3-05）。"""
    by_inst: Dict[str, List[Candidate]] = {}
    for c in cands:
        by_inst.setdefault(c.instrument_id, []).append(c)
    merged = []
    for iid in sorted(by_inst):
        group = by_inst[iid]
        directions = [c.meta.get("direction") for c in group if c.meta.get("direction")]
        # 方向归类：buy/long → 多；sell/short → 空
        def _side(d):
            return "long" if d in ("buy", "long") else "short" if d in ("sell", "short") else None
        sides = [_side(d) for d in directions]
        long_n = sides.count("long")
        short_n = sides.count("short")
        conflicts = []
        if long_n and short_n:
            # 有真实冲突：以多数侧为准，少数侧记入 conflicts
            majority = "long" if long_n >= short_n else "short"
            for c, s in zip(group, sides):
                if s and s != majority:
                    conflicts.append("+".join(c.source_models))
        sources = sorted({m for c in group for m in c.source_models})
        merged.append(MergedCandidate(
            instrument_id=iid, sources=tuple(sources),
            conflicts=tuple(conflicts),
            first_available_at=min(c.available_at for c in group),
            direction_votes=tuple(filter(None, sides)),
        ))
    return merged


# ═══════════════════════════════════════════════════════════
# S3-07 排序：分数可分解、同分确定性
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RankedCandidate:
    instrument_id: str
    score: float
    components: Dict[str, float]      # 分解：可解释
    tiebreak_key: tuple               # 同分确定性 tiebreak

    def __post_init__(self):
        for k, v in self.components.items():
            if v != v or v in (float("inf"), float("-inf")):
                raise DomainValidationError(f"分数分量非法 {k}={v}")


def rank_by_score(merged: Sequence[MergedCandidate],
                  scorer, top_k: int = 10) -> List[RankedCandidate]:
    """通用排序：scorer(m) -> (score, components)。同分按 tiebreak 排。

    K 由调用方预注册，不依据测试结果反复挑选（任务书 S3-07）。
    """
    ranked = []
    for m in merged:
        score, components = scorer(m)
        ranked.append(RankedCandidate(
            instrument_id=m.instrument_id, score=score, components=components,
            tiebreak_key=(m.instrument_id,),  # 确定性：同分按代码排序
        ))
    ranked.sort(key=lambda r: (-r.score, r.tiebreak_key))
    return ranked[:top_k] if top_k else ranked


# ═══════════════════════════════════════════════════════════
# S3-08 候选生命周期：盘后候选次日生效 + 隔夜重验证
# ═══════════════════════════════════════════════════════════

class CandidateExpiredError(RuntimeError):
    pass


@dataclass
class CandidateLifecycle:
    """候选有效期管理。"""
    max_valid_hours: int = 24          # 盘后候选最早次日生效，有效期至次日收盘

    def validate_for_session(self, cand: Candidate,
                             session_open: datetime,
                             now: datetime) -> Tuple[bool, str]:
        """次日开盘重验证（S3-08）。

        通过条件：now >= eligible_from（不早于生成时刻生效），
        且未超出有效期。停牌/风险事件/超出入场区的作废由执行层
        补充（此处管时间维度）。
        """
        if now < cand.eligible_from:
            return False, f"NOT_YET_ELIGIBLE: now({now}) < eligible_from({cand.eligible_from})"
        expiry = cand.eligible_from + timedelta(hours=self.max_valid_hours)
        if now > expiry:
            return False, f"EXPIRED: now({now}) > expiry({expiry})"
        if session_open.date() < cand.available_at.date():
            return False, "CANDIDATE_FROM_FUTURE_SESSION"
        return True, "OK"
