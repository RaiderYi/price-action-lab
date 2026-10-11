"""
focus_config.py — 聚焦架构 v1 单一事实源 (2026-10-11)

用户拍板：方案A双核四结构 + 区间开关，只做A股30分钟。
依据: data/reviews/FOCUS_V1_ARCHITECTURE_20261011.md
      wiki/sources/article-20200818-brooks-10-best-pa-patterns.md

本模块是"哪些信号允许进入生产"的唯一裁决点。
signal_registry / signal_predictor / 报告层都从这里取 LIVE_SIGNALS。
"""

# ── 市场与时间框架声明 ──────────────────────────────────────────
MARKET = "A股"            # 只做A股；加密货币已砍，指数仅作环境上下文
TIMEFRAME = "30m"         # 唯一信号时间框架

# ── 生产信号面（5结构/6键）────────────────────────────────────
# 延续核: H2/L2（回调入场）+ breakout（精选突破，动能入场）
# 反转核: wedge（三推）+ final_flag（最终旗形），TBTL最小目标统一
# 区间核: tr_fade（仅明确range regime激活）
LIVE_SIGNALS = frozenset({
    "H2", "L2",            # 延续核·回调入场（唯一strict血统）
    "breakout",            # 延续核·动能入场（新增，精选标准）
    "wedge",               # 反转核·三推楔形
    "final_flag",          # 反转核·最终旗形
    "tr_fade",             # 区间核·开关（range regime硬门控）
})

# ── 工具层（不出信号，只供目标价/结构证据）─────────────────────
TOOL_SIGNALS = frozenset({
    "measured_move",       # 测量移动：只算目标位
    "brooks_h1_strict", "brooks_l2_strict",  # strict研究层
    "brooks_h2_strict", "brooks_l1_strict",
})

# ── 降级/研究层（保留registry条目，enabled=False）──────────────
RESEARCH_ONLY = frozenset({
    "H1", "L1",            # 首次回调概率低，不出信号
    "climax_reversal",     # 反转核已由wedge+final_flag承担
    "eighty_twenty",       # CONTEXT_FACTOR
    "double_bottom", "double_top",  # 自迭代#1证伪（-10.4R）
    "buy_the_close", "sell_the_close",
})

# ── Channel 过滤器（75%规律）──────────────────────────────────
CHANNEL_FILTER = {
    "enabled": True,
    # 精选突破标准（等价于只做25%成功突破）：三条件全满足
    "breakout_min_range_atr": 1.2,   # 信号棒区间 ≥ 1.2×ATR（区间扩张）
    "breakout_close_extreme_pct": 0.7,  # 收盘位于信号棒区间上/下70%以外（收在极端）
    "breakout_lookback_bars": 20,    # 前高/前低回看窗口
    # 强趋势逆势禁令：趋势置信度≥0.7时，非wedge/非final_flag的逆势信号拦截
    "strong_trend_confidence": 0.7,
    "strong_trend_allowed_counter": frozenset({"wedge", "final_flag"}),
}

# ── tr_fade 区间质量门控 ──────────────────────────────────────
TR_FADE_GATE = {
    "min_range_width_atr": 2.5,   # 区间宽度 ≥ 2.5×ATR 才算"明确range"
}


def is_live(signal_type: str) -> bool:
    """某信号类型是否允许进入生产信号面。"""
    return signal_type in LIVE_SIGNALS


def strong_trend_allows(signal_type: str, direction_vs_trend: str) -> bool:
    """强趋势过滤：逆势信号只放行wedge/final_flag（75%通道反转规律的同向表达）。"""
    if not CHANNEL_FILTER["enabled"]:
        return True
    if direction_vs_trend != "counter":
        return True
    return signal_type in CHANNEL_FILTER["strong_trend_allowed_counter"]


def tr_fade_range_ok(range_width: float, atr: float) -> bool:
    """tr_fade激活条件：区间宽度达标（明确range regime）。"""
    if atr <= 0:
        return False
    return range_width >= TR_FADE_GATE["min_range_width_atr"] * atr
