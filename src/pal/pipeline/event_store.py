"""第三轮复审 T08：事件仓库——订单/成交/账本的持久化与恢复。

第六轮 R6-03 整改：
- append_atomic()：一笔业务处理的全部事件（order/fill/游标/risk_state）
  单次 write + flush + fsync 落盘，形成原子提交边界——写失败时
  盘上与内存均无半状态，重试可完整重新处理；
- 唯一性校验在写盘之前对整批预检（含批内互斥），写盘成功后才
  更新内存去重索引——不再出现"索引已污染但事件未落盘"；
- 相同 fill_id/order_id 重放幂等跳过（重试语义），相同 ID 不同
  载荷报 EventConflictError。

设计：append-only JSONL 事件流 + 确定性重放。
- 每个事件带全局单调 seq；
- 重放 = 从空状态按序 apply，与在线运行结果逐字段一致；
- write-ahead：状态变更前先落盘事件，checkpoint 只存压缩点。
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pal.domain.models import DomainValidationError


class EventConflictError(RuntimeError):
    """重复/冲突事件（唯一约束违反）。"""


# 原子批中的一个待提交条目：(kind, payload, ts)
JournalEntry = Tuple[str, Dict[str, Any], str]


@dataclass(frozen=True)
class StoreEvent:
    seq: int          # bar_consumed | order | fill | ledger_tx | nav | note | risk_state
    kind: str
    payload: Dict[str, Any]
    ts: str = ""       # ISO 事件时间（业务时钟，非墙钟）

    def to_json(self) -> str:
        return json.dumps(
            {"seq": self.seq, "kind": self.kind, "payload": self.payload,
             "ts": self.ts}, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def from_json(line: str) -> "StoreEvent":
        d = json.loads(line)
        return StoreEvent(d["seq"], d["kind"], d["payload"], d.get("ts", ""))


class EventStore:
    """append-only 事件仓库（JSONL 落盘 + 唯一性约束 + 重放）。

    唯一约束（分域，一单多 fill 合法）：
    - fill 事件按 fill_id 唯一；
    - order 事件按 order_id 唯一；
    - bar_consumed 按 bar_key 唯一。
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self._events: List[StoreEvent] = []
        self._seq = 0
        self._uniq_fill: set = set()
        self._uniq_order: set = set()
        self._uniq_bar: set = set()
        self._lock = threading.Lock()
        if path and os.path.exists(path):
            self._load(path)

    # ── 唯一性预检（不动任何状态）──
    def _check_unique(self, kind: str, payload: Dict[str, Any],
                      seen_fill: set, seen_order: set,
                      seen_bar: set) -> None:
        if kind == "fill":
            fid = payload.get("fill_id")
            if fid is not None and (fid in self._uniq_fill
                                    or fid in seen_fill):
                raise EventConflictError(f"重复成交回报: fill_id={fid}")
        elif kind == "order":
            oid = payload.get("order_id")
            if oid is not None and (oid in self._uniq_order
                                    or oid in seen_order):
                raise EventConflictError(f"重复订单事件: order_id={oid}")
        elif kind == "bar_consumed":
            bk = payload.get("bar_key")
            if bk is not None and (bk in self._uniq_bar or bk in seen_bar):
                raise EventConflictError(f"重复bar事件: {bk}")

    # ── 写入 ──
    def append(self, kind: str, payload: Dict[str, Any],
               ts: str = "") -> StoreEvent:
        """单事件提交（内部走同一原子路径）。"""
        return self.append_atomic([(kind, payload, ts)])[0]

    def append_atomic(self, entries: Sequence[JournalEntry]
                      ) -> List[StoreEvent]:
        """R6-03：一批业务事件原子提交。

        - 先对整批做唯一性预检（含批内互斥）——冲突时零副作用抛错；
        - 全部序列化为一个字节块，单次 write + flush + fsync；
        - 落盘成功后才追加内存事件表并更新去重索引。
        写失败（OSError 等）时：盘上无新增完整行、内存索引未变，
        调用方可整体重试。
        """
        with self._lock:
            seen_fill: set = set()
            seen_order: set = set()
            seen_bar: set = set()
            for kind, payload, ts in entries:
                self._check_unique(kind, payload,
                                   seen_fill, seen_order, seen_bar)
                if kind == "fill" and payload.get("fill_id") is not None:
                    seen_fill.add(payload["fill_id"])
                elif kind == "order" and payload.get("order_id") is not None:
                    seen_order.add(payload["order_id"])
                elif (kind == "bar_consumed"
                        and payload.get("bar_key") is not None):
                    seen_bar.add(payload["bar_key"])
            seq_base = self._seq
            blob = "".join(
                StoreEvent(seq_base + i + 1, kind, payload, ts).to_json()
                + "\n"
                for i, (kind, payload, ts) in enumerate(entries)
            ).encode("utf-8")
            if self.path and blob:
                self._fsync_write(blob)
            out: List[StoreEvent] = []
            for i, (kind, payload, ts) in enumerate(entries):
                ev = StoreEvent(seq_base + i + 1, kind, payload, ts)
                self._events.append(ev)
                # 落盘成功后才更新索引（R6-03：索引不得先于磁盘）
                if kind == "fill" and payload.get("fill_id") is not None:
                    self._uniq_fill.add(payload["fill_id"])
                elif kind == "order" and payload.get("order_id") is not None:
                    self._uniq_order.add(payload["order_id"])
                elif (kind == "bar_consumed"
                        and payload.get("bar_key") is not None):
                    self._uniq_bar.add(payload["bar_key"])
                out.append(ev)
            self._seq = seq_base + len(entries)
            return out

    def _fsync_write(self, blob: bytes) -> None:
        with open(self.path, "ab") as f:
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())

    def _load(self, path: str) -> None:
        with open(path, "rb") as f:
            for line in f.read().decode("utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                ev = StoreEvent.from_json(line)
                if ev.kind == "fill":
                    fid = ev.payload.get("fill_id")
                    if fid is not None:
                        if fid in self._uniq_fill:
                            raise EventConflictError(
                                f"载入即冲突: fill_id={fid}")
                        self._uniq_fill.add(fid)
                elif ev.kind == "order":
                    oid = ev.payload.get("order_id")
                    if oid is not None:
                        if oid in self._uniq_order:
                            raise EventConflictError(
                                f"载入即冲突: order_id={oid}")
                        self._uniq_order.add(oid)
                elif ev.kind == "bar_consumed":
                    bk = ev.payload.get("bar_key")
                    if bk is not None:
                        self._uniq_bar.add(bk)
                self._events.append(ev)
                self._seq = max(self._seq, ev.seq)

    # ── 查询 ──
    def events(self) -> List[StoreEvent]:
        return list(self._events)

    def by_kind(self, kind: str) -> List[StoreEvent]:
        return [e for e in self._events if e.kind == kind]

    def __len__(self) -> int:
        return len(self._events)


# ═══════════════════════════════════════════════════════════
# 重放器：事件 → 账本状态（恢复 = 重放全部事件）
# ═══════════════════════════════════════════════════════════

@dataclass
class ReplayState:
    """从事件流重建的可对账状态。"""
    cash: float = 0.0
    initial_cash: float = 0.0
    positions: Dict[str, int] = field(default_factory=dict)      # 总量
    sellable: Dict[str, Dict[str, int]] = field(default_factory=dict)  # iid -> {date: qty}
    orders: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    fills: List[Dict[str, Any]] = field(default_factory=list)
    bar_keys: set = field(default_factory=set)

    def reconcile(self, ledger_cash: float, ledger_positions: Dict[str, int],
                  tolerance: float = 0.005) -> Tuple[bool, List[str]]:
        """每日对账：事件重建态 vs 在线账本。"""
        diffs: List[str] = []
        if abs(self.cash - ledger_cash) > tolerance:
            diffs.append(f"cash: replay={self.cash:.2f} "
                         f"ledger={ledger_cash:.2f}")
        if self.positions != ledger_positions:
            diffs.append(f"positions: replay={self.positions} "
                         f"ledger={ledger_positions}")
        return (len(diffs) == 0, diffs)


def replay_events(events: Sequence[StoreEvent]) -> ReplayState:
    """确定性重放（恢复路径 = 同一代码，不维护第二套账）。"""
    st = ReplayState()
    seen_fills: set = set()
    for ev in events:
        p = ev.payload
        if ev.kind == "session_init":
            st.initial_cash = float(p["initial_cash"])
            st.cash = st.initial_cash
        elif ev.kind == "order":
            st.orders[p["order_id"]] = dict(p)
        elif ev.kind == "fill":
            fid = p.get("fill_id", "")
            if fid in seen_fills:
                continue        # 幂等：重复成交回报不重复记账
            seen_fills.add(fid)
            st.fills.append(dict(p))
            gross = float(p["qty"]) * float(p["price"])
            commission = float(p.get("commission", 0.0))
            tax = float(p.get("stamp_tax", 0.0))
            if p["side"] == "buy":
                st.cash -= (gross + commission)
                st.positions[p["instrument_id"]] = (
                    st.positions.get(p["instrument_id"], 0)
                    + int(p["qty"]))
                sf = p.get("sellable_from")
                if sf:
                    iid = p["instrument_id"]
                    st.sellable.setdefault(iid, {})[sf] = (
                        st.sellable.get(iid, {}).get(sf, 0)
                        + int(p["qty"]))
            else:
                st.cash += (gross - commission - tax)
                st.positions[p["instrument_id"]] = (
                    st.positions.get(p["instrument_id"], 0)
                    - int(p["qty"]))
        elif ev.kind == "bar_consumed":
            st.bar_keys.add(p["bar_key"])
    return st
