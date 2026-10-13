"""AR11：统一交易运行服务（TradingRuntime）。

蓝图 §3/§4：CLI/backtest/paper 只是适配器，同一事件流通过同一
输入解析、状态迁移、风险校验和记账逻辑。

本模块收敛此前散在 pal_cli 里的运行逻辑：
- 载入快照（bars/daily/manifest/hash 校验）；
- 构造 TradingCalendar（尊重 manifest.trading_days，V 补充）；
- 注入行业映射（AR08）；
- 驱动 SessionOrchestrator（唯一内核）；
- 产出 run 产物（status/manifest/backtest.json/ledger/events）。

四种模式的差异只在：事件来源（快照/事件文件/实时）、执行适配、
账户隔离（蓝图 §4）——首版 backtest/paper/scan 共用本服务。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time
from typing import Dict, List, Optional, Sequence, Tuple

from pal.data.bars import Bar
from pal.data.calendar import TZ, TradingCalendar
from pal.ledger.positions import AccountLedger
from pal.pipeline.event_store import EventStore
from pal.pipeline.orchestrator import (
    OrchestratorConfig,
    SessionOrchestrator,
)
from pal.selection.providers import Candidate
from pal.signals.engine import EngineConfig


class RuntimeError_(RuntimeError):
    pass


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_bars_jsonl(fp: str) -> List[Bar]:
    bars = []
    with open(fp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            bars.append(Bar(
                instrument_id=d["instrument_id"],
                timeframe=d["timeframe"],
                bar_start=datetime.fromisoformat(d["bar_start"]),
                bar_end=datetime.fromisoformat(d["bar_end"]),
                available_at=datetime.fromisoformat(d["available_at"]),
                open=d["open"], high=d["high"], low=d["low"],
                close=d["close"], volume=d["volume"],
                amount=d.get("amount", 0.0),
                is_final=d.get("is_final", True)))
    return bars


def load_snapshot(snap_dir: str) -> Dict:
    """载入+校验快照（hash/缺文件拒绝——AR01/V01/V09 契约）。"""
    import glob as _glob
    mf = os.path.join(snap_dir, "manifest.json")
    if not os.path.isfile(mf):
        raise RuntimeError_(f"快照缺 manifest.json: {snap_dir}")
    manifest = json.load(open(mf, encoding="utf-8"))
    bars, daily = [], []
    hashes = {}
    for fp in sorted(_glob.glob(os.path.join(snap_dir, "bars_*.jsonl"))):
        hashes[os.path.basename(fp)] = sha256_file(fp)
        bars += load_bars_jsonl(fp)
    for fp in sorted(_glob.glob(os.path.join(snap_dir, "daily_*.jsonl"))):
        hashes[os.path.basename(fp)] = sha256_file(fp)
        daily += load_bars_jsonl(fp)
    declared = manifest.get("file_sha256", {})
    for fn, h in declared.items():
        if not os.path.isfile(os.path.join(snap_dir, fn)):
            raise RuntimeError_(f"声明的输入文件缺失: {fn}")
        if hashes.get(fn) not in (None, h):
            raise RuntimeError_(f"快照文件与冻结 hash 不符: {fn}")
    return {"manifest": manifest, "bars": bars, "daily": daily,
            "input_hashes": hashes}


class TradingRuntime:
    """统一运行服务（AR11）——backtest/paper/scan 共用。"""

    def __init__(self, snap_info: Dict, initial_cash: float = 1_000_000.0,
                 store: Optional[EventStore] = None,
                 engine_version: str = "runtime-v1",
                 ledger: Optional[AccountLedger] = None):
        self.snap = snap_info
        man = snap_info["manifest"]
        # V 补充（蓝图附录A"其他"）：日历尊重 manifest.trading_days，
        # 不再从实际有行情的日期推断
        td = tuple(date.fromisoformat(d)
                   for d in man.get("trading_days", [])) or \
            tuple(sorted({b.bar_start.date() for b in snap_info["bars"]}))
        self.calendar = TradingCalendar(
            td, man.get("calendar_version", "snapshot-derived"))
        # R6-07：paper 恢复场景注入已重放的账本（与 backtest 同内核）
        self.ledger = ledger if ledger is not None             else AccountLedger(initial_cash)
        self.store = store
        cfg = OrchestratorConfig(EngineConfig(engine_version),
                                 calendar=self.calendar)
        self.orch = SessionOrchestrator(cfg, self.ledger, store=store)
        # AR08：行业映射注入 allocator 主链
        self.orch._industries = {
            iid: meta.get("industry", "unknown")
            for iid, meta in man.get("instruments", {}).items()}
        self.history: Dict[str, List[Bar]] = {}
        self._traded_iids: set = set()      # 无 store 时的成交票追踪
        self.daily_by_iid: Dict[str, List[Bar]] = {}
        for b in snap_info["daily"]:
            self.daily_by_iid.setdefault(b.instrument_id, []).append(b)

    # ── 候选（按交易日，蓝图 §5.1.4）──
    def day_candidates(self, d: date) -> List[Candidate]:
        at = datetime.combine(d, time(0), tzinfo=TZ)
        return [Candidate(
            f"cand_{iid.replace('.', '_')}_{d.isoformat()}",
            iid, ("static_pool",), at, at, None)
            for iid in self.snap["manifest"].get("instruments", {})]

    # ── 事件驱动（多票确定性批次）──
    # R6-08：排序键含 instrument_id 字典序平局裁决——同刻多票按票号
    # 排序，输入到达顺序不再改变处理顺序（预注册时间优先规则）。
    # 批内资金/名额竞争由 allocator 按 (score desc, setup_id asc)
    # 确定性分配（T07 协议），与到达顺序无关。
    def process_bars(self, bars: Sequence[Bar]) -> List[str]:
        events: List[str] = []
        for bar in sorted(bars,
                          key=lambda b: (b.available_at, b.bar_start,
                                         b.instrument_id)):
            d = bar.bar_start.date()
            cand = next((c for c in self.day_candidates(d)
                         if c.instrument_id == bar.instrument_id
                         and c.eligible_from <= bar.available_at), None)
            ev = self.orch.on_bar(
                bar.instrument_id, bar,
                bars_30m=self.history.get(bar.instrument_id, []),
                daily_bars=self.daily_by_iid.get(bar.instrument_id, []),
                candidate=cand)
            for e in ev:
                if e.startswith("FILL:"):
                    self._traded_iids.add(bar.instrument_id)
            self.history.setdefault(bar.instrument_id, []).append(bar)
            events.extend(ev)
        return events

    # ── 产物 ──
    def ledger_snapshot(self) -> Dict:
        if self.store:
            traded = {e.payload["instrument_id"]
                      for e in self.store.by_kind("fill")}
        else:
            # 无 store：从历史事件追踪（on_bar 返回的成交事件）
            traded = set(self._traded_iids)
        return {
            "cash": round(self.ledger.cash, 4),
            "positions": {i: self.ledger.positions.total_qty(i)
                          for i in sorted(traded)}}
