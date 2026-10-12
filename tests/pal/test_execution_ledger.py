"""S5 测试：规则/订单/撮合/T+1/账本（任务书 §7 交易+会计场景）。"""
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError
from pal.execution.fill_models import (
    dual_touch_conservative,
    limit_up_price,
    match_buy_limit,
    match_stop_loss_long,
    participation_cap_qty,
)
from pal.execution.market_rules import (
    MAIN_BOARD,
    Order,
    OrderState,
    RuleBook,
)
from pal.ledger.positions import AccountLedger, PositionBook, PositionLot

T0 = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)


def bar(o, h, l, c, vol=1e6):
    return Bar(instrument_id="SSE.600519", timeframe="30m",
               bar_start=T0, bar_end=T0 + timedelta(minutes=30),
               available_at=T0 + timedelta(minutes=30),
               open=o, high=h, low=l, close=c, volume=vol)


class TestMarketRules:
    def test_rules_asof(self):
        rb = RuleBook()
        rb.register(MAIN_BOARD)
        r = rb.rules_for("main", date(2026, 10, 13))
        assert r.t_plus == 1 and r.lot_size == 100

    def test_no_rules_raises(self):
        rb = RuleBook()
        with pytest.raises(KeyError):
            rb.rules_for("star", date(2020, 1, 1))

    def test_limit_prices(self):
        assert limit_up_price(10.0, MAIN_BOARD) == 11.0
        assert limit_up_price(10.0, MAIN_BOARD, is_st=True) == 10.5


class TestOrderState:
    def test_happy_path(self):
        o = Order("ord_1", "plan_1", "buy", "limit", 200, limit_price=10.5)
        o.transition(OrderState.SUBMITTED)
        o.apply_fill(100, 10.4)
        assert o.state == OrderState.PARTIALLY_FILLED
        o.apply_fill(100, 10.45)
        assert o.state == OrderState.FILLED
        assert o.avg_fill_price == pytest.approx(10.425)

    def test_overfill_rejected(self):
        o = Order("ord_1", "p", "buy", "limit", 100, limit_price=10.5)
        o.transition(OrderState.SUBMITTED)
        with pytest.raises(DomainValidationError, match="超量"):
            o.apply_fill(150, 10.4)

    def test_filled_is_terminal(self):
        o = Order("o", "p", "buy", "market", 100)
        o.transition(OrderState.SUBMITTED)
        o.apply_fill(100, 10.0)
        from pal.execution.market_rules import OrderTransitionError
        with pytest.raises(OrderTransitionError):
            o.transition(OrderState.CANCELLED)

    def test_bad_side_rejected(self):
        with pytest.raises(DomainValidationError):
            Order("o", "p", "hold", "market", 100)


class TestFillModels:
    def test_gap_open_fills_at_open_not_stop(self):
        """§7：跳空低于止损按开盘成交，不按更优止损价。"""
        b = bar(9.0, 9.2, 8.8, 9.0)
        r = match_stop_loss_long(b, stop_price=9.5)
        assert r.filled and r.price == 9.0
        assert "gap_open_fill_at_open" in r.assumptions

    def test_intra_bar_stop(self):
        b = bar(10.0, 10.2, 9.6, 9.8)
        r = match_stop_loss_long(b, stop_price=9.7)
        assert r.filled and r.price == 9.7

    def test_one_way_limit_down_cannot_sell(self):
        """一字跌停卖出不保证成交（风险继续存在）。"""
        b = bar(9.0, 9.0, 9.0, 9.0)   # 一字
        r = match_stop_loss_long(b, stop_price=9.5)
        assert not r.filled
        assert "limit_down_cannot_sell" in r.assumptions

    def test_one_way_limit_up_buy_rejected(self):
        b = bar(11.0, 11.0, 11.0, 11.0, vol=0)  # 一字涨停
        r = match_buy_limit(b, limit_price=11.0)
        assert not r.filled

    def test_buy_limit_not_touched(self):
        b = bar(10.5, 10.8, 10.3, 10.6)
        r = match_buy_limit(b, limit_price=10.2)
        assert not r.filled

    def test_dual_touch_conservative_stop(self):
        """同bar双触达 → 保守取止损 + 路径不确定标记。"""
        b = bar(10.0, 12.0, 9.0, 11.0)
        r = dual_touch_conservative(b, stop_price=9.5, target_price=11.5)
        assert r.filled and r.price == 9.5
        assert r.path_uncertain

    def test_participation_cap(self):
        b = bar(10, 10.2, 9.9, 10.1, vol=10000)
        assert participation_cap_qty(5000, b, 0.1) == 1000


class TestTPlusOne:
    def test_same_day_sell_rejected(self):
        """§7：昨100股+今100股，只可卖100。"""
        book = PositionBook()
        d1, d2 = date(2026, 10, 13), date(2026, 10, 14)
        book.add_lot(PositionLot("l1", "SSE.600519", 100, 10.0, d1,
                                 sellable_from=d2))   # 昨天买，今天可卖
        book.add_lot(PositionLot("l2", "SSE.600519", 100, 10.5, d2,
                                 sellable_from=date(2026, 10, 15)))
        assert book.total_qty("SSE.600519") == 200
        assert book.sellable_qty("SSE.600519", d2) == 100   # 只昨天的可卖
        with pytest.raises(DomainValidationError, match="T\\+1"):
            book.reduce("SSE.600519", 200, d2)

    def test_next_day_all_sellable(self):
        book = PositionBook()
        d1 = date(2026, 10, 13)
        book.add_lot(PositionLot("l1", "X", 100, 10.0, d1, date(2026, 10, 14)))
        assert book.sellable_qty("X", date(2026, 10, 14)) == 100


class TestLedger:
    def test_buy_sell_roundtrip_cash_conservation(self):
        """§7 会计：手算两笔交易逐项核对。"""
        led = AccountLedger(initial_cash=100_000.0)
        d1, d2 = date(2026, 10, 13), date(2026, 10, 14)
        # 买 1000股 @10.0：gross=10000, comm=max(2.5,5)=5 → cost 10005
        led.buy("SSE.600519", 1000, 10.0, d1, MAIN_BOARD,
                t1_next_trading_day=d2)
        assert led.cash == pytest.approx(100_000 - 10_005)
        # 卖 1000股 @11.0：gross=11000, comm=5, stamp=5.5 → net 10989.5
        net = led.sell("SSE.600519", 1000, 11.0, d2, MAIN_BOARD)
        assert net == pytest.approx(11_000 - 5 - 5.5)
        assert led.cash == pytest.approx(100_000 - 10_005 + 10_989.5)
        assert led.cash_conservation_check({})
        # NAV 无持仓时 = cash
        assert led.nav({}) == pytest.approx(led.cash)

    def test_insufficient_cash_rejected(self):
        led = AccountLedger(initial_cash=1000.0)
        with pytest.raises(DomainValidationError, match="资金不足"):
            led.buy("X", 1000, 10.0, date(2026, 10, 13), MAIN_BOARD,
                    t1_next_trading_day=date(2026, 10, 14))

    def test_nav_with_mark(self):
        led = AccountLedger(initial_cash=100_000.0)
        d1 = date(2026, 10, 13)
        led.buy("X", 1000, 10.0, d1, MAIN_BOARD,
                t1_next_trading_day=date(2026, 10, 14))
        nav = led.nav({"X": 12.0})
        # cash = 100000-10005 = 89995; 持仓市值 12000 → NAV 101995
        assert nav == pytest.approx(101_995.0)

    def test_sell_more_than_holdings_rejected(self):
        led = AccountLedger(100_000.0)
        d1 = date(2026, 10, 13)
        with pytest.raises(DomainValidationError):
            led.sell("X", 100, 10.0, d1, MAIN_BOARD)

    def test_dividend_via_movement(self):
        """企业行动走账本（分红入账）。"""
        led = AccountLedger(100_000.0)
        led._record("dividend", 50.0, "X cash div")
        assert led.cash == pytest.approx(100_050.0)
        assert led.cash_conservation_check({})
