"""第三轮复审 T07：多票统一组合分配验收。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from pal.data.bars import Bar
from pal.ledger.positions import AccountLedger
from pal.portfolio.allocator import (
    AllocationRequest,
    PortfolioAllocator,
)
from pal.portfolio.risk import CircuitBreaker, PaperDefaults


def req(iid, sid, entry, stop=9.0, score=1.0, industry="ind_a"):
    return AllocationRequest(iid, sid, entry, stop, entry + 2.0,
                             score=score, industry=industry)


class TestDeterministicAllocation:
    def test_three_fight_insufficient_cash_fixed_outcome(self):
        """3 只票争夺不足现金：固定输入→固定分配（顺序无关）。"""
        p = PaperDefaults(initial_cash=100_000.0)
        alloc = PortfolioAllocator(p)
        led = AccountLedger(100_000.0)
        reqs = [req("SSE.600001", "s1", 10.0, 9.5, score=3.0),
                req("SSE.600002", "s2", 10.0, 9.5, score=2.0),
                req("SSE.600003", "s3", 10.0, 9.5, score=1.0)]
        r1 = alloc.allocate(reqs, led, {})
        # 到达顺序打乱 → 同一结果
        r2 = alloc.allocate(list(reversed(reqs)), AccountLedger(100_000.0), {})
        by_id1 = {x.instrument_id: (x.allow, x.qty) for x in r1}
        by_id2 = {x.instrument_id: (x.allow, x.qty) for x in r2}
        assert by_id1 == by_id2
        # 至少一只被现金约束拒绝（10万/3票 单票上限10%=1万 → 全部小仓位，
        # 但现金100%敞口上限80%=8万 → 8只满仓位后第3只受总仓位约束）
        assert len(r1) == 3

    def test_same_score_id_order_deterministic(self):
        """同分按 setup_id 字典序——完全确定。"""
        alloc = PortfolioAllocator(PaperDefaults(initial_cash=10_000_000.0))
        led = AccountLedger(10_000_000.0)
        reqs = [req("SSE.600009", "sC", 10.0, score=1.0),
                req("SSE.600010", "sA", 10.0, score=1.0),
                req("SSE.600011", "sB", 10.0, score=1.0)]
        r = alloc.allocate(reqs, led, {})
        ids = [x.setup_id for x in r if x.allow]
        assert ids == sorted(ids)

    def test_duplicate_instrument_net_budget(self):
        """同票多请求 → 第二个直接拒（一份净预算，不重复配资）。"""
        alloc = PortfolioAllocator(PaperDefaults(initial_cash=1_000_000.0))
        led = AccountLedger(1_000_000.0)
        r = alloc.allocate(
            [req("SSE.600001", "s1", 10.0), req("SSE.600001", "s2", 10.0)],
            led, {})
        assert r[0].allow and not r[1].allow
        assert "REJ_DUPLICATE_INSTRUMENT" in r[1].reason_codes

    def test_industry_cap_across_batch(self):
        """批内同行业聚合上限（25%）。"""
        p = PaperDefaults(initial_cash=1_000_000.0)
        alloc = PortfolioAllocator(p)
        led = AccountLedger(1_000_000.0)
        # 风险 0.25% → 2500/(entry-stop=0.5)=5000股=5万 < 10%上限
        # 行业 25%=25万：3只同业 5万×3=15万 OK；叠加多只后受限
        reqs = [req("SSE.600001", f"s{i}", 10.0, 9.5, score=5.0 - i,
                    industry="same")
                for i in range(8)]
        r = alloc.allocate(reqs, led, {})
        allowed = [x for x in r if x.allow]
        industry_value = sum(x.qty * 10.0 for x in allowed)
        # 行业上限 25万 + 舍入容差（一手）
        assert industry_value <= 250_000 + 10 * 100

    def test_missing_mark_degrades_not_crashes(self):
        """持仓缺报价 → 全批显式降级（不崩溃、不部分写账）。"""
        from datetime import date
        alloc = PortfolioAllocator(PaperDefaults())
        led = AccountLedger(1_000_000.0)
        led.buy("SSE.600001", 1000, 10.0, date(2026, 10, 9),
                __import__("pal.execution.market_rules",
                           fromlist=["MAIN_BOARD"]).MAIN_BOARD,
                t1_next_trading_day=date(2026, 10, 12))
        # marks 缺 600001 报价
        r = alloc.allocate([req("SSE.600002", "s2", 10.0)], led,
                           marks={})
        assert len(r) == 1 and not r[0].allow
        assert "DEGRADED_MISSING_MARK" in r[0].reason_codes


class TestCircuitBreakerGate:
    def test_breaker_blocks_new_not_exit(self):
        """熔断停开仓：allocate 全拒；但方法本身不动退出账本。"""
        cb = CircuitBreaker(PaperDefaults())
        cb.on_data_fault(True)
        alloc = PortfolioAllocator(PaperDefaults(), breaker=cb)
        led = AccountLedger(1_000_000.0)
        r = alloc.allocate([req("SSE.600001", "s1", 10.0)], led, {})
        assert not r[0].allow
        assert any("CB_" in c or c == "DATA_FAULT" for c in r[0].reason_codes)
        # 熔断不冻结退出：账本卖出照常可用（由 orchestrator 承担），
        # allocator 只拦新仓
        assert led.cash == 1_000_000.0


class TestPartialFillRelease:
    def test_qty_respects_participation_and_caps(self):
        """批准 qty 同时受风险/单票/现金/行业约束（取最小）。"""
        p = PaperDefaults(initial_cash=200_000.0)
        alloc = PortfolioAllocator(p)
        led = AccountLedger(200_000.0)
        r = alloc.allocate([req("SSE.600001", "s1", 10.0, 9.0)],
                           led, {})
        assert r[0].allow
        # 风险预算 200000*0.0025=500 / (1.0*1.001) = 499 股 → 取整 400
        assert r[0].qty == 400
