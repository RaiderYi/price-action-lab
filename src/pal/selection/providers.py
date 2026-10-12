"""统一候选提供者协议（S3-01）+ 五模型桥接解析（S3-02）。

任务书 §4 Candidate 协议要点：
- 候选生成时刻早于使用时刻（eligible_from / available_at 分立）；
- 多来源不是重复持仓（S3-05 去重）；
- STRUCTURED_V1 只从明确 JSON 标记块读取：缺字段/未知版本/时间倒置/
  单位不明一律拒绝，不解析 Markdown 表格。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pal.domain.estimates import SourceEstimate
from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class Candidate:
    """统一候选对象（多提供者同构）。"""
    candidate_id: str
    instrument_id: str                 # "SSE.600519"
    source_models: tuple               # ("m1","m3") 支持模型列表
    available_at: datetime             # 系统可知时刻
    eligible_from: datetime            # 最早可交易时刻（≥available_at）
    estimate: Optional[SourceEstimate]
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.eligible_from < self.available_at:
            raise DomainValidationError(
                f"eligible_from({self.eligible_from}) 早于 available_at("
                f"{self.available_at})：候选不可在其可知前可交易")
        if not self.source_models:
            raise DomainValidationError("候选必须至少有一个来源模型")


class CandidateProvider:
    """提供者基类（S3-01）。缺提供者=能力 disabled，不阻断其余工作。"""

    name: str = "base"

    def candidates(self, asof: datetime) -> List[Candidate]:
        raise NotImplementedError

    def capability(self) -> Dict[str, object]:
        return {"provider": self.name, "available": True}


class StaticPoolProvider(CandidateProvider):
    """静态研究池提供者（合成夹具/历史实验用）。"""
    name = "static_pool"

    def __init__(self, pool: Sequence[str], asof: datetime):
        self._pool = list(pool)
        self._asof = asof

    def candidates(self, asof: datetime) -> List[Candidate]:
        return [
            Candidate(
                candidate_id=f"cand_static_{iid.replace('.', '_')}",
                instrument_id=iid, source_models=("static_pool",),
                available_at=self._asof, eligible_from=self._asof,
                estimate=None)
            for iid in self._pool if self._asof <= asof
        ]


# ═══════════════════════════════════════════════════════════
# S3-02: STRUCTURED_V1 JSON 块解析
# ═══════════════════════════════════════════════════════════

STRUCTURED_V1_MARK = "TRADE_PLAN_STRUCTURED_V1"
_REQUIRED_FIELDS = ("symbol", "direction", "models", "asof")
_KNOWN_DIRECTIONS = frozenset({"buy", "sell", "long", "short"})


class BridgeFormatError(DomainValidationError):
    """STRUCTURED_V1 块非法——桥接拒绝，不猜测。"""


def parse_structured_v1(text: str) -> List[dict]:
    """从文本中提取全部 STRUCTURED_V1 JSON 块并校验。

    拒绝：缺标记块、非法JSON、缺必需字段、未知版本、时间倒置、
    未知方向、代码非数字字符串（前导零保护）。
    """
    blocks = re.findall(
        rf"<!--\s*{STRUCTURED_V1_MARK}\s*-->\s*```json\s*(\{{.*?\}})\s*```",
        text, flags=re.S)
    if not blocks:
        # 无块=空结果（合法：文档无候选）；但有伪造块痕迹时报错
        if STRUCTURED_V1_MARK in text:
            raise BridgeFormatError(
                f"发现 {STRUCTURED_V1_MARK} 标记但无法提取合法 JSON 块")
        return []
    out = []
    for raw in blocks:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            raise BridgeFormatError(f"JSON 非法: {e}") from None
        missing = [f for f in _REQUIRED_FIELDS if f not in obj]
        if missing:
            raise BridgeFormatError(f"缺必需字段: {missing}")
        sym = obj["symbol"]
        if not isinstance(sym, str) or not sym.isdigit():
            raise BridgeFormatError(f"symbol 必须数字字符串(保前导零): {sym!r}")
        if obj["direction"] not in _KNOWN_DIRECTIONS:
            raise BridgeFormatError(f"未知方向: {obj['direction']!r}")
        if not isinstance(obj["models"], list) or not obj["models"]:
            raise BridgeFormatError("models 必须非空列表")
        try:
            asof = datetime.fromisoformat(obj["asof"])
        except (TypeError, ValueError):
            raise BridgeFormatError(f"asof 非法: {obj['asof']!r}") from None
        if "eligible_from" in obj:
            try:
                ef = datetime.fromisoformat(obj["eligible_from"])
            except (TypeError, ValueError):
                raise BridgeFormatError(
                    f"eligible_from 非法: {obj['eligible_from']!r}") from None
            if ef < asof:
                raise BridgeFormatError(
                    f"时间倒置: eligible_from({ef}) < asof({asof})")
        out.append(obj)
    return out


def candidates_from_structured_v1(text: str,
                                  exchange_of=lambda code: "SSE") -> List[Candidate]:
    """STRUCTURED_V1 块 → 统一 Candidate 对象。"""
    cands = []
    for obj in parse_structured_v1(text):
        asof = datetime.fromisoformat(obj["asof"])
        ef = datetime.fromisoformat(obj.get("eligible_from", obj["asof"]))
        est = None
        if any(k in obj for k in ("ev", "wr", "source_ev", "source_wr")):
            est = SourceEstimate(
                source_id="+".join(obj["models"]),
                source_ev=obj.get("ev", obj.get("source_ev")),
                source_wr=obj.get("wr", obj.get("source_wr")),
                probability_status=obj.get("probability_status", "uncalibrated_prior"),
                source_method=obj.get("source_method", "unknown"),
                source_version=obj.get("source_version", "unversioned"),
            )
        cands.append(Candidate(
            candidate_id=f"cand_5m_{obj['symbol']}_{int(asof.timestamp())}",
            instrument_id=f"{exchange_of(obj['symbol'])}.{obj['symbol']}",
            source_models=tuple(obj["models"]),
            available_at=asof, eligible_from=ef, estimate=est,
            meta={"direction": obj["direction"]},
        ))
    return cands
