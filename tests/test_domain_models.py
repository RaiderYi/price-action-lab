"""S1-01 测试：领域模型枚举与校验。

任务书 §4 验收：非法时间、负价格、未知方向/状态、无版本输入被明确拒绝。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from pal.domain.models import (
    DomainValidationError,
    Implementation,
    InstrumentId,
    Maturity,
    PositionDirection,
    PriceDirection,
    RunStatus,
    SignalState,
    TimeWindow,
    require_non_negative,
    require_positive_price,
)


class TestDirectionSeparation:
    def test_price_direction_not_trade_action(self):
        assert PriceDirection.UP.value == "up"
        assert PriceDirection.UP.value != "buy"
        with pytest.raises(ValueError):
            PriceDirection("buy")   # up/down 之外的值拒绝

    def test_trade_action_rejects_up(self):
        with pytest.raises(ValueError):
            TradeAction_UP = __import__("pal.domain.models", fromlist=["TradeAction"]).TradeAction("up")

    def test_position_direction_long_only_v1(self):
        assert [d.value for d in PositionDirection] == ["long"]  # 第一版不开空


class TestInstrumentId:
    def test_code_keeps_leading_zero(self):
        iid = InstrumentId(code="000001", exchange="SZSE", board="main")
        assert iid.instrument_id == "SZSE.000001"

    def test_int_code_rejected(self):
        with pytest.raises(DomainValidationError):
            InstrumentId(code=1, exchange="SZSE", board="main")

    def test_non_numeric_code_rejected(self):
        with pytest.raises(DomainValidationError):
            InstrumentId(code="600AAA", exchange="SSE", board="main")

    def test_empty_exchange_rejected(self):
        with pytest.raises(DomainValidationError):
            InstrumentId(code="600519", exchange="", board="main")


class TestValidation:
    def test_negative_price_rejected(self):
        with pytest.raises(DomainValidationError):
            require_positive_price(-0.01, "stop")

    def test_zero_price_rejected(self):
        with pytest.raises(DomainValidationError):
            require_positive_price(0, "entry")

    def test_nan_rejected(self):
        with pytest.raises(DomainValidationError):
            require_positive_price(float("nan"), "entry")

    def test_inf_rejected(self):
        with pytest.raises(DomainValidationError):
            require_positive_price(float("inf"), "entry")

    def test_negative_qty_rejected(self):
        with pytest.raises(DomainValidationError):
            require_non_negative(-1, "qty")


class TestTimeWindow:
    def test_inverted_window_rejected(self):
        with pytest.raises(DomainValidationError):
            TimeWindow(start="2026-10-12T15:00:00+08:00", end="2026-10-12T14:00:00+08:00")

    def test_equal_window_rejected(self):
        with pytest.raises(DomainValidationError):
            TimeWindow(start="2026-10-12T15:00:00+08:00", end="2026-10-12T15:00:00+08:00")

    def test_valid_window_ok(self):
        tw = TimeWindow(start="2026-10-12T09:30:00+08:00", end="2026-10-12T10:00:00+08:00")
        assert tw.start < tw.end


class TestEnumsRejectUnknown:
    def test_signal_state_unknown_rejected(self):
        with pytest.raises(ValueError):
            SignalState("filled")  # 成交不是信号状态（§4：TRIGGERED≠FILLED）

    def test_implementation_unknown_rejected(self):
        with pytest.raises(ValueError):
            Implementation("v9")

    def test_maturity_unknown_rejected(self):
        with pytest.raises(ValueError):
            Maturity("super")

    def test_run_status_unknown_rejected(self):
        with pytest.raises(ValueError):
            RunStatus("whatever")
