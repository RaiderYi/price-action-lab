#!/usr/bin/env python3
"""
统一信号注册表 (Signal Registry)

系统中所有信号类型的唯一真相源 (Single Source of Truth)。
signal_predictor.py、daily_prompt.md、wiki_assembler.py、
JSON schema、LLM prompt 必须全部引用此注册表。

禁止任何模块自行维护信号类型白名单。
"""

from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════
# 信号等级定义
# ═══════════════════════════════════════════════════════════════════

SIGNAL_GRADES = {
    "A": {
        "label": "重点关注",
        "meaning": "结构清楚、RR达标、止损合理、可直接作为交易参考",
        "max_rr_required": True,     # RR必须达标
        "min_rr": None,              # 从信号类型继承
        "allow_weak_structure": False,
    },
    "B": {
        "label": "普通观察",
        "meaning": "结构基本成立、确认不足或RR勉强达标",
        "max_rr_required": True,
        "min_rr": None,
        "allow_weak_structure": True,
    },
    "C": {
        "label": "谨慎观察",
        "meaning": "有一定结构想象空间，但RR不达标/结构不标准/位置差",
        "max_rr_required": False,    # C级不强制RR达标
        "min_rr": 1.0,              # 但RR必须≥1.0
        "allow_weak_structure": True,
    },
    "D": {
        "label": "暂不参考",
        "meaning": "结构不成立/RR明显不足/信号命名错误/关键证据缺失",
        "max_rr_required": False,
        "min_rr": None,
        "allow_weak_structure": True,
    },
    "REJECT": {
        "label": "拒绝",
        "meaning": "RR<1.0/止损不合理/方向冲突/数据不足",
        "max_rr_required": False,
        "min_rr": None,
        "allow_weak_structure": True,
    },
}

# ═══════════════════════════════════════════════════════════════════
# 信号注册表（14 种信号，唯一真相源）
# ═══════════════════════════════════════════════════════════════════

SIGNAL_REGISTRY: Dict[str, dict] = {
    # ── 趋势延续组 ──
    "H1": {
        "group": "trend_continuation",
        "default_direction": "long",
        "allowed_directions": ["long"],
        "required_regime": ["uptrend", "bull_pullback"],
        "required_fields": ["HL1", "HL2", "prior_high", "trigger_bar", "confirmation"],
        "standard_rule": "HL2 > HL1 and price confirms upside continuation",
        "weak_rule": "HL2 near HL1 or structure unclear, bullish bias but not confirmed",
        "invalid_rule": "HL2 < HL1 by meaningful margin or price reclaims structure low",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["h1-l1-signal", "abc-pullback", "trend-resumption"],
        "risk_notes": ["late trend risk", "failed breakout risk", "double top risk"],
    },
    "H2": {
        "group": "trend_continuation",
        "default_direction": "long",
        "allowed_directions": ["long"],
        "required_regime": ["uptrend", "bull_pullback"],
        "required_fields": ["HL1", "HL2", "prior_high", "trigger_bar", "confirmation"],
        "standard_rule": "HL2 > HL1 and price confirms upside continuation after two-legged pullback",
        "weak_rule": "HL2 near HL1 or second leg pullback shallow, structure suggestive but unconfirmed",
        "invalid_rule": "HL2 < HL1 by meaningful margin or price fails to break HL1 trigger",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["h2-l2-signal", "h2-l2-state-machine", "abc-pullback"],
        "risk_notes": ["trend exhaustion risk", "wedge formation risk", "failed second entry risk"],
    },
    "L1": {
        "group": "trend_continuation",
        "default_direction": "short",
        "allowed_directions": ["short"],
        "required_regime": ["downtrend", "bear_pullback", "breakout_down"],
        "required_fields": ["LH1", "LH2", "prior_low", "trigger_bar", "confirmation"],
        "standard_rule": "LH2 < LH1 and price confirms downside continuation",
        "weak_rule": "LH2 near LH1 or structure unclear, bearish bias but not confirmed",
        "invalid_rule": "LH2 > LH1 by meaningful margin or price reclaims structure high",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["h1-l1-signal", "abc-pullback", "trend-resumption"],
        "risk_notes": ["trend exhaustion risk", "double bottom risk", "failed breakdown risk"],
    },
    "L2": {
        "group": "trend_continuation",
        "default_direction": "short",
        "allowed_directions": ["short"],
        "required_regime": ["downtrend", "bear_pullback", "breakout_down"],
        "required_fields": ["LH1", "LH2", "prior_low", "trigger_bar", "confirmation"],
        "standard_rule": "LH2 < LH1 and price breaks below prior low with bearish confirmation bar",
        "weak_rule": "LH2 near LH1 (within 0.5% of LH1) or second leg pullback shallow — structure suggestive but unconfirmed",
        "invalid_rule": "LH2 > LH1 by meaningful margin (>0.5% above LH1) — bear structure broken, not standard L2",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["h2-l2-signal", "h2-l2-state-machine", "abc-pullback", "trend-continuation"],
        "risk_notes": [
            "LH2>LH1 invalidates standard L2",
            "late trend risk — trend may be mature",
            "range transition risk — trend may be converting to trading range",
            "failed breakdown risk — prior low may hold as double bottom",
        ],
    },
    "BTC": {
        "group": "trend_continuation",
        "default_direction": "long",
        "allowed_directions": ["long"],
        "required_regime": ["strong_uptrend"],
        "required_fields": ["trend_strength", "close_position", "signal_bar"],
        "standard_rule": "Strong bull trend with bull bar closing near high, buy at close of signal bar",
        "weak_rule": "Trend is present but weakening, close not at extreme high",
        "invalid_rule": "Trend is not clearly bullish or bar closes weak (near low)",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["btc-stc", "stc-btc", "trend-inertia"],
        "risk_notes": ["chasing risk — only valid in strong trend", "climax risk", "late entry risk"],
    },
    "STC": {
        "group": "trend_continuation",
        "default_direction": "short",
        "allowed_directions": ["short"],
        "required_regime": ["strong_downtrend"],
        "required_fields": ["trend_strength", "close_position", "signal_bar"],
        "standard_rule": "Strong bear trend with bear bar closing near low, sell at close of signal bar",
        "weak_rule": "Trend is present but weakening, close not at extreme low",
        "invalid_rule": "Trend is not clearly bearish or bar closes strong (near high)",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["btc-stc", "stc-btc", "trend-inertia"],
        "risk_notes": ["chasing risk", "climax risk", "late entry risk"],
    },

    # ── 反转组 ──
    "wedge": {
        "group": "reversal",
        "default_direction": "derived",  # 由趋势方向推导
        "allowed_directions": ["long", "short"],
        "direction_rule": "上升趋势中的楔形→做空，下降趋势中的楔形→做多",
        "required_regime": ["trend_extension", "trend_exhaustion"],
        "required_fields": ["push1_price", "push2_price", "push3_price",
                           "push1_amplitude", "push2_amplitude", "push3_amplitude",
                           "convergence_angle", "third_push_touch_trendline"],
        "standard_rule": "三次推动 + 幅度递减 + 趋势线收敛 + 第三推未触及趋势线",
        "weak_rule": "三推结构存在但幅度递减不明显，或第三推仍触及趋势线",
        "invalid_rule": "少於三次推动，或幅度递增而非递减",
        "min_rr": 2.0,  # 反转信号要求更高 RR
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["wedge-signal", "three-push-wedge", "wedge-gravity-dual-core",
                       "wedge-quality-scoring", "parabolic-wedge", "wedge-flag"],
        "risk_notes": ["premature entry risk", "trend continuation risk", "fourth push risk"],
    },
    "double_bottom": {
        "group": "reversal",
        "default_direction": "long",
        "allowed_directions": ["long"],
        "direction_rule": "下跌趋势中的双底→做多",
        "required_regime": ["downtrend_exhaustion", "range_bottom"],
        "required_fields": ["first_low", "second_low", "low_difference_pct",
                           "trigger_bar", "confirmation"],
        "standard_rule": "两次独立触底、价格接近(差值≤区间宽度的10%)、第二次触底后出现做多确认",
        "weak_rule": "两次触底价格接近但第二次触底无明确确认K线",
        "invalid_rule": "仅一次触底即反弹，或两次触底价差过大(>5%)",
        "min_rr": 2.0,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["double-top-bottom", "micro-double-bottom", "double-pattern"],
        "risk_notes": ["failed reversal risk", "bear trend continuation", "stop run risk"],
    },
    "double_top": {
        "group": "reversal",
        "default_direction": "short",
        "allowed_directions": ["short"],
        "direction_rule": "上升趋势中的双顶→做空",
        "required_regime": ["uptrend_exhaustion", "range_top"],
        "required_fields": ["first_high", "second_high", "high_difference_pct",
                           "trigger_bar", "confirmation"],
        "standard_rule": "两次独立触顶、价格接近(差值≤区间宽度的10%)、第二次触顶后出现做空确认",
        "weak_rule": "两次触顶价格接近但第二次触顶无明确确认K线",
        "invalid_rule": "仅一次触顶即回落，或两次触顶价差过大(>5%)",
        "min_rr": 2.0,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["double-top-bottom", "double-pattern"],
        "risk_notes": ["failed reversal risk", "bull trend continuation", "stop run risk"],
    },
    "climax_reversal": {
        "group": "reversal",
        "default_direction": "derived",
        "allowed_directions": ["long", "short"],
        "direction_rule": "上升高潮后→做空，下跌高潮后→做多",
        "required_regime": ["trend_exhaustion", "climax"],
        "required_fields": ["climax_bar_count", "consecutive_large_bodies",
                           "volume_anomaly", "reversal_confirmation_bar"],
        "standard_rule": "连续大实体K线(≥3根 body>70%)或单根超大K线(body>均值的3倍) + 跟随反向K线确认",
        "weak_rule": "有高潮K线但跟随确认不明显，或高潮后进入TR而非反转",
        "invalid_rule": "单根大阴线不等於高潮反转，必须有跟随确认",
        "min_rr": 2.0,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["climax", "post-climax-reversal", "consecutive-climaxes",
                       "vacuum-climax"],
        "risk_notes": ["false climax risk", "trend continuation after TR", "V-reversal risk"],
    },
    "final_flag": {
        "group": "reversal",
        "default_direction": "derived",
        "allowed_directions": ["long", "short"],
        "direction_rule": "上升趋势末端的最终旗形→做空，下降趋势末端→做多",
        "required_regime": ["trend_exhaustion", "trend_end"],
        "required_fields": ["flag_pole_length", "flag_consolidation_bars",
                           "breakout_direction", "breakout_failure_evidence"],
        "standard_rule": "长旗杆 + 10-20棒旗形盘整 + 突破失败返回旗形区间",
        "weak_rule": "旗形结构存在但旗杆较短或盘整不充分",
        "invalid_rule": "旗杆不明显或突破成功延续原趋势",
        "min_rr": 2.0,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["final-flag", "final-flags", "flag-pennant"],
        "risk_notes": ["false reversal risk", "breakout continuation risk", "premature entry risk"],
    },

    # ── 区间组 ──
    "tr_fade": {
        "group": "range",
        "default_direction": "derived",
        "allowed_directions": ["long", "short"],
        "direction_rule": "区间下沿→做多，区间上沿→做空",
        "required_regime": ["trading_range"],
        "required_fields": ["range_high", "range_low", "current_position_pct",
                           "boundary_test_evidence"],
        "standard_rule": "价格在明确区间边界、出现边界测试K线(影线/小实体/反转K线)",
        "weak_rule": "价格接近边界但无明确测试K线",
        "invalid_rule": "无明确区间边界，或价格在区间中间",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["tr-fade", "trading-range-reversal", "trading-range-characteristics"],
        "risk_notes": ["breakout risk", "false boundary test", "thin range risk"],
    },
    "eighty_twenty": {
        "group": "range",
        "default_direction": "derived",
        "allowed_directions": ["long", "short"],
        "direction_rule": "80%极值处→做多(低位)/做空(高位)",
        "required_regime": ["trading_range"],
        "required_fields": ["range_high", "range_low", "current_percentile",
                           "extreme_bar_evidence"],
        "standard_rule": "价格在区间80%+极值位置 + 出现反转K线证据",
        "weak_rule": "价格在极值区域但无明确反转信号",
        "invalid_rule": "无明确区间或不在极值区域",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["eighty-percent-rule", "range-zone-positioning"],
        "risk_notes": ["breakout risk at extremes", "trend day risk", "thin range risk"],
    },

    # ── 测量组 ──
    "measured_move": {
        "group": "measurement",
        "default_direction": "derived",
        "allowed_directions": ["long", "short"],
        "direction_rule": "突破方向决定",
        "required_regime": ["breakout", "trend_continuation"],
        "required_fields": ["measurement_leg_start", "measurement_leg_end",
                           "target_projection", "breakout_confirmation"],
        "standard_rule": "有清晰测量腿 + 突破确认 + 目标位基于测量投影",
        "weak_rule": "测量腿存在但突破确认不充分",
        "invalid_rule": "无清晰测量腿或突破失败",
        "min_rr": 1.5,
        "can_be_high_quality_if_rr_below_min": False,
        "can_be_observe_if_rr_below_min": True,
        "max_stop_loss_pct": 0.025,
        "kb_concepts": ["measured-move", "path-ab-breakout"],
        "risk_notes": ["measurement error risk", "failed breakout risk", "partial move risk"],
    },
}
# ═══════════════════════════════════════════════════════════════════
# Phase 2-3-4.0-C: Signal Definition Registry v3 (KB确认版)
# 18 信号: 4 strict(NOT_IMPLEMENTED) + 4 proxy + 10 others
# ═══════════════════════════════════════════════════════════════════

SIGNAL_DEFINITION_REGISTRY: Dict[str, dict] = {
    # ═══ bar_counting family (strict Brooks, NOT IMPLEMENTED) ═══
    "brooks_h1_strict": {
        "signal_type": "brooks_h1_strict", "display_name_cn": "严格 Brooks H1",
        "pa_family": "bar_counting", "direction": "long",
        "definition_version": "brooks_h1_strict_v1", "implementation_version": "NOT_IMPLEMENTED",
        "maturity": "NOT_IMPLEMENTED", "strict_match": True, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": False, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "bull pullback 中第一次 high > prior_bar.high 的K线",
        "required_context": ["bull_move", "pullback"],
        "required_trigger": ["high_gt_prior_high", "first_up_bar_in_pullback"],
        "trigger_rule": "high > prior_bar.high (bar counting)",
        "entry_rule": "price breaks above H1 signal bar high",
        "stop_rule": "below H1 signal bar low minus 1 tick",
        "invalid_conditions": ["not_in_bull_pullback", "stop_hit"],
        "code_detector": None, "price_builder": None, "guardrail_rules": [],
        "report_allowed_wording": ["严格 Brooks H1 第一次向上尝试成立"],
        "report_forbidden_wording": ["不要把 proxy 称为 H1"],
    },
    "brooks_h2_strict": {
        "signal_type": "brooks_h2_strict", "display_name_cn": "严格 Brooks H2 第二次向上尝试",
        "pa_family": "bar_counting", "direction": "long",
        "definition_version": "brooks_h2_strict_v1", "implementation_version": "NOT_IMPLEMENTED",
        "maturity": "NOT_IMPLEMENTED", "strict_match": True, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": False, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "bull pullback 中第二次 high > prior_bar.high 的K线。H2终结第二波调整，经典二次入场买点。所有小型双底本质上是H2。",
        "required_context": ["bull_move", "pullback", "two_leg_pullback", "h1_already_occurred"],
        "required_trigger": ["high_gt_prior_high", "second_up_bar_in_pullback", "trigger_bar_breaks_h2_high"],
        "trigger_rule": "high > prior_bar.high (bar counting, 非 close-based)",
        "entry_rule": "price breaks above H2 signal bar high",
        "stop_rule": "below H2 signal bar low minus 1 tick",
        "invalid_conditions": ["not_in_bull_pullback", "h2_low_broken", "new_low_made", "stop_hit"],
        "code_detector": None, "price_builder": None, "guardrail_rules": [],
        "report_allowed_wording": ["严格 Brooks H2 第二次向上尝试成立"],
        "report_forbidden_wording": ["不要把 higher-low proxy 称为 Brooks H2"],
    },
    "brooks_l1_strict": {
        "signal_type": "brooks_l1_strict", "display_name_cn": "严格 Brooks L1",
        "pa_family": "bar_counting", "direction": "short",
        "definition_version": "brooks_l1_strict_v1", "implementation_version": "NOT_IMPLEMENTED",
        "maturity": "NOT_IMPLEMENTED", "strict_match": True, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": False, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "bear rally 中第一次 low < prior_bar.low 的K线",
        "required_context": ["bear_move", "rally"],
        "required_trigger": ["low_lt_prior_low", "first_down_bar_in_rally"],
        "trigger_rule": "low < prior_bar.low (bar counting)",
        "entry_rule": "price breaks below L1 signal bar low",
        "stop_rule": "above L1 signal bar high plus 1 tick",
        "invalid_conditions": ["not_in_bear_rally", "stop_hit"],
        "code_detector": None, "price_builder": None, "guardrail_rules": [],
        "report_allowed_wording": ["严格 Brooks L1 第一次向下尝试成立"],
        "report_forbidden_wording": ["不要把 proxy 称为 L1"],
    },
    "brooks_l2_strict": {
        "signal_type": "brooks_l2_strict", "display_name_cn": "严格 Brooks L2 第二次向下尝试",
        "pa_family": "bar_counting", "direction": "short",
        "definition_version": "brooks_l2_strict_v1", "implementation_version": "NOT_IMPLEMENTED",
        "maturity": "NOT_IMPLEMENTED", "strict_match": True, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": False, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "bear rally 中第二次 low < prior_bar.low 的K线。L2终结第二波反弹，经典二次入场卖点。所有小型双顶本质上是L2。",
        "required_context": ["bear_move", "rally", "two_leg_rally", "l1_already_occurred"],
        "required_trigger": ["low_lt_prior_low", "second_down_bar_in_rally", "trigger_bar_breaks_l2_low"],
        "trigger_rule": "low < prior_bar.low (bar counting, 非 close-based)",
        "entry_rule": "price breaks below L2 signal bar low",
        "stop_rule": "above L2 signal bar high plus 1 tick",
        "invalid_conditions": ["not_in_bear_rally", "l2_high_broken", "new_high_made", "stop_hit"],
        "code_detector": None, "price_builder": None, "guardrail_rules": [],
        "report_allowed_wording": ["严格 Brooks L2 第二次向下尝试成立"],
        "report_forbidden_wording": ["不要把 lower-high proxy 称为 Brooks L2"],
    },

    # ═══ swing_proxy family (当前生产, is_proxy=true) ═══
    "H1": {
        "signal_type": "H1", "display_name_cn": "H1代理（higher-low proxy）",
        "pa_family": "swing_proxy", "direction": "long",
        "definition_version": "hermes_h1_proxy_v1", "implementation_version": "hermes_h1_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": True, "proxy_for": "brooks_h1_strict",
        "enabled": False, "implemented": True, "manual_review_status": "APPROVE_AS_PROXY",
        "core_definition_cn": "复用H2的swing-point检测器，无独立实现。不是严格Brooks H1。",
        "code_detector": "supported_via_H2_reuse (_detect_h2)",
        "report_allowed_wording": ["系统识别为 H1 代理信号（非严格 Brooks H1）"],
        "report_forbidden_wording": ["严格 Brooks H1 成立"],
        "notes": "Phase 4.1 后标记 legacy。",
    },
    "H2": {
        "signal_type": "H2", "display_name_cn": "H2代理（higher-low proxy）",
        "pa_family": "swing_proxy", "direction": "long",
        "definition_version": "hermes_h2_proxy_v1", "implementation_version": "hermes_h2_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": True, "proxy_for": "brooks_h2_strict",
        "legacy_names": ["legacy_h2_proxy", "hermes_h2_v1"],
        "enabled": True, "implemented": True, "manual_review_status": "APPROVE_AS_PROXY",
        "core_definition_cn": "两个逐次抬高的swing low (HL1<HL2, HL2<CP)。不是严格Brooks H2 (bar counting)。",
        "code_detector": "_detect_h2",
        "report_allowed_wording": ["系统当前H2为higher-low proxy；不等同于严格Brooks H2"],
        "report_forbidden_wording": ["严格 Brooks H2 成立", "价格行为学 H2 二次入场", "经典 H2 做多"],
    },
    "L1": {
        "signal_type": "L1", "display_name_cn": "L1代理（lower-high proxy）",
        "pa_family": "swing_proxy", "direction": "short",
        "definition_version": "hermes_l1_proxy_v1", "implementation_version": "hermes_l1_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": True, "proxy_for": "brooks_l1_strict",
        "enabled": False, "implemented": True, "manual_review_status": "APPROVE_AS_PROXY",
        "core_definition_cn": "复用L2的swing-point检测器。不是严格Brooks L1。",
        "code_detector": "复用 _detect_l2",
        "report_allowed_wording": ["系统识别为 L1 代理信号"],
        "report_forbidden_wording": ["严格 Brooks L1 成立"],
    },
    "L2": {
        "signal_type": "L2", "display_name_cn": "L2代理（lower-high proxy）",
        "pa_family": "swing_proxy", "direction": "short",
        "definition_version": "hermes_l2_proxy_v1", "implementation_version": "hermes_l2_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": True, "proxy_for": "brooks_l2_strict",
        "legacy_names": ["legacy_l2_proxy", "hermes_l2_v1"],
        "enabled": True, "implemented": True, "manual_review_status": "APPROVE_AS_PROXY",
        "core_definition_cn": "两个逐次降低的swing high (LH1>LH2, LH2>CP)。不是严格Brooks L2 (bar counting)。",
        "code_detector": "_detect_l2",
        "report_allowed_wording": ["系统识别为 L2 代理信号（非严格 Brooks L2）"],
        "report_forbidden_wording": ["严格 Brooks L2 成立", "Brooks L2 二次入场"],
    },

    # ═══ reversal family ═══
    "wedge": {
        "signal_type": "wedge", "display_name_cn": "楔形",
        "pa_family": "reversal", "direction": "derived",
        "definition_version": "brooks_wedge_v1", "implementation_version": "hermes_wedge_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": True, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB — PARTIAL_MATCH",
        "core_definition_cn": "三推+幅度递减+趋势线收敛。三推结构本质是H3/L3。",
        "code_detector": "_detect_wedge",
        "report_allowed_wording": ["楔形结构"],
        "report_forbidden_wording": [],
        "notes": "PARTIAL_MATCH: 第三推趋势线触及验证偏弱。recommended_action=STRICT_IMPLEMENTATION_REVIEW。",
    },
    "climax_reversal": {
        "signal_type": "climax_reversal", "display_name_cn": "高潮反转",
        "pa_family": "reversal", "direction": "derived",
        "definition_version": "brooks_climax_v1", "implementation_version": "hermes_climax_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB — PARTIAL_MATCH",
        "core_definition_cn": "趋势末端剧烈加速(高潮)+衰竭+反向。冲击与交易区间模式。",
        "code_detector": "_detect_climax",
        "report_allowed_wording": ["高潮反转形态"],
        "report_forbidden_wording": [],
        "notes": "缺趋势末端前置条件(趋势持续20+bar后)。recommended_action=ADD_TREND_EXHAUSTION_CONTEXT。",
    },
    "final_flag": {
        "signal_type": "final_flag", "display_name_cn": "末端旗形反转",
        "pa_family": "trend_exhaustion", "direction": "derived",
        "definition_version": "brooks_final_flag_v1", "implementation_version": "hermes_final_flag_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": True, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "趋势末端窄幅盘整，原趋势突破失败后反向突破。趋势终结信号。",
        "code_detector": "_detect_final_flag",
        "report_allowed_wording": ["末端旗形（趋势终结信号）"],
        "report_forbidden_wording": [],
        "notes": "KB已确认。recommended_action=STRICT_IMPLEMENTATION_REVIEW。",
    },

    # ═══ price_action_pattern (H2/L2形态表达) ═══
    "double_bottom": {
        "signal_type": "double_bottom", "display_name_cn": "双底（H2形态表达）",
        "pa_family": "price_action_pattern", "direction": "long",
        "definition_version": "brooks_db_v1", "implementation_version": "hermes_double_pattern_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": "brooks_h2_strict",
        "enabled": False, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "两次触底近似同一水平。每个小型双底本质上是H2买入设置。",
        "code_detector": "_detect_double_pattern",
        "report_allowed_wording": ["双底（H2形态表达）"],
        "report_forbidden_wording": [],
        "notes": "本质是H2的形态化表达。recommended_action=LINK_TO_H2_L2_STRICT。",
    },
    "double_top": {
        "signal_type": "double_top", "display_name_cn": "双顶（L2形态表达）",
        "pa_family": "price_action_pattern", "direction": "short",
        "definition_version": "brooks_dt_v1", "implementation_version": "hermes_double_pattern_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": "brooks_l2_strict",
        "enabled": False, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "两次触顶近似同一水平。每个小型双顶本质上是L2卖出设置。",
        "code_detector": "_detect_double_pattern",
        "report_allowed_wording": ["双顶（L2形态表达）"],
        "report_forbidden_wording": [],
        "notes": "本质是L2的形态化表达。recommended_action=LINK_TO_H2_L2_STRICT。",
    },

    # ═══ breakout (Focus v1 新增: 延续核·动能入场, 精选突破) ═══
    "breakout": {
        "signal_type": "breakout", "display_name_cn": "精选突破（selected breakout entry）",
        "pa_family": "breakout", "direction": "both",
        "definition_version": "brooks_breakout_v1_focus", "implementation_version": "hermes_breakout_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": True, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "大区间棒突破前高/前低且收在棒体极端、区间扩张≥1.2ATR。Brooks最爱的精选突破（收在前高之上、离突破区间越远越好），过滤75%失败突破。",
        "code_detector": "_is_breakout_entry",
        "trigger_rule": "close beyond prior_high/prior_low (lookback 20 bars) AND close in extreme 30% of bar AND bar_range >= 1.2*ATR",
        "entry_rule": "breakout bar close 或 回测突破位不破再入场",
        "stop_rule": "突破棒中点或突破位下方 1 tick",
        "invalid_conditions": ["close back inside range", "failed_breakout_risk"],
        "report_allowed_wording": ["精选突破（精选标准：收在前高之上+区间扩张+收在极端）"],
        "report_forbidden_wording": ["把所有突破都当信号（75%突破会失败，仅做精选）"],
        "notes": "Focus v1 (2026-10-11): 10大形态#3。Channel 75%规律的顺势表达——只做那25%的优质突破。",
    },

    # ═══ trading_range_strategy ═══
    "tr_fade": {
        "signal_type": "tr_fade", "display_name_cn": "交易区间反转（trading range reversal）",
        "pa_family": "trading_range_strategy", "direction": "derived",
        "definition_version": "brooks_tr_reversal_v1", "implementation_version": "hermes_tr_fade_v1 (CURRENT)",
        "maturity": "TRADE_READY", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": True, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB",
        "core_definition_cn": "交易区间底部1/3买入、顶部1/3卖出。区间边界失败突破后的反向交易策略。",
        "code_detector": "_detect_tr_fade",
        "report_allowed_wording": ["交易区间反转策略（原tr_fade）"],
        "report_forbidden_wording": [],
        "notes": "KB确认: strict strategy但非孤立形态信号。recommended_action=RENAME_REVIEW。display_label建议trading_range_reversal。",
    },

    # ═══ context_factor ═══
    "eighty_twenty": {
        "signal_type": "eighty_twenty", "display_name_cn": "80-20法则（context factor）",
        "pa_family": "range_context", "direction": "derived",
        "definition_version": "brooks_8020_principle_v1", "implementation_version": "hermes_8020_v1 (CURRENT)",
        "maturity": "CONTEXT_FACTOR", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB — 不是独立信号",
        "core_definition_cn": "Brooks统计规律: 交易区间内80%突破尝试会失败。是TR Fade的概率基础，不可独立交易。",
        "code_detector": "_detect_eighty_twenty",
        "report_allowed_wording": ["80-20背景概率（用于辅助TR Fade判断）"],
        "report_forbidden_wording": ["80-20交易信号", "eighty_twenty做多/做空"],
        "notes": "recommended_action=CONVERT_TO_CONTEXT_FACTOR。不独立产生交易候选。",
    },

    # ═══ measurement_tool ═══
    "measured_move": {
        "signal_type": "measured_move", "display_name_cn": "测量移动（目标投影工具）",
        "pa_family": "measurement_tool", "direction": "derived",
        "definition_version": "brooks_mm_v1", "implementation_version": "hermes_mm_v1 (CURRENT)",
        "maturity": "STRUCTURE_READY", "strict_match": False, "is_proxy": False, "proxy_for": None,
        "enabled": False, "implemented": True, "manual_review_status": "CONFIRMED_BY_KB — 非入场信号",
        "core_definition_cn": "目标=基准点±前一波段高度。用于TP/RR测算，不单独构成入场信号。",
        "code_detector": "_detect_measured_move",
        "report_allowed_wording": ["测量移动目标投影（TP参考工具）"],
        "report_forbidden_wording": ["测量移动入场信号", "measured_move做多/做空"],
        "notes": "recommended_action=USE_AS_TARGET_PROJECTION_TOOL。",
    },

    # ═══ disabled ═══
    "buy_the_close": {
        "signal_type": "buy_the_close", "display_name_cn": "收盘买入 (disabled)",
        "pa_family": "disabled", "direction": "long",
        "definition_version": "disabled", "implementation_version": "disabled",
        "maturity": "disabled", "strict_match": False, "is_proxy": True, "proxy_for": None,
        "enabled": False, "implemented": False, "manual_review_status": "CONFIRMED_BY_KB — 非核心Brooks信号",
        "core_definition_cn": "非核心策略。KB确认: 是入场时机策略而非基于形态结构的信号。保持disabled。",
        "report_allowed_wording": [],
        "report_forbidden_wording": [],
    },
    "sell_the_close": {
        "signal_type": "sell_the_close", "display_name_cn": "收盘卖出 (disabled)",
        "pa_family": "disabled", "direction": "short",
        "definition_version": "disabled", "implementation_version": "disabled",
        "maturity": "disabled", "strict_match": False, "is_proxy": True, "proxy_for": None,
        "enabled": False, "implemented": False, "manual_review_status": "CONFIRMED_BY_KB — 非核心Brooks信号",
        "core_definition_cn": "同buy_the_close。保持disabled。",
        "report_allowed_wording": [],
        "report_forbidden_wording": [],
    },
}

# ═══════════════════════════════════════════════════════════════════
# Phase 3: 扩展访问器 + 违规词扫描器
# ═══════════════════════════════════════════════════════════════════

def get_signal_definition(signal_type: str) -> dict:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, SIGNAL_REGISTRY.get(signal_type, {}))

def get_all_signal_definitions() -> Dict[str, dict]:
    return dict(SIGNAL_DEFINITION_REGISTRY)

def get_live_signal_types() -> List[str]:
    return [st for st, cfg in SIGNAL_DEFINITION_REGISTRY.items() if cfg.get("enabled", False)]

def get_strict_signal_types() -> List[str]:
    return [st for st, cfg in SIGNAL_DEFINITION_REGISTRY.items() if cfg.get("strict_match", False)]

def get_proxy_signal_types() -> List[str]:
    return [st for st, cfg in SIGNAL_DEFINITION_REGISTRY.items() if cfg.get("is_proxy", False)]

def is_strict_signal(signal_type: str) -> bool:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("strict_match", False)

def is_proxy_signal(signal_type: str) -> bool:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("is_proxy", False)

def get_pa_family(signal_type: str) -> str:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("pa_family", "unknown")

def get_report_allowed_wording(signal_type: str) -> List[str]:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("report_allowed_wording", [])

def get_report_forbidden_wording(signal_type: str) -> List[str]:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("report_forbidden_wording", [])

def get_definition_version(signal_type: str) -> str:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("definition_version", "unknown")

def get_implementation_version(signal_type: str) -> str:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("implementation_version", "unknown")

def get_manual_review_status(signal_type: str) -> str:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("manual_review_status", "UNKNOWN")

def format_signal_label(signal_type: str) -> str:
    cfg = SIGNAL_DEFINITION_REGISTRY.get(signal_type, {})
    if cfg.get("is_proxy") and cfg.get("enabled"):
        return f"{signal_type}代理（{cfg.get('pa_family','')} proxy，非严格价格行为学 {signal_type}）"
    if not cfg.get("enabled") and not cfg.get("implemented"):
        return f"{signal_type}（未实现）"
    return signal_type

def get_signal_display_name(signal_type: str) -> str:
    return SIGNAL_DEFINITION_REGISTRY.get(signal_type, {}).get("display_name_cn", signal_type)

def get_display_signal_label(signal_type: str) -> str:
    cfg = SIGNAL_DEFINITION_REGISTRY.get(signal_type, {})
    if cfg.get("is_proxy") and cfg.get("enabled"):
        pa = cfg.get("pa_family", "proxy")
        if pa == "swing_proxy":
            short = "higher-low proxy" if cfg.get("direction") == "long" else "lower-high proxy"
            return f"{signal_type}代理（{short}）"
        return f"{signal_type}代理"
    if not cfg.get("enabled") and not cfg.get("implemented"):
        return f"{signal_type}（未实现）"
    return signal_type

def get_proxy_disclaimer(signal_type: str) -> str:
    cfg = SIGNAL_DEFINITION_REGISTRY.get(signal_type, {})
    if cfg.get("is_proxy") and cfg.get("proxy_for"):
        strict_name = cfg["proxy_for"]
        return f"当前工程代理实现，尚未满足严格价格行为学 {strict_name} 定义。"
    return ""

# Phase 3: 报告违规词扫描器
_PROXY_FORBIDDEN_PATTERNS = [
    "严格 Brooks H2 成立", "严格 Brooks L2 成立",
    "严格 Brooks H1 成立", "严格 Brooks L1 成立",
    "标准 H2", "标准 L2",
    "价格行为学 H2 成立", "价格行为学 L2 成立",
    "Brooks H2 买点", "Brooks L2 卖点",
    "Brooks H2 二次入场", "Brooks L2 二次入场",
    "经典 H2 做多", "经典 L2 做空",
]

def check_report_violations(report_text: str, signal_type: str) -> list:
    cfg = SIGNAL_DEFINITION_REGISTRY.get(signal_type, {})
    if not cfg.get("is_proxy"):
        return []
    violations = []
    for pattern in _PROXY_FORBIDDEN_PATTERNS:
        if pattern in report_text:
            idx = report_text.find(pattern)
            start = max(0, idx - 20)
            end = min(len(report_text), idx + len(pattern) + 20)
            snippet = report_text[start:end].replace('\n', ' ')
            violations.append((pattern, snippet))
    return violations

def get_all_forbidden_patterns() -> list:
    return list(_PROXY_FORBIDDEN_PATTERNS)



# ═══════════════════════════════════════════════════════════════════
# 结构化证据 Schema (Structured Evidence Schema)
#
# 每种信号类型的必须/可选证据字段。
# rule_guardrail 据此判断"结构失败" vs "证据缺失"。
# ═══════════════════════════════════════════════════════════════════

EVIDENCE_SCHEMA: Dict[str, dict] = {
    # ── 趋势延续组 ──
    "H1": {
        "required_evidence": ["HL1", "HL2", "prior_high", "trigger_bar", "confirmation"],
        "optional_evidence": ["pullback_strength", "trend_context", "volume_confirmation"],
        "validation_rules": [
            "HL2 > HL1 (second higher low after pullback)",
            "price breaks above HL1 trigger after pullback",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无 HL1/HL2 不得判定为 H1",
    },
    "H2": {
        "required_evidence": ["HL1", "HL2", "prior_high", "trigger_bar", "confirmation"],
        "optional_evidence": ["pullback_strength", "trend_context", "volume_confirmation",
                              "second_leg_depth", "ema_position"],
        "validation_rules": [
            "HL2 > HL1 (second higher low after two-legged pullback)",
            "price breaks above HL1 trigger after second leg",
            "two distinct pullback legs visible",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无 HL1/HL2 不得判定为 H2",
    },
    "L1": {
        "required_evidence": ["LH1", "LH2", "prior_low", "trigger_bar", "confirmation"],
        "optional_evidence": ["pullback_strength", "trend_context", "volume_confirmation"],
        "validation_rules": [
            "LH2 < LH1 (second lower high after pullback)",
            "price breaks below LH1 trigger after pullback",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无 LH1/LH2 不得判定为 L1",
    },
    "L2": {
        "required_evidence": ["LH1", "LH2", "prior_low", "trigger_bar", "confirmation"],
        "optional_evidence": ["pullback_strength", "trend_context", "volume_confirmation",
                              "second_leg_depth", "ema_position", "daily_trend_alignment"],
        "validation_rules": [
            "LH2 < LH1 by margin > 0.5% × LH1 (standard) or within tolerance (weak)",
            "LH2 > LH1 → invalid_or_weak_L2, not standard L2",
            "price breaks below prior_low with bearish confirmation bar",
            "trend context must be bearish (downtrend/breakout_down/bear_pullback)",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无 LH1/LH2 标记为 evidence_missing，最高 OBSERVE",
    },
    "BTC": {
        "required_evidence": ["trend_strength", "close_position", "signal_bar"],
        "optional_evidence": ["volume_confirmation", "ema_position", "prior_bars_strength"],
        "validation_rules": [
            "strong bull trend with bull bar closing near high",
            "close position in upper 25% of bar range",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE",
    },
    "STC": {
        "required_evidence": ["trend_strength", "close_position", "signal_bar"],
        "optional_evidence": ["volume_confirmation", "ema_position", "prior_bars_strength"],
        "validation_rules": [
            "strong bear trend with bear bar closing near low",
            "close position in lower 25% of bar range",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE",
    },

    # ── 反转组 ──
    "wedge": {
        "required_evidence": ["push_1_price", "push_2_price", "push_3_price",
                             "push_1_amplitude", "push_2_amplitude", "push_3_amplitude",
                             "momentum_change", "trend_context"],
        "optional_evidence": ["convergence_angle", "third_push_touch_trendline",
                             "volume_divergence", "climax_confirmation"],
        "validation_rules": [
            "three distinct pushes in same direction",
            "push amplitudes decreasing (push_3 < push_2 < push_1)",
            "momentum visibly declining on third push",
            "trend context must be trend_extension or trend_exhaustion",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无三推数据不得判定为 wedge",
    },
    "double_bottom": {
        "required_evidence": ["bottom_1_price", "bottom_2_price", "neckline",
                             "second_test_result", "confirmation"],
        "optional_evidence": ["low_difference_pct", "volume_on_second_test",
                             "trend_context", "trigger_bar"],
        "validation_rules": [
            "two distinct bottoms at similar price (difference ≤ 10% of range width)",
            "second test shows failed breakdown (price rejects and closes above bottom_1)",
            "neckline identified between two bottoms",
            "confirmation bar breaks above neckline",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无两次触底数据不得判定为 double_bottom",
    },
    "double_top": {
        "required_evidence": ["top_1_price", "top_2_price", "neckline",
                             "second_test_result", "confirmation"],
        "optional_evidence": ["high_difference_pct", "volume_on_second_test",
                             "trend_context", "trigger_bar"],
        "validation_rules": [
            "two distinct tops at similar price (difference ≤ 10% of range width)",
            "second test shows failed breakout (price rejects and closes below top_1)",
            "confirmation bar breaks below neckline",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无两次触顶数据不得判定为 double_top",
    },
    "climax_reversal": {
        "required_evidence": ["climax_bar_count", "consecutive_large_bodies",
                             "reversal_confirmation_bar", "trend_context"],
        "optional_evidence": ["volume_anomaly", "climax_bar_details",
                             "post_climax_tr_bars"],
        "validation_rules": [
            "≥3 consecutive bars with body>70% of range, OR single bar body>3× mean",
            "a reversal confirmation bar follows the climax",
            "trend must be extended/mature",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE",
    },
    "final_flag": {
        "required_evidence": ["flag_pole_length", "flag_consolidation_bars",
                             "breakout_direction", "breakout_failure_evidence",
                             "trend_maturity"],
        "optional_evidence": ["flag_type", "volume_during_flag", "failed_breakout_detail"],
        "validation_rules": [
            "long flag pole preceding the flag consolidation",
            "10-20 bar flag consolidation",
            "breakout attempt fails and price returns into flag range",
            "trend must be mature (trend_maturity ≥ 0.6)",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE",
    },

    # ── 区间组 ──
    "tr_fade": {
        "required_evidence": ["trading_range_high", "trading_range_low",
                             "current_position_pct", "boundary_test_result"],
        "optional_evidence": ["failed_breakout_evidence", "volume_at_boundary",
                             "range_quality", "trend_context"],
        "validation_rules": [
            "clear trading range boundaries identified",
            "price at extreme of range (near high for short, near low for long)",
            "boundary test shows rejection (wick/reversal bar)",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无区间边界数据不得判定为 tr_fade",
    },
    "eighty_twenty": {
        "required_evidence": ["trading_range_high", "trading_range_low",
                             "current_percentile", "extreme_bar_evidence"],
        "optional_evidence": ["failed_breakout_evidence", "volume_at_extreme"],
        "validation_rules": [
            "price in 80%+ percentile of trading range",
            "reversal bar evidence at extreme",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE",
    },

    # ── 测量组 ──
    "measured_move": {
        "required_evidence": ["measure_start", "measure_end", "breakout_point",
                             "projected_target", "target_basis"],
        "optional_evidence": ["measure_leg_type", "breakout_quality_score",
                             "volume_on_breakout", "partial_targets"],
        "validation_rules": [
            "clear measurement leg (impulse move) identified",
            "breakout confirmed (close beyond breakout point)",
            "target projected based on measurement leg length",
        ],
        "missing_evidence_policy": "INCOMPLETE_EVIDENCE — 无测量依据不得判定为 measured_move",
    },
}

# ═══════════════════════════════════════════════════════════════════
# Evidence 辅助函数
# ═══════════════════════════════════════════════════════════════════

def get_evidence_schema(signal_type: str) -> dict:
    """获取信号类型的证据 schema。"""
    return EVIDENCE_SCHEMA.get(signal_type, {})

def get_required_evidence(signal_type: str) -> List[str]:
    """获取信号类型必须的结构证据字段。"""
    return EVIDENCE_SCHEMA.get(signal_type, {}).get("required_evidence", [])

def get_optional_evidence(signal_type: str) -> List[str]:
    """获取信号类型可选的结构证据字段。"""
    return EVIDENCE_SCHEMA.get(signal_type, {}).get("optional_evidence", [])

def get_validation_rules(signal_type: str) -> List[str]:
    """获取信号类型的验证规则。"""
    return EVIDENCE_SCHEMA.get(signal_type, {}).get("validation_rules", [])

def check_evidence_completeness(signal_type: str, evidence: dict) -> dict:
    """检查结构化证据的完整性。
    
    Returns:
        {"complete": bool, "missing_required": [...], "missing_optional": [...],
         "completeness_pct": float}
    """
    schema = EVIDENCE_SCHEMA.get(signal_type, {})
    required = schema.get("required_evidence", [])
    optional = schema.get("optional_evidence", [])
    
    missing_required = [f for f in required if f not in evidence or evidence[f] is None]
    missing_optional = [f for f in optional if f not in evidence or evidence[f] is None]
    
    total_fields = len(required) + len(optional)
    provided = total_fields - len(missing_required) - len(missing_optional)
    
    return {
        "complete": len(missing_required) == 0,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "completeness_pct": provided / total_fields if total_fields > 0 else 0,
    }

def get_signal_types() -> List[str]:
    """返回所有注册的信号类型名（14种）。"""
    return list(SIGNAL_REGISTRY.keys())

def get_signal_group(signal_type: str) -> str:
    """返回信号所属组别。"""
    return SIGNAL_REGISTRY.get(signal_type, {}).get("group", "unknown")

def get_signal_groups() -> Dict[str, List[str]]:
    """返回按组别分类的信号类型。"""
    groups: Dict[str, List[str]] = {}
    for st, cfg in SIGNAL_REGISTRY.items():
        g = cfg["group"]
        groups.setdefault(g, []).append(st)
    return groups

def get_kb_concepts(signal_type: str) -> List[str]:
    """返回信号类型对应的 KB 概念列表。"""
    return SIGNAL_REGISTRY.get(signal_type, {}).get("kb_concepts", [])

def get_min_rr(signal_type: str) -> float:
    """返回信号类型的最低 RR 要求。"""
    return SIGNAL_REGISTRY.get(signal_type, {}).get("min_rr", 1.5)

def get_required_fields(signal_type: str) -> List[str]:
    """返回信号类型要求的结构证据字段。"""
    return SIGNAL_REGISTRY.get(signal_type, {}).get("required_fields", [])

def is_reversal_signal(signal_type: str) -> bool:
    """判断是否为反转类信号。"""
    return get_signal_group(signal_type) == "reversal"

def is_trend_continuation(signal_type: str) -> bool:
    """判断是否为趋势延续类信号。"""
    return get_signal_group(signal_type) == "trend_continuation"

def is_range_signal(signal_type: str) -> bool:
    """判断是否为区间类信号。"""
    return get_signal_group(signal_type) == "range"

def get_all_kb_concepts() -> List[str]:
    """返回所有信号类型引用的 KB 概念（去重）。"""
    all_concepts = set()
    for cfg in SIGNAL_REGISTRY.values():
        all_concepts.update(cfg.get("kb_concepts", []))
    return sorted(all_concepts)

def validate_signal_type(signal_type: str) -> bool:
    """验证信号类型是否在注册表中。"""
    return signal_type in SIGNAL_REGISTRY

# ═══════════════════════════════════════════════════════════════════
# 枚举一致性自检
# ═══════════════════════════════════════════════════════════════════

def check_consistency() -> dict:
    """自检：验证注册表内部一致性。"""
    issues = []
    groups = ["trend_continuation", "reversal", "range", "measurement"]
    expected_count = {
        "trend_continuation": 6,   # H1, H2, L1, L2, BTC, STC
        "reversal": 5,             # wedge, double_bottom, double_top, climax_reversal, final_flag
        "range": 2,                # tr_fade, eighty_twenty
        "measurement": 1,          # measured_move
    }

    for g in groups:
        actual = [st for st, cfg in SIGNAL_REGISTRY.items() if cfg["group"] == g]
        expected = expected_count[g]
        if len(actual) != expected:
            issues.append(f"组 '{g}' 应有 {expected} 种信号，实际 {len(actual)}: {actual}")

    for st, cfg in SIGNAL_REGISTRY.items():
        if "min_rr" not in cfg:
            issues.append(f"'{st}' 缺少 min_rr 字段")
        if "kb_concepts" not in cfg or not cfg["kb_concepts"]:
            issues.append(f"'{st}' 缺少 kb_concepts")
        if "group" not in cfg:
            issues.append(f"'{st}' 缺少 group 字段")
        if "default_direction" not in cfg:
            issues.append(f"'{st}' 缺少 default_direction 字段")

    return {
        "total_signals": len(SIGNAL_REGISTRY),
        "expected_total": 14,
        "groups": {g: [st for st, c in SIGNAL_REGISTRY.items() if c["group"] == g] for g in groups},
        "issues": issues,
        "consistent": len(issues) == 0,
    }


if __name__ == "__main__":
    result = check_consistency()
    print(f"信号注册表自检: {'✅ 一致' if result['consistent'] else '❌ 有问题'}")
    print(f"信号总数: {result['total_signals']}/{result['expected_total']}")
    print(f"\n分组:")
    for g, signals in result['groups'].items():
        print(f"  {g}: {len(signals)} 种 — {signals}")
    if result['issues']:
        print(f"\n问题:")
        for i in result['issues']:
            print(f"  - {i}")
