"""完备性自查脚本：核对 §7 验收场景的测试覆盖。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# §7 关键场景 → 覆盖测试文件（人工映射，脚本只报告跑没跑过）
SCENARIOS = {
    "因果:追加K线不改过去决策": "tests/pal/test_swings_regime.py::TestCausalSwings::test_prefix_stability_property",
    "因果:右3棒确认前摆点不可用": "tests/pal/test_swings_regime.py::TestCausalSwings::test_unconfirmed_candidate_not_emitted",
    "因果:available_at早于bar_end拒绝": "tests/pal/test_security_bars.py::TestBarCausality::test_available_before_bar_end_rejected",
    "因果:供应商延迟顺延可见性": "tests/pal/test_security_bars.py::TestBarCausality::test_supplier_delay_pushes_availability",
    "结构:H2代理反例(单HL不计数)": "tests/pal/test_engine_patterns.py::TestStrictH2Verdict::test_single_hl_not_counted_as_h2",
    "结构:breakout极端收盘反例": "tests/test_breakout_extremes.py::TestBreakoutExtremeCloseFix::test_long_close_at_40pct_rejected",
    "结构:setup成立未确认不成交": "tests/pal/test_lifecycle_pricing.py::TestStateMachine::test_raw_cannot_trigger_directly",
    "结构:幅度递减非楔形": "tests/pal/test_engine_patterns.py::TestWedge::test_not_monotonic_rejected",
    "结构:无突破位大棒非强突破": "tests/pal/test_engine_patterns.py::TestBreakoutStrengthConvergence::test_no_level_no_strong_even_big_bar",
    "价格:缺结构证据insufficient": "tests/pal/test_lifecycle_pricing.py::TestBreakoutPricing::test_empty_evidence_never_generic",
    "价格:多头目标在入场下方硬拒": "tests/pal/test_lifecycle_pricing.py::TestFinalFlagPricing::test_event3_target_conflict_with_direction_rejected",
    "交易:当日买入盘中止损不虚构卖出": "tests/pal/test_execution_ledger.py::TestTPlusOne::test_same_day_sell_rejected",
    "交易:T+1昨100今100只可卖100": "tests/pal/test_execution_ledger.py::TestTPlusOne::test_same_day_sell_rejected",
    "交易:跳空低于止损按开盘不按stop": "tests/pal/test_execution_ledger.py::TestFillModels::test_gap_open_fills_at_open_not_stop",
    "交易:一字板不保证成交": "tests/pal/test_execution_ledger.py::TestFillModels::test_one_way_limit_down_cannot_sell",
    "交易:同bar双触达保守+路径不确定": "tests/pal/test_execution_ledger.py::TestFillModels::test_dual_touch_conservative_stop",
    "交易:期末持仓估值不强平": "tests/pal/test_replay.py::TestReplayer::test_last_bar_not_force_closed",
    "会计:手算两笔逐项一致": "tests/pal/test_execution_ledger.py::TestLedger::test_buy_sell_roundtrip_cash_conservation",
    "会计:现金守恒": "tests/pal/test_execution_ledger.py::TestLedger::test_dividend_via_movement",
    "组合:现金只够部分标的确定性分配": "tests/pal/test_portfolio_risk.py::TestPositionSizing::test_cash_constraint",
    "组合:多模型同票一份净持仓": "tests/pal/test_selection.py::TestMergeDedupe::test_five_models_one_position",
    "研究:成本/撮合假设变化与账本一致": "tests/pal/test_execution_ledger.py::TestLedger::test_buy_sell_roundtrip_cash_conservation",
    "研究:标签purge不穿越": "tests/pal/test_research_framework.py::TestTimeSplit::test_purge_removes_boundary_labels",
    "研究:空仓零交易NA非假造": "tests/pal/test_research_framework.py::TestMetrics::test_ir_zero_vol_returns_none",
    "研究:数据不足INCONCLUSIVE": "tests/pal/test_research_framework.py::TestReleaseGate::test_insufficient_samples_inconclusive",
    "运营:数据源失败闭锁新开仓": "tests/pal/test_data_quality_snapshot.py::TestFreshness::test_source_error_locks",
    "运营:供应商分歧不静默拼接": "tests/pal/test_data_quality_snapshot.py::TestQuality::test_source_conflict_raises",
}

results = {}
failures = []
for name, nodeid in SCENARIOS.items():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", nodeid, "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=ROOT)
    ok = r.returncode == 0 and "passed" in r.stdout
    results[name] = "COVERED" if ok else "MISSING"
    if not ok:
        failures.append((name, nodeid, r.stdout[-300:]))

print(json.dumps({
    "total_scenarios": len(SCENARIOS),
    "covered": sum(1 for v in results.values() if v == "COVERED"),
    "missing": sum(1 for v in results.values() if v == "MISSING"),
    "detail": results,
}, ensure_ascii=False, indent=1))
if failures:
    print("\nFAILURES:")
    for n, nid, out in failures:
        print(f"  {n} -> {nid}\n    {out}")
