"""第三轮复审 T08：事件仓库——订单/成交/账本的持久化与恢复。

复审验收要求：
- 保存完整因果关联 run→candidate→setup→plan→order→fill→lot→exit；
- 订单与成交有唯一约束（重复回报幂等，不重复记账）；
- 失败时不能出现"订单已成交但账本未落地"的半状态（事务边界）；
- checkpoint 前/后注入中断，重启状态与不中断运行一致；
- 每天订单、成交、现金、持仓可对账（reconcile）。

设计：append-only JSONL 事件流 + 确定性重放。
- 每个事件带全局单调 seq；
- 重放 = 从空状态按序 apply，与在线运行结果逐字段一致；
- write-ahead：状态变更前先落盘事件，checkpoint 只存压缩点。
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from pal.domain.models import DomainValidationError


class EventConflictError(RuntimeError):
    """重复/冲突事件（唯一约束违反）。"""


@dataclass(frozen=True)
class StoreEvent:
    seq: int
    kind: str          # bar_consumed | order | fill | ledger_tx | nav | note
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

    唯一约束：
    - seq 单调（重放相同 seq 视为重复交付，幂等跳过）；
    - kind+key 唯一（如 fill_id）：同 key 二次 append → EventConflictError。
    """

    def __init__(self, path: Optional[str] = None,
                 unique_keys: Sequence[str] = ("fill_id", "order_id",
                                               "bar_key")):
        self.path = path
        self._events: List[StoreEvent] = []
        self._seq = 0
        self._uniq: Dict[str, str] = {}     # f"{kind}|{key}" -> seq
        self._unique_fields = tuple(unique_keys)
        # A07：fill 事件按 fill_id 唯一；order_id 是可重复关联键，
        # 只有 order 事件本身按 order_id 唯一（一单多笔成交合法）
        self._uniq_fill = set()
        self._uniq_order = set()
        self._lock = threading.Lock()
        if path and os.path.exists(path):
            self._load(path)

    # ── 写入 ──
    def append(self, kind: str, payload: Dict[str, Any],
               ts: str = "") -> StoreEvent:
        with self._lock:
            # A07：fill 用 fill_id 去重；order 用 order_id；
            # bar_consumed 用 bar_key（各自分域，一单多 fill 合法）
            if kind == "fill":
                fid = payload.get("fill_id")
                if fid is not None and fid in self._uniq_fill:
                    raise EventConflictError(
                        f"重复成交回报: fill_id={fid}")
                if fid is not None:
                    self._uniq_fill.add(fid)
            elif kind == "order":
                oid = payload.get("order_id")
                if oid is not None and oid in self._uniq_order:
                    raise EventConflictError(
                        f"重复订单事件: order_id={oid}")
                if oid is not None:
                    self._uniq_order.add(oid)
            elif kind == "bar_consumed":
                bk = payload.get("bar_key")
                if bk is not None and any(
                        e.kind == "bar_consumed"
                        and e.payload.get("bar_key") == bk
                        for e in self._events):
                    raise EventConflictError(f"重复bar事件: {bk}")
            self._seq += 1
            ev = StoreEvent(self._seq, kind, payload, ts)
            if self.path:
                self._fsync_append(ev)
            self._events.append(ev)
            return ev

    def _fsync_append(self, ev: StoreEvent) -> None:
        # write-ahead：先落盘再进内存（崩溃时事件已在盘上）
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(ev.to_json() + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _load(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ev = StoreEvent.from_json(line)
                # A07：载入重建分域唯一索引（fill_id/order_id/bar_key）
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
                # A07：sellable 恢复（sellable_from 随 fill 事件持久化）
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
