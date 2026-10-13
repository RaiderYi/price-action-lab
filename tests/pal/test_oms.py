"""AR09 OMS 验收：生命周期/一单多fill/撤单释放/占用。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.execution.market_rules import Order, OrderState
from pal.oms.service import OmsError, OrderManagementService


def mk_order(oid="o1", qty=1000):
    return Order(order_id=oid, plan_id="p1", side="buy",
                 order_type="stop", qty=qty, stop_price=10.0)


class TestLifecycle:
    def test_submit_reserves_and_tracks(self):
        oms = OrderManagementService()
        o = mk_order()
        r = oms.submit(o, reserve_cash=10_000.0, created_at="t1")
        assert o.state == OrderState.SUBMITTED
        assert not r.released
        assert oms.reserved_cash_outstanding() == 10_000.0

    def test_duplicate_submit_rejected(self):
        oms = OrderManagementService()
        oms.submit(mk_order(), 1000.0)
        with pytest.raises(OmsError):
            oms.submit(mk_order(), 1000.0)

    def test_multi_fill_same_order(self):
        """AR09 核心：一单多 fill（f1+f2+f3 部分成交累计）。"""
        oms = OrderManagementService()
        oms.submit(mk_order(qty=1000), 10_000.0)
        o = oms.orders["o1"]
        oms.apply_fill("o1", 400, 10.0, fill_id="f1")
        assert o.state == OrderState.PARTIALLY_FILLED
        oms.apply_fill("o1", 400, 10.1, fill_id="f2")
        assert o.state == OrderState.PARTIALLY_FILLED
        oms.apply_fill("o1", 200, 10.2, fill_id="f3")
        assert o.state == OrderState.FILLED
        assert o.filled_qty == 1000
        assert o.remaining() == 0

    def test_duplicate_fill_id_idempotent(self):
        oms = OrderManagementService()
        oms.submit(mk_order(qty=1000), 10_000.0)
        o = oms.orders["o1"]
        oms.apply_fill("o1", 400, 10.0, fill_id="f1")
        oms.apply_fill("o1", 400, 10.0, fill_id="f1")   # 重传
        assert o.filled_qty == 400        # 不重复

    def test_cancel_releases_reservation(self):
        oms = OrderManagementService()
        oms.submit(mk_order(qty=1000), 10_000.0)
        oms.apply_fill("o1", 400, 10.0, fill_id="f1")
        cancelled = oms.cancel("o1")
        assert cancelled == 600           # 撤余量
        assert oms.reserved_cash_outstanding() == 0.0   # 占用释放

    def test_cancel_nothing_left_rejected(self):
        oms = OrderManagementService()
        o = oms.submit(mk_order(qty=100), 1000.0)
        oms.apply_fill("o1", 100, 10.0, fill_id="f1")
        with pytest.raises(OmsError):
            oms.cancel("o1")

    def test_terminal_no_more_fills(self):
        oms = OrderManagementService()
        oms.submit(mk_order(qty=100), 1000.0)
        oms.apply_fill("o1", 100, 10.0, fill_id="f1")
        with pytest.raises(Exception):
            oms.apply_fill("o1", 100, 10.0, fill_id="f9")  # 超量
