"""第二轮复审批次 C 反例：R04/R05/R09/R10其余。先红后绿。"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.context.regime import assess_trend_regime
from pal.context.swings import detect_swings
from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError
from pal.portfolio.risk import ExitPolicyEngine, ExitPolicyState
from pal.pricing.structure_prices import (
    price_final_flag_reversal,
    price_h2_long,
)
from pal.signals.breakout import assess_breakout_strength
from pal.signals.engine import strict_h2_verdict

T0 = datetime(2026, 10, 13, 9, 30, tzinfo=TZ)


def bar30(i, o=10.0, h=10.5, l=9.5, c=10.2, vol=1000.0, iid="SSE.600519",
          at=None):
    s = T0 + timedelta(minutes=30 * i)
    return Bar(instrument_id=iid, timeframe="30m", bar_start=s,
               bar_end=s + timedelta(minutes=30),
               available_at=at or s + timedelta(minutes=30),
               open=o, high=max(h, o, c), low=min(l, o, c), close=c,
               volume=vol)


def swing(kind, price, i_start, confirm_offset=3):
    fs = T0 + timedelta(minutes=30 * i_start)
    cs = fs + timedelta(minutes=30 * confirm_offset)
    from pal.context.swings import SwingPoint
    return SwingPoint(kind, price, fs, cs, cs)


class TestR04StrictH2:
    """R04：趋势门必须真实生效。"""

    def test_trend_quality_gate_enforced(self):
        """复现：L9→H12→L9.5、close10，min_trend_quality=1.1 仍返回 H2。"""
        bars = [bar30(0, c=9.0, h=9.2, l=8.9, o=9.0),
                bar30(1, c=12.0, h=12.2, l=9.0, o=9.5),
                bar30(2, c=9.5, h=9.8, l=9.3, o=10.0),
                bar30(3, c=10.0, h=10.2, l=9.4, o=9.6)]
        swings = [swing("L", 9.0, 0), swing("H", 12.0, 1), swing("L", 9.5, 2)]
        v = strict_h2_verdict(swings, bars, min_trend_quality=1.1)
        assert v is None, "趋势质量门=1.1 仍放行（R04复现：参数未使用）"

    def test_no_trend_prior_high_progression_rejected(self):
        """注释声称'此前H高于更早H'——两个递降H（无牛市推进）应拒绝。"""
        bars = [bar30(0, c=10.0), bar30(1, c=10.5), bar30(2, c=9.8),
                bar30(3, c=10.2)]
        # H 序列递降：12 → 11（非牛市推进）
        swings = [swing("H", 12.0, 0), swing("L", 9.0, 1), swing("H", 11.0, 2),
                  swing("L", 9.5, 3)]
        v = strict_h2_verdict(swings, bars, min_trend_quality=0.0)
        assert v is None, "H 递降（无趋势推进）不应判定 H2"


class TestR05BreakoutFollowThrough:
    """R05：本棒突破≠跟随确认。"""

    def test_first_breakout_bar_not_follow(self):
        """复现：21棒high10.2，末棒high11 low9.9 close10.4（pos≈45%）→strong。"""
        bars = [bar30(i, o=10.0, h=10.2, l=9.9, c=10.05) for i in range(21)]
        bars.append(bar30(21, o=10.1, h=11.0, l=9.9, c=10.4))
        s = assess_breakout_strength(bars, breakout_level=10.2)
        assert not s.actionable_strong, (
            "首根突破棒不得立即获得 strong/actionable（R05复现：本棒当跟随）")
        assert s.follow_through is False or s.follow_through is None

    def test_follow_only_from_later_bar(self):
        """R05：跟随只能来自信号棒之后的完成棒（assess_with_follow_bars）。"""
        from pal.signals.breakout import assess_with_follow_bars
        bars = [bar30(i, o=10.0, h=10.2, l=9.9, c=10.05) for i in range(21)]
        sig = bar30(21, o=10.3, h=11.5, l=10.2, c=11.3)   # 大棒极端收盘突破
        bars.append(sig)
        # 只有信号棒 → 不可判跟随
        s0 = assess_with_follow_bars(bars, sig.bar_start, breakout_level=10.2)
        assert s0.follow_through is None
        # 加入下一棒（收盘仍在位上）→ 跟随成立
        bars.append(bar30(22, o=11.2, h=11.6, l=10.9, c=11.4))
        s1 = assess_with_follow_bars(bars, sig.bar_start, breakout_level=10.2)
        assert s1.follow_through is True
        assert s1.level == "strong" and s1.actionable_strong

    def test_extreme_close_required_for_strong(self):
        """继承 F03 极端收盘质量条件（45% 收盘不给 strong）。"""
        from pal.signals.breakout import assess_with_follow_bars
        bars = [bar30(i, o=10.0, h=10.2, l=9.9, c=10.05) for i in range(21)]
        sig = bar30(21, o=10.3, h=11.5, l=10.2, c=10.5)   # pos≈23% 弱收盘
        bars.append(sig)
        bars.append(bar30(22, o=10.6, h=10.9, l=10.3, c=10.8))
        s = assess_with_follow_bars(bars, sig.bar_start, breakout_level=10.2)
        assert s.level != "strong"     # 弱收盘 → moderate/weak
        assert s.follow_through is not None


class TestR09Pricing:
    def test_final_flag_long_direction_consistent(self):
        """R09复现：flag11/low10/target12 → entry10 stop11 名为多头实为倒挂。"""
        with pytest.raises(DomainValidationError):
            price_final_flag_reversal(
                {"flag_high": 11.0, "failure_low": 10.0, "measured_target": 12.0},
                current_price=10.5)

    def test_h2_target_not_inflated_to_2r(self):
        """R09复现：prior_high=9.5 < entry=10，目标被强抬到12（2R）。"""
        with pytest.raises(DomainValidationError):
            price_h2_long(
                {"HL2": 9.0, "signal_bar_high": 10.0, "prior_high": 9.5},
                current_price=9.8)


class TestR10Remaining:
    def test_trailing_stop_pending_not_immediate(self):
        """R10复现：移动止损立即改 state.stop（9→9.8），本棒回判本棒。"""
        st = ExitPolicyState(stop=9.0)
        eng = ExitPolicyEngine()
        new_stop = eng.update_trailing(st, 9.8)
        # pending 生效：active stop 仍为 9.0，9.8 下一棒生效
        assert st.stop == 9.0 or new_stop == 9.8 and st.stop == 9.0, (
            "移动止损必须 pending 到下一棒（R10：不能用本棒更新回判本棒）")

    def test_swing_available_at_includes_supplier_delay(self):
        """R10复现：确认棒 bar_end 11:30，供应商延迟到 12:30 → 摆点 11:30 可用（错）。"""
        bars = [bar30(0, h=12.0, l=9.0, c=10.0, vol=1),
                bar30(1, h=10.4, l=9.6, c=10.0, vol=1),
                bar30(2, h=10.4, l=9.6, c=10.0, vol=1),
                bar30(3, h=10.4, l=9.6, c=10.0, vol=1)]
        # 给第3根（确认棒）供应商延迟 60 分钟
        delayed = [b if i != 3 else bar30(3, h=10.4, l=9.6, c=10.0,
                                          at=b.bar_end + timedelta(minutes=60))
                   for i, b in enumerate(bars)]
        swings = detect_swings(delayed, confirm_bars=3)
        for s in swings:
            assert s.available_at >= datetime(2026, 10, 13, 12, 30, tzinfo=TZ), (
                "摆点 available_at 必须含确认棒供应商延迟（R10复现）")

    def test_ma60_insufficient_data_unknown(self):
        """R10复现：30根 close=10 → ma60=5（错除法）。应 unknown 或明示缩短。"""
        bars = []
        from datetime import date, time as dtime
        for i in range(30):
            d = date(2026, 1, 5) + timedelta(days=i)
            s = datetime.combine(d, dtime(9, 30), tzinfo=TZ)
            e = datetime.combine(d, dtime(15, 0), tzinfo=TZ)
            bars.append(Bar(instrument_id="X", timeframe="1d", bar_start=s,
                            bar_end=e, available_at=e, open=10.0, high=10.05,
                            low=9.95, close=10.0, volume=1e6, amount=5e7))
        ra = assess_trend_regime(bars, min_bars=30)
        # 30根数据 MA60 不可算 → 特征中 ma60 不得是错值 5
        assert ra.features.get("ma_bull") is None or ra.kind.value == "unknown" \
            or ra.features.get("ma60") != 5.0
