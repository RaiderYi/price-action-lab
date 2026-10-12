"""S5-07/08 测试：回放器尾bar + 差异分解。"""
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar
from pal.data.calendar import TZ
from pal.domain.models import DomainValidationError
from pal.execution.market_rules import MAIN_BOARD
from pal.research.replay import SinglePositionReplayer, decompose_diff

D0 = date(2026, 10, 13)


def dbar(i, o, h, l, c, vol=1e6, iid="SSE.600519"):
    d = D0 + timedelta(days=i)
    s = datetime.combine(d, time(9, 30), tzinfo=TZ)
    e = datetime.combine(d, time(15, 0), tzinfo=TZ)
    h = max(h, o, c); l = min(l, o, c)
    return Bar(instrument_id=iid, timeframe="1d", bar_start=s, bar_end=e,
               available_at=e, open=o, high=h, low=l, close=c, volume=vol)


def rising(n=30, p0=10.0):
    bars = []
    for i in range(n):
        px = p0 * (1 + 0.01 * i)
        bars.append(dbar(i, px * 0.998, px * 1.004, px * 0.995, px))
    return bars


class TestReplayer:
    def test_last_bar_not_force_closed(self):
        """F08：末尾不无条件强平。"""
        bars = rising(30)
        rp = SinglePositionReplayer(MAIN_BOARD)
        res = rp.replay("SSE.600519", bars, entry_signal_idx=[1])
        # 持续上涨：target 触发前一直持有；期末若仍持仓 → 估值标记
        if res.open_positions_marked:
            m = res.open_positions_marked[0]
            assert m.exit_reason == "open_eod_mark"
            assert m.exit_price == bars[-1].close     # 估值=最后收盘
        else:
            # 若已止盈离场，交易 reason 应为 target/timeout（合法）
            assert res.trades[-1].exit_reason in ("target", "timeout", "stop")

    def test_open_position_not_fabricated_as_trade(self):
        bars = rising(10)   # 短序列大概率不触 target
        rp = SinglePositionReplayer(MAIN_BOARD)
        res = rp.replay("SSE.600519", bars, entry_signal_idx=[1])
        marked_ids = {id(t) for t in res.open_positions_marked}
        trade_ids = {id(t) for t in res.trades}
        assert not (marked_ids & trade_ids)   # 估值标记不进成交列表

    def test_t1_respected_in_replay(self):
        """当日买入当日不卖（即使触发止损）。"""
        bars = [dbar(0, 10, 10.2, 9.9, 10.0),
                dbar(1, 10.1, 10.3, 10.0, 10.1),     # day1 买入
                dbar(2, 9.0, 9.2, 8.8, 8.9)]         # day2 跳空低触发止损
        rp = SinglePositionReplayer(MAIN_BOARD)
        res = rp.replay("SSE.600519", bars, entry_signal_idx=[1])
        if res.trades:
            t = res.trades[0]
            assert t.exit_date == D0 + timedelta(days=2)
            assert t.exit_price == 9.0    # 开盘而非 stop 10.1*0.95≈9.6
        else:
            assert res.open_positions_marked   # 卖不出也标记

    def test_empty_bars_rejected(self):
        rp = SinglePositionReplayer(MAIN_BOARD)
        with pytest.raises(DomainValidationError):
            rp.replay("X", [], [0])

    def test_nav_positive(self):
        bars = rising(30)
        rp = SinglePositionReplayer(MAIN_BOARD)
        res = rp.replay("SSE.600519", bars, entry_signal_idx=[1])
        assert res.final_nav is not None and res.final_nav > 0


class TestDiffDecomposition:
    def test_components_sum(self):
        comps = decompose_diff(legacy_total=-0.8681, rule_fix=0.3,
                               signal_swap=-0.1, pricing_model=0.2, costs=-0.25)
        total_contrib = sum(c.contribution for c in comps)
        assert total_contrib == pytest.approx(0.15)
        names = {c.component for c in comps}
        assert names == {"rule_fix", "signal_swap", "pricing_model", "costs"}

    def test_not_all_blamed_on_regime(self):
        """S5-08 验收：不将所有差异归于单一因素（结构化4成分）。"""
        comps = decompose_diff(-1.0, 0.1, 0.2, 0.3, -0.4)
        assert len(comps) == 4
        assert all(isinstance(c.legacy_value, float) for c in comps)
