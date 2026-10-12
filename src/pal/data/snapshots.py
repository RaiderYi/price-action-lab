"""数据快照冻结（S2-07，F10）：可复现的数据 manifest。"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from pal.domain.models import DomainValidationError


@dataclass(frozen=True)
class DataSnapshot:
    snapshot_id: str
    created_at: str
    timeframe: str
    date_range: tuple              # (start_iso, end_iso)
    files: Dict[str, str]          # rel_path -> sha256
    adjustment_basis: str          # "raw" | "forward_adjusted:<version>"
    source: str
    calendar_version: str
    quality_summary: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.files:
            raise DomainValidationError("空快照无意义")
        for k in ("snapshot_id", "adjustment_basis", "source", "calendar_version"):
            if not getattr(self, k):
                raise DomainValidationError(f"{k} 不能为空（复现要素）")

    def to_json(self) -> str:
        d = dict(self.__dict__)
        d["date_range"] = list(self.date_range)
        d["files"] = dict(self.files)
        return json.dumps(d, ensure_ascii=False, sort_keys=True, indent=1)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build_snapshot(files: List[str], timeframe: str, date_range: tuple,
                   adjustment_basis: str, source: str,
                   calendar_version: str,
                   quality_summary: dict | None = None,
                   now_iso: str | None = None) -> DataSnapshot:
    """从文件集合构建冻结快照（同 seed 同输入可复现，F10）。"""
    hashes = {}
    for f in sorted(files):
        hashes[f] = _sha256_file(f)
    digest = hashlib.sha256(
        json.dumps(hashes, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    snap = DataSnapshot(
        snapshot_id=f"snap_{timeframe}_{digest}",
        created_at=now_iso or datetime.now().astimezone().isoformat(timespec="seconds"),
        timeframe=timeframe, date_range=tuple(date_range), files=hashes,
        adjustment_basis=adjustment_basis, source=source,
        calendar_version=calendar_version,
        quality_summary=quality_summary or {},
    )
    return snap


def verify_snapshot(snap: DataSnapshot, base_dir: str) -> dict:
    """校验当前文件集与快照一致（防文件集合变化改变抽样）。"""
    import os
    results = {}
    for rel, expect in snap.files.items():
        p = os.path.join(base_dir, rel)
        if not os.path.exists(p):
            results[rel] = "MISSING"
            continue
        actual = _sha256_file(p)
        results[rel] = "OK" if actual == expect else f"HASH_MISMATCH:{actual[:12]}"
    return results
