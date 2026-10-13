"""第三轮复审 T08：事件仓库持久化与恢复验收。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.pipeline.event_store import (
    EventConflictError,
    EventStore,
    replay_events,
)


class TestUniqueConstraints:
    def test_duplicate_fill_rejected(self):
        es = EventStore()
        es.append("fill", {"fill_id": "f1", "instrument_id": "SSE.600001",
                           "side": "buy", "qty": 100, "price": 10.0})
        with pytest.raises(EventConflictError):
            es.append("fill", {"fill_id": "f1",
                               "instrument_id": "SSE.600001",
                               "side": "buy", "qty": 100, "price": 10.0})

    def test_same_value_different_kind_ok(self):
        """唯一约束按 kind 分域（fill f1 与 order f1 不冲突）。"""
        es = EventStore()
        es.append("fill", {"fill_id": "x", "qty": 1, "price": 1.0,
                           "side": "buy", "instrument_id": "i"})
        es.append("order", {"order_id": "x", "side": "buy", "qty": 1})
        assert len(es) == 2

    def test_duplicate_bar_key_rejected(self):
        es = EventStore()
        es.append("bar_consumed", {"bar_key": "SSE.1|30m|2026-10-13T09:30"})
        with pytest.raises(EventConflictError):
            es.append("bar_consumed",
                      {"bar_key": "SSE.1|30m|2026-10-13T09:30"})


class TestPersistenceAndRecovery:
    def test_reload_from_disk_identical(self):
        """落盘重载 → 事件序列与唯一索引一致。"""
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "events.jsonl")
            es = EventStore(path)
            es.append("session_init", {"initial_cash": 1_000_000.0})
            es.append("order", {"order_id": "o1", "side": "buy", "qty": 100})
            es.append("fill", {"fill_id": "f1", "order_id": "o1",
                               "side": "buy", "qty": 100, "price": 10.0,
                               "instrument_id": "SSE.600001",
                               "commission": 5.0})
            # 重载
            es2 = EventStore(path)
            assert len(es2) == 3
            assert [e.seq for e in es2.events()] == [1, 2, 3]
            # 重载后重复事件仍拒
            with pytest.raises(EventConflictError):
                es2.append("fill", {"fill_id": "f1", "side": "buy",
                                    "qty": 100, "price": 10.0,
                                    "instrument_id": "SSE.600001"})

    def test_crash_recovery_replay_equals_online(self):
        """中断恢复：重放事件 == 在线状态（现金/持仓逐项一致）。"""
        es = EventStore()
        es.append("session_init", {"initial_cash": 1_000_000.0})
        es.append("fill", {"fill_id": "f1", "side": "buy", "qty": 1000,
                           "price": 10.0, "instrument_id": "SSE.600001",
                           "commission": 5.0})
        es.append("fill", {"fill_id": "f2", "side": "sell", "qty": 1000,
                           "price": 11.0, "instrument_id": "SSE.600001",
                           "commission": 5.0, "stamp_tax": 5.5})
        st = replay_events(es.events())
        assert st.cash == pytest.approx(
            1_000_000.0 - 10_005.0 + (11_000.0 - 5.0 - 5.5))
        assert st.positions == {"SSE.600001": 0}

    def test_repeated_fill_delivery_idempotent_in_replay(self):
        """重复成交回报重放不重复记账（fill_id 幂等）。"""
        es = EventStore()
        es.append("session_init", {"initial_cash": 1_000_000.0})
        p = {"fill_id": "f1", "side": "buy", "qty": 100, "price": 10.0,
             "instrument_id": "SSE.600001", "commission": 5.0}
        es.append("fill", p)
        st = replay_events(es.events())
        cash_once = st.cash
        # 模拟重放含手工复制的重复事件（绕过 append 的唯一检查）
        from pal.pipeline.event_store import StoreEvent
        dup = StoreEvent(99, "fill", dict(p), "")
        st2 = replay_events(es.events() + [dup])
        assert st2.cash == cash_once     # 不重复扣款


class TestReconcile:
    def test_daily_reconcile_match_and_mismatch(self):
        es = EventStore()
        es.append("session_init", {"initial_cash": 500_000.0})
        es.append("fill", {"fill_id": "f1", "side": "buy", "qty": 100,
                           "price": 10.0, "instrument_id": "SSE.600001",
                           "commission": 5.0})
        st = replay_events(es.events())
        ok, _ = st.reconcile(ledger_cash=500_000.0 - 1005.0,
                             ledger_positions={"SSE.600001": 100})
        assert ok
        ok2, diffs = st.reconcile(ledger_cash=499_000.0,
                                  ledger_positions={"SSE.600001": 100})
        assert not ok2 and diffs


class TestAtomicity:
    def test_write_ahead_disk_before_memory_visible(self):
        """write-ahead：事件先落盘（崩溃后可恢复），无半状态。"""
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "events.jsonl")
            es = EventStore(path)
            es.append("fill", {"fill_id": "f1", "side": "buy", "qty": 1,
                               "price": 1.0, "instrument_id": "i",
                               "commission": 0.0})
            # append 返回即已 fsync——重载能看到
            es2 = EventStore(path)
            assert len(es2) == 1
            assert es2.by_kind("fill")[0].payload["fill_id"] == "f1"
