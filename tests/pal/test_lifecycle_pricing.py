"""S4-06/S4-07 测试：setup 状态机 + 结构定价（F05/F06 场景）。"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError, SignalState
from pal.pricing.structure_prices import (
    InsufficientStructureEvidence,
    price_breakout_long,
    price_final_flag_reversal,
    price_h2_long,
    price_insufficient,
)
from pal.signals.lifecycle import (
    IllegalTransitionError,
    SetupBook,
    SignalStateMachine,
)

T0 = datetime(2026, 10, 13, 10, 0, tzinfo=TZ)


class TestStateMachine:
    def test_happy_path(self):
        sm = SignalStateMachine("setup_x", expires_at=T0 + timedelta(hours=4))
        sm.transition(SignalState.QUALIFIED, T0)
        sm.transition(SignalState.ARMED, T0 + timedelta(minutes=30))
        sm.transition(SignalState.TRIGGERED, T0 + timedelta(hours=1))
        assert sm.state == SignalState.TRIGGERED

    def test_expired_never_revives(self):
        sm = SignalStateMachine("setup_x")
        sm.transition(SignalState.EXPIRED, T0)
        with pytest.raises(IllegalTransitionError, match="复活"):
            sm.transition(SignalState.ARMED, T0 + timedelta(minutes=1))

    def test_raw_cannot_trigger_directly(self):
        """F06：预测不得直接成交——RAW 必须先 QUALIFIED/ARMED。"""
        sm = SignalStateMachine("setup_x")
        with pytest.raises(IllegalTransitionError):
            sm.transition(SignalState.TRIGGERED, T0)

    def test_terminal_absorbs_bar_events(self):
        sm = SignalStateMachine("setup_x", expires_at=T0)
        sm.transition(SignalState.QUALIFIED, T0 - timedelta(minutes=2))
        sm.transition(SignalState.ARMED, T0 - timedelta(minutes=1))
        sm.transition(SignalState.TRIGGERED, T0 - timedelta(minutes=1))
        sm.on_bar(T0 + timedelta(hours=10))   # 触发后过期事件不改状态
        assert sm.state == SignalState.TRIGGERED

    def test_auto_expiry_on_bar(self):
        sm = SignalStateMachine("setup_x", expires_at=T0 + timedelta(hours=1))
        sm.on_bar(T0 + timedelta(hours=2))
        assert sm.state == SignalState.EXPIRED

    def test_full_log(self):
        sm = SignalStateMachine("setup_x")
        sm.transition(SignalState.REJECTED, T0, "REJ_INSUFFICIENT_EVIDENCE")
        assert sm.transition_log[0][3] == "REJ_INSUFFICIENT_EVIDENCE"


class TestSetupBook:
    def test_idempotent_register(self):
        book = SetupBook()
        a = book.register("setup_1", None)
        b = book.register("setup_1", None)
        assert a is b   # 同结构不重复开仓

    def test_cooldown_blocks_refire(self):
        book = SetupBook(cooldown_bars=3)
        book.mark_triggered("H2", 10)
        assert book.in_cooldown("H2", 11)
        assert book.in_cooldown("H2", 12)
        assert not book.in_cooldown("H2", 13)   # bar 13 距 10 已3根

    def test_conflict_detection(self):
        book = SetupBook()
        msg = book.conflict_check({"H2", "breakout"}, {"L2"})
        assert msg is None   # 不同family多空并存=可解释，不算同结构冲突
        msg = book.conflict_check({"H2"}, {"H2"})
        assert msg and "DIRECTION_CONFLICT" in msg


class TestH2Pricing:
    def test_structured_price(self):
        plan = price_h2_long(
            {"HL2": 98.0, "signal_bar_high": 101.0, "prior_high": 104.0},
            current_price=100.5)
        assert plan.price_status == "structured"
        assert plan.stop == 98.0 and plan.entry == 101.0
        assert plan.target >= 104.0

    def test_missing_evidence_rejected(self):
        """任务书 §2.1：breakout/final_flag 空证据 → 禁止 success 定价。"""
        with pytest.raises(InsufficientStructureEvidence, match="缺证据"):
            price_h2_long({}, current_price=100.0)

    def test_stop_above_entry_rejected(self):
        with pytest.raises(DomainValidationError, match="结构非法"):
            price_h2_long(
                {"HL2": 102.0, "signal_bar_high": 101.0, "prior_high": 104.0},
                current_price=100.5)


class TestBreakoutPricing:
    def test_structured(self):
        plan = price_breakout_long(
            {"breakout_level": 100.0, "signal_bar_low": 97.0,
             "measured_target": 112.0}, current_price=100.2)
        assert plan.price_status == "structured"
        assert plan.structure_rr == pytest.approx(4.0)

    def test_target_below_entry_rejected(self):
        with pytest.raises(DomainValidationError):
            price_breakout_long(
                {"breakout_level": 100.0, "signal_bar_low": 97.0,
                 "measured_target": 99.0}, current_price=100.2)

    def test_empty_evidence_never_generic(self):
        with pytest.raises(InsufficientStructureEvidence):
            price_breakout_long({}, current_price=100.0)


class TestFinalFlagPricing:
    def test_event3_target_conflict_with_direction_rejected(self):
        """夹具：target=96 与多头反转方向矛盾 → 必须拒绝（§7：做多目标
        在入场下方 = 硬拒绝，不能 abs 算出正RR）。"""
        with pytest.raises(DomainValidationError, match="target"):
            price_final_flag_reversal(
                {"flag_high": 106.0, "failure_low": 102.0, "measured_target": 96.0},
                current_price=103.0)

    def test_event3_valid_long_reversal(self):
        """R09 后语义：多头自洽字段 flag_low < failure_high < target。"""
        plan = price_final_flag_reversal(
            {"flag_low": 100.0, "failure_high": 104.0, "measured_target": 110.0},
            current_price=103.5)
        assert plan.price_status == "structured"
        assert (plan.entry, plan.stop, plan.target) == (104.0, 100.0, 110.0)
        assert plan.structure_rr == pytest.approx(1.5)

    def test_missing_failure_evidence_rejected(self):
        """事件3 必须有失败确认；旧方向字段（flag_high/failure_low）拒绝。"""
        with pytest.raises(InsufficientStructureEvidence, match="R09"):
            price_final_flag_reversal(
                {"flag_high": 106.0, "measured_target": 96.0},
                current_price=103.0)

    def test_insufficient_explicit(self):
        plan = price_insufficient("no structure evidence")
        assert plan.price_status == "insufficient_evidence"
        assert plan.entry == 0.0
