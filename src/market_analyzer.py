#!/usr/bin/env python3
"""
价格行为学市场环境分析器
基于 Al Brooks 方法论，从完整K线数据自动判断市场结构

核心逻辑：
- 趋势 (Trend): 存在清晰的 HH/HL (上升) 或 LL/LH (下降) 推进结构
- 区间 (Range): 价格在支撑/阻力之间双向波动，无明确推进
- 过渡 (Transition): 趋势停止推进，出现深度回调或高潮K线
- 突破 (Breakout): 价格带量突破区间/通道边界，并有跟随
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SwingPoint:
    """波段高低点"""
    type: str          # "HH" | "HL" | "LH" | "LL"
    price: float
    date: str
    index: int


@dataclass
class MarketStructure:
    """市场结构分析结果"""
    phase: str                    # "trend" | "range" | "transition" | "breakout"
    direction: str                # "up" | "down" | "neutral"
    confidence: float             # 0-1
    reasoning: str                # 判断依据
    swing_points: List[SwingPoint]
    key_levels: Dict[str, float]  # support, resistance, channel_high, channel_low
    recent_bars_summary: str      # 近5根K线的价格行为描述
    atr: float                    # 平均真实波幅
    bars_above_below_ma: Dict     # 相对MA的位置统计


def find_swing_points(df: pd.DataFrame, window: int = 3) -> List[SwingPoint]:
    """
    识别波段高低点
    
    使用局部极值法：某根K线的高点是前后 window 根K线中的最高点 → 波段高点
    某根K线的低点是前后 window 根K线中的最低点 → 波段低点
    """
    swings = []
    n = len(df)
    
    for i in range(window, n - window):
        # 检查是否是局部高点
        high_slice = df['high'].iloc[i-window:i+window+1]
        if df['high'].iloc[i] == high_slice.max():
            swings.append(SwingPoint(
                type="swing_high",
                price=df['high'].iloc[i],
                date=str(df['date'].iloc[i]),
                index=i
            ))
        
        # 检查是否是局部低点
        low_slice = df['low'].iloc[i-window:i+window+1]
        if df['low'].iloc[i] == low_slice.min():
            swings.append(SwingPoint(
                type="swing_low",
                price=df['low'].iloc[i],
                date=str(df['date'].iloc[i]),
                index=i
            ))
    
    # 按时间排序
    swings.sort(key=lambda x: x.index)
    
    # 将相邻的同类型点合并，只保留极值
    filtered = []
    for s in swings:
        if not filtered:
            filtered.append(s)
            continue
        last = filtered[-1]
        if last.type == s.type:
            # 同类型，保留更极端的
            if s.type == "swing_high":
                if s.price > last.price:
                    filtered[-1] = s
            else:
                if s.price < last.price:
                    filtered[-1] = s
        else:
            filtered.append(s)
    
    return filtered


def classify_swing_sequence(swings: List[SwingPoint]) -> Tuple[str, List[SwingPoint]]:
    """
    将波段高低点序列分类为 HH/HL/LH/LL
    
    例如: High-Low-High-Low → HH/HL/LH/LL 序列
    """
    if len(swings) < 4:
        return "insufficient", swings
    
    # 提取高点和低点
    highs = [s for s in swings if s.type == "swing_high"]
    lows = [s for s in swings if s.type == "swing_low"]
    
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient", swings
    
    # 分类每个点
    classified = []
    
    # 分类高点: HH vs LH
    for i, h in enumerate(highs):
        if i == 0:
            classified.append(SwingPoint("?", h.price, h.date, h.index))
        else:
            prev_high = highs[i-1].price
            if h.price > prev_high:
                classified.append(SwingPoint("HH", h.price, h.date, h.index))
            else:
                classified.append(SwingPoint("LH", h.price, h.date, h.index))
    
    # 分类低点: HL vs LL
    for i, l in enumerate(lows):
        if i == 0:
            classified.append(SwingPoint("?", l.price, l.date, l.index))
        else:
            prev_low = lows[i-1].price
            if l.price > prev_low:
                classified.append(SwingPoint("HL", l.price, l.date, l.index))
            else:
                classified.append(SwingPoint("LL", l.price, l.date, l.index))
    
    classified.sort(key=lambda x: x.index)
    
    # 判断整体结构
    hh_count = sum(1 for s in classified if s.type == "HH")
    hl_count = sum(1 for s in classified if s.type == "HL")
    lh_count = sum(1 for s in classified if s.type == "LH")
    ll_count = sum(1 for s in classified if s.type == "LL")
    
    total_classified = hh_count + hl_count + lh_count + ll_count
    if total_classified == 0:
        return "insufficient", classified
    
    # Brooks 定义:
    # 趋势上升: 多数高点是 HH, 多数低点是 HL
    # 趋势下降: 多数高点是 LH, 多数低点是 LL
    up_score = (hh_count + hl_count) / total_classified
    down_score = (lh_count + ll_count) / total_classified
    
    if up_score > 0.7:
        return "uptrend", classified
    elif down_score > 0.7:
        return "downtrend", classified
    elif up_score > 0.5 or down_score > 0.5:
        return "weak_trend", classified
    else:
        return "range", classified


def is_trading_range(df: pd.DataFrame, swings: List[SwingPoint]) -> Tuple[bool, Dict]:
    """
    判断是否为交易区间
    
    特征:
    - 多次测试相近的高点和低点
    - 价格在近期高低点之间波动
    - 没有明确的 HH/HL 或 LL/LH 推进
    """
    if len(swings) < 4:
        return False, {}
    
    highs = [s.price for s in swings if s.type == "swing_high"]
    lows = [s.price for s in swings if s.type == "swing_low"]
    
    if len(highs) < 2 or len(lows) < 2:
        return False, {}
    
    # 计算阻力区（近期高点的集中度）
    recent_highs = highs[-3:]
    resistance_cluster = max(recent_highs) - min(recent_highs)
    resistance = np.mean(recent_highs)
    
    # 计算支撑区（近期低点的集中度）
    recent_lows = lows[-3:]
    support_cluster = max(recent_lows) - min(recent_lows)
    support = np.mean(recent_lows)
    
    # 区间宽度
    range_width = resistance - support
    current_price = df['close'].iloc[-1]
    
    # 判断标准:
    # 1. 高点集中 (cluster < 1% of price)
    # 2. 低点集中
    # 3. 当前价格在区间内
    price_pct = current_price * 0.01
    
    is_range = (
        resistance_cluster < price_pct * 1.5 and
        support_cluster < price_pct * 1.5 and
        support < current_price < resistance and
        len(highs) >= 2 and len(lows) >= 2
    )
    
    return is_range, {
        "support": support,
        "resistance": resistance,
        "range_width": range_width,
        "touches_high": len(highs),
        "touches_low": len(lows),
    }


def is_breakout(df, range_levels):
    """
    判断是否为突破
    
    特征:
    - 价格突破区间边界（前高/前低）
    - 突破幅度 > 0.5 ATR
    - 突破后有跟随（收盘在突破方向）

    v2: 优先使用 kb_rules breakout_quality 评分，回退到原有逻辑
    """
    # KB rules 优先：使用突破质量评分引擎
    try:
        from kb_rules.breakout_quality import score_breakout_quality
        result = score_breakout_quality(df)
        if result.triggered and result.confidence >= 0.4:
            direction = result.details.get("direction", "up")
            return True, direction
    except ImportError:
        pass
    
    # fallback: 原有逻辑
    if not range_levels:
        return False, ""

    current = df['close'].iloc[-1]
    prev = df['close'].iloc[-2] if len(df) > 1 else current
    atr = calculate_atr(df)

    resistance = range_levels.get("resistance")
    support = range_levels.get("support")

    if not resistance or not support:
        return False, ""

    # 向上突破
    if current > resistance + atr * 0.3:
        # 检查是否有跟随
        if prev > resistance * 0.998:
            return True, "up"

    # 向下突破
    if current < support - atr * 0.3:
        if prev < support * 1.002:
            return True, "down"

    return False, ""


def is_transition(df, trend_type, swings):
    """
    判断是否为过渡期
    
    特征（Brooks 定义）:
    - 趋势停止推进：不再创新高/新低
    - 出现深度回调：回调幅度 > 50% 趋势段
    - 出现高潮K线：超长实体 + 巨量
    - 出现反向强K线：趋势末端的强势反转K线

    v2: 优先使用 kb_rules climax 检测，回退到原有逻辑
    """
    # KB rules 优先：使用高潮检测引擎
    try:
        from kb_rules.climax import detect_climax
        result = detect_climax(df, phase=trend_type)
        if result.triggered and result.confidence >= 0.6:
            return True, f"高潮检测: {result.reasoning}"
    except ImportError:
        pass
    
    # fallback: 原有逻辑
    if len(df) < 10:
        return False, ""

    recent = df.iloc[-10:]

    # 检查趋势是否停止推进
    highs = [s.price for s in swings if s.type == "swing_high"]
    lows = [s.price for s in swings if s.type == "swing_low"]

    trend_stalled = False
    if trend_type == "uptrend" and len(highs) >= 3:
        if highs[-1] <= highs[-2] * 1.002:  # 最后一波没有明显新高
            trend_stalled = True
    elif trend_type == "downtrend" and len(lows) >= 3:
        if lows[-1] >= lows[-2] * 0.998:  # 最后一波没有明显新低
            trend_stalled = True

    # 检查深度回调
    deep_pullback = False
    if len(df) >= 20:
        trend_high = df['high'].iloc[-20:-5].max()
        trend_low = df['low'].iloc[-20:-5].min()
        if trend_type == "uptrend":
            pullback_low = df['low'].iloc[-5:].min()
            fib_50 = trend_high - (trend_high - trend_low) * 0.5
            if pullback_low < fib_50:
                deep_pullback = True
        elif trend_type == "downtrend":
            pullback_high = df['high'].iloc[-5:].max()
            fib_50 = trend_low + (trend_high - trend_low) * 0.5
            if pullback_high > fib_50:
                deep_pullback = True

    # 检查高潮K线（实体特别长 + 成交量放大）
    climax = False
    for i in range(-5, 0):
        if i >= -len(df):
            bar = df.iloc[i]
            body = abs(bar['close'] - bar['open'])
            range_ = bar['high'] - bar['low']
            avg_range = (df['high'].iloc[max(0, i-10):i] - df['low'].iloc[max(0, i-10):i]).mean()
            if range_ > avg_range * 2 and body > range_ * 0.7:
                climax = True
                break

    if trend_stalled or deep_pullback or climax:
        reasons = []
        if trend_stalled: reasons.append("趋势停止推进")
        if deep_pullback: reasons.append("深度回调")
        if climax: reasons.append("高潮K线")
        return True, "、".join(reasons)

    return False, ""


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """计算平均真实波幅"""
    if len(df) < period + 1:
        period = len(df) - 1
    
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean().iloc[-1]
    return atr if not np.isnan(atr) else high_low.mean()


def summarize_recent_bars(df: pd.DataFrame, n: int = 5) -> str:
    """
    用文字描述近 n 根K线的价格行为
    
    例如: "第1根: 大阳线,实体占80%,上影线短,放量"
    """
    if len(df) < n:
        n = len(df)
    
    recent = df.iloc[-n:].copy()
    
    summaries = []
    for idx, (_, bar) in enumerate(recent.iterrows(), 1):
        open_p = bar['open']
        close_p = bar['close']
        high_p = bar['high']
        low_p = bar['low']
        body = abs(close_p - open_p)
        range_ = high_p - low_p
        
        # 实体占比
        body_pct = (body / range_ * 100) if range_ > 0 else 0
        
        # 上下影线
        if close_p >= open_p:  # 阳线
            upper_shadow = high_p - close_p
            lower_shadow = open_p - low_p
        else:  # 阴线
            upper_shadow = high_p - open_p
            lower_shadow = close_p - low_p
        
        # 描述
        desc = []
        
        # 阴阳
        if close_p > open_p * 1.001:
            desc.append("阳线")
        elif close_p < open_p * 0.999:
            desc.append("阴线")
        else:
            desc.append("十字星")
        
        # 实体大小
        if body_pct > 70:
            desc.append("大实体")
        elif body_pct < 30:
            desc.append("小实体")
        
        # 影线
        if upper_shadow > body * 1.5:
            desc.append("长上影")
        if lower_shadow > body * 1.5:
            desc.append("长下影")
        
        # 位置
        if close_p == high_p:
            desc.append("收盘最高")
        elif close_p == low_p:
            desc.append("收盘最低")
        
        summaries.append(f"  [{bar['date']}] O:{open_p:.2f} H:{high_p:.2f} L:{low_p:.2f} C:{close_p:.2f} | {'/'.join(desc)}")
    
    return "\n".join(summaries)


def analyze_market_structure(df: pd.DataFrame) -> MarketStructure:
    """
    主分析函数：从完整K线数据判断市场环境
    
    返回 Brooks PA 定义的市场结构
    """
    if df is None or len(df) < 10:
        return MarketStructure(
            phase="insufficient_data",
            direction="neutral",
            confidence=0.0,
            reasoning="数据不足，无法判断",
            swing_points=[],
            key_levels={},
            recent_bars_summary="",
            atr=0,
            bars_above_below_ma={}
        )
    
    # 1. 识别波段高低点
    swings = find_swing_points(df)
    
    # 2. 分类波段序列
    swing_type, classified_swings = classify_swing_sequence(swings)
    
    # 3. 计算关键价位
    highs = [s.price for s in swings if s.type == "swing_high"]
    lows = [s.price for s in swings if s.type == "swing_low"]
    
    key_levels = {
        "recent_high": max(highs) if highs else df['high'].max(),
        "recent_low": min(lows) if lows else df['low'].min(),
        "prev_high": highs[-2] if len(highs) >= 2 else None,
        "prev_low": lows[-2] if len(lows) >= 2 else None,
    }
    
    # 4. 检查是否是交易区间
    is_range, range_levels = is_trading_range(df, swings)
    if range_levels:
        key_levels.update(range_levels)
    
    # 5. 检查是否是突破
    is_break, breakout_dir = is_breakout(df, range_levels)
    
    # 6. 检查是否是过渡
    is_trans, trans_reason = is_transition(df, swing_type, swings)
    
    # 7. 计算 ATR
    atr = calculate_atr(df)
    key_levels["atr"] = atr

    # 新增：楔形检测（不影响 phase 判定，仅记录）
    try:
        from kb_rules.trend_maturity import evaluate_trend_maturity
        wedge_result = evaluate_trend_maturity(df, direction="up" if swing_type == "uptrend" else "down")
        if wedge_result.triggered:
            key_levels["wedge_detected"] = True
            key_levels["wedge_confidence"] = wedge_result.confidence
            key_levels["wedge_details"] = wedge_result.details
    except ImportError:
        pass

    # 8. 近5根K线摘要
    bar_summary = summarize_recent_bars(df)
    
    # 9. 综合判断市场环境
    current_price = df['close'].iloc[-1]
    
    if is_break:
        phase = "breakout"
        direction = breakout_dir
        confidence = 0.7
        reasoning = f"价格突破{range_levels.get('resistance' if breakout_dir == 'up' else 'support', '关键位'):.2f}，ATR={atr:.2f}"
    
    elif is_trans:
        phase = "transition"
        direction = "up" if swing_type == "downtrend" else "down" if swing_type == "uptrend" else "neutral"
        confidence = 0.55
        reasoning = f"趋势({swing_type})出现过渡迹象：{trans_reason}"
    
    elif is_range:
        phase = "range"
        direction = "neutral"
        # 信心度基于区间清晰度
        range_quality = 1 - (range_levels.get("range_width", 0) / current_price)
        confidence = min(0.8, max(0.4, range_quality))
        reasoning = f"价格在 {range_levels['support']:.2f}-{range_levels['resistance']:.2f} 区间内震荡，多次测试高低点"
    
    elif swing_type in ("uptrend", "downtrend"):
        phase = "trend"
        direction = "up" if swing_type == "uptrend" else "down"
        confidence = 0.75
        hh_count = sum(1 for s in classified_swings if s.type == "HH")
        hl_count = sum(1 for s in classified_swings if s.type == "HL")
        lh_count = sum(1 for s in classified_swings if s.type == "LH")
        ll_count = sum(1 for s in classified_swings if s.type == "LL")
        reasoning = f"清晰的{swing_type}结构：HH={hh_count}, HL={hl_count}, LH={lh_count}, LL={ll_count}"
    
    elif swing_type == "weak_trend":
        phase = "trend"
        direction = "up" if sum(1 for s in classified_swings if s.type in ("HH", "HL")) > sum(1 for s in classified_swings if s.type in ("LH", "LL")) else "down"
        confidence = 0.55
        reasoning = f"弱趋势，推进结构不完整"
    
    else:
        phase = "range"
        direction = "neutral"
        confidence = 0.4
        reasoning = "无明显结构，视为小区间整理"
    
    # 10. MA位置统计
    ma20 = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else df['close'].mean()
    above_ma = sum(df['close'].iloc[-10:] > ma20)
    below_ma = 10 - above_ma
    
    return MarketStructure(
        phase=phase,
        direction=direction,
        confidence=round(confidence, 2),
        reasoning=reasoning,
        swing_points=classified_swings,
        key_levels=key_levels,
        recent_bars_summary=bar_summary,
        atr=round(atr, 2),
        bars_above_below_ma={"above_ma20": above_ma, "below_ma20": below_ma}
    )


def format_klines_for_llm(df: pd.DataFrame, max_bars: int = 20) -> str:
    """
    将K线数据格式化为AI可读的文本表格
    
    输出格式:
    日期        开盘    最高    最低    收盘    涨跌%   成交量      实体描述
    2026-05-01  100.0   102.0   99.0    101.5   +1.5%   1,234,567  阳线/大实体
    """
    if df is None or len(df) == 0:
        return "（无K线数据）"
    
    n = min(max_bars, len(df))
    recent = df.iloc[-n:].copy()
    
    lines = []
    lines.append(f"\n近{n}根K线数据（价格行为分析基础）：")
    lines.append(f"{'日期':<14} {'开盘':>8} {'最高':>8} {'最低':>8} {'收盘':>8} {'涨跌%':>7} {'成交量':>12} {'K线描述'}")
    lines.append("-" * 92)
    
    for _, bar in recent.iterrows():
        date = str(bar['date'])[-14:] if 'date' in bar else "N/A"
        open_p = bar['open']
        high_p = bar['high']
        low_p = bar['low']
        close_p = bar['close']
        pct = bar.get('pctChg', 0)
        vol = bar.get('volume', 0)
        
        body = abs(close_p - open_p)
        range_ = high_p - low_p
        body_pct = (body / range_ * 100) if range_ > 0 else 0
        
        # K线描述
        desc = []
        if close_p > open_p:
            desc.append("阳")
        elif close_p < open_p:
            desc.append("阴")
        else:
            desc.append("十字")
        
        if body_pct > 70:
            desc.append("大实体")
        elif body_pct < 25:
            desc.append("小实体")
        
        if high_p - max(open_p, close_p) > body * 1.2:
            desc.append("长上影")
        if min(open_p, close_p) - low_p > body * 1.2:
            desc.append("长下影")
        
        vol_str = f"{int(vol):,}" if pd.notna(vol) else "N/A"
        pct_str = f"{pct:+.2f}%" if pd.notna(pct) else "N/A"
        
        lines.append(
            f"{date:<14} {open_p:>8.2f} {high_p:>8.2f} {low_p:>8.2f} {close_p:>8.2f} "
            f"{pct_str:>7} {vol_str:>12} {'/'.join(desc)}"
        )
    
    return "\n".join(lines)


def format_market_analysis_for_llm(analysis: MarketStructure, symbol: str) -> str:
    """将市场结构分析结果格式化为LLM可读文本"""
    lines = []
    lines.append(f"\n【{symbol} 市场环境分析】")
    lines.append(f"  阶段: {analysis.phase}")
    lines.append(f"  方向: {analysis.direction}")
    lines.append(f"  信心度: {analysis.confidence}")
    lines.append(f"  判断依据: {analysis.reasoning}")
    lines.append(f"  ATR(14): {analysis.atr}")
    lines.append(f"  近10日位于MA20上方: {analysis.bars_above_below_ma.get('above_ma20')} 根")
    
    if analysis.key_levels:
        lines.append(f"  关键价位:")
        for key, val in analysis.key_levels.items():
            if val is not None and key != "atr":
                if isinstance(val, (int, float)):
                    lines.append(f"    {key}: {val:.2f}")
                elif isinstance(val, bool):
                    lines.append(f"    {key}: {'是' if val else '否'}")
                elif isinstance(val, dict):
                    # 嵌套dict如wedge_details，展平显示
                    flat = ', '.join(f"{k}={v}" for k, v in val.items())
                    lines.append(f"    {key}: {{{flat}}}")
                else:
                    lines.append(f"    {key}: {val}")
    
    if analysis.swing_points:
        lines.append(f"  波段点序列:")
        for sp in analysis.swing_points[-6:]:  # 只展示最近6个
            lines.append(f"    {sp.type}: {sp.price:.2f} ({sp.date})")
    
    if analysis.recent_bars_summary:
        lines.append(f"\n  近5根K线价格行为:")
        for line in analysis.recent_bars_summary.split("\n"):
            lines.append(f"    {line}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    import pandas as pd
    from pathlib import Path
    
    print("=" * 60)
    print("市场环境分析器测试")
    print("=" * 60)
    
    # 读取茅台数据测试
    csv_path = Path(__file__).parent.parent / "data" / "stocks" / "600519_d_2025-05-01_2026-05-20.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        analysis = analyze_market_structure(df)
        
        print(f"\n标的: 600519 贵州茅台")
        print(f"阶段: {analysis.phase}")
        print(f"方向: {analysis.direction}")
        print(f"信心度: {analysis.confidence}")
        print(f"依据: {analysis.reasoning}")
        print(f"\n关键价位: {analysis.key_levels}")
        print(f"\n波段点: {[f'{s.type}:{s.price:.2f}' for s in analysis.swing_points[-4:]]}")
        print(f"\n近5根K线:")
        print(analysis.recent_bars_summary)
        
        print("\n" + "=" * 60)
        print("K线数据格式化测试")
        print("=" * 60)
        print(format_klines_for_llm(df, max_bars=10))
