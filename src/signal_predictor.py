#!/usr/bin/env python3
"""
Brooks PA 严格信号预判引擎

基于K线形态和市场环境，预判每只标的当前最可能出现的2-3种信号类型。
严格遵守Al Brooks价格行为学的判断逻辑，不做猜测。

核心原则:
1. 先市场环境 → 再信号形态（Context first）
2. 必须有K线结构支撑（Structure-based）
3. 不做"可能"/"也许"的判断，只做"符合/不符合"
4. 过渡期的标的一般不给出具体信号，只给出观察条件
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

from market_analyzer import MarketStructure


@dataclass
class SignalPrediction:
    """信号预判结果"""
    signal_type: str        # 信号类型（白名单内）
    direction: str          # 方向: buy(做多)/sell(做空)
    confidence: float       # 预判信心度 0-1
    reason: str             # 预判理由（基于K线结构）
    trigger_price: float    # 触发价格
    trigger_condition: str  # 触发条件（K线形态）


def _is_three_push_wedge(df: pd.DataFrame, direction: str) -> Tuple[bool, str]:
    """
    检查是否有三推楔形结构
    
    Brooks定义:
    - 上升趋势中的三推楔形：三次向上推动，每次高点抬高但幅度递减，K线实体变小
    - 下降趋势中的三推楔形：三次向下推动，每次低点降低但幅度递减
    """
    if len(df) < 10:
        return False, ""
    
    recent = df.iloc[-10:].copy()
    
    # 计算每根K线的实体和方向
    recent['body'] = (recent['close'] - recent['open']).abs()
    recent['direction'] = np.where(recent['close'] > recent['open'], 1, -1)
    
    if direction == "up":
        # 上升趋势中寻找三推楔形（向下楔形 = 牛市旗形后反转）
        # 简化：找三次向上的高点，幅度递减
        highs = recent['high'].values
        # 找局部高点
        push_highs = []
        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                push_highs.append((i, highs[i]))
        
        if len(push_highs) >= 3:
            # 检查幅度递减
            amplitudes = []
            for i in range(1, len(push_highs)):
                amp = push_highs[i][1] - push_highs[i-1][1]
                amplitudes.append(amp)
            
            if len(amplitudes) >= 2 and amplitudes[-1] < amplitudes[0] * 0.7:
                return True, f"三推楔形: 三次高点 {push_highs[-3][1]:.2f}→{push_highs[-2][1]:.2f}→{push_highs[-1][1]:.2f}, 幅度递减"
    
    elif direction == "down":
        # 下降趋势中寻找三推楔形（向上楔形 = 熊市旗形后反转）
        lows = recent['low'].values
        push_lows = []
        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                push_lows.append((i, lows[i]))
        
        if len(push_lows) >= 3:
            amplitudes = []
            for i in range(1, len(push_lows)):
                amp = push_lows[i-1][1] - push_lows[i][1]
                amplitudes.append(amp)
            
            if len(amplitudes) >= 2 and amplitudes[-1] < amplitudes[0] * 0.7:
                return True, f"三推楔形: 三次低点 {push_lows[-3][1]:.2f}→{push_lows[-2][1]:.2f}→{push_lows[-1][1]:.2f}, 幅度递减"
    
    return False, ""


def _is_double_bottom_top(df: pd.DataFrame, key_levels: Dict) -> Tuple[bool, str, str]:
    """
    检查是否有双底或双顶结构
    
    Brooks定义:
    - 双底: 两次测试相近的低点，第二次出现反转K线（长下影/阳线收盘高位）
    - 双顶: 两次测试相近的高点，第二次出现反转K线（长上影/阴线收盘低位）
    """
    if len(df) < 8:
        return False, "", ""
    
    recent = df.iloc[-8:].copy()
    lows = recent['low'].values
    highs = recent['high'].values
    
    # 找两个相近的低点
    for i in range(len(lows) - 3):
        for j in range(i + 3, len(lows)):
            if abs(lows[i] - lows[j]) / lows[i] < 0.015:  # 1.5%范围内
                # 检查第二次是否有反转迹象
                bar_j = recent.iloc[j]
                body = abs(bar_j['close'] - bar_j['open'])
                range_ = bar_j['high'] - bar_j['low']
                lower_shadow = bar_j['close'] - bar_j['low'] if bar_j['close'] > bar_j['open'] else bar_j['open'] - bar_j['low']
                
                if lower_shadow > body * 0.8 and bar_j['close'] > bar_j['open']:
                    return True, "double_bottom", f"双底: 两次测试低点 {lows[i]:.2f} 和 {lows[j]:.2f}, 第二次出现长下影阳线"
    
    # 找两个相近的高点
    for i in range(len(highs) - 3):
        for j in range(i + 3, len(highs)):
            if abs(highs[i] - highs[j]) / highs[i] < 0.015:
                bar_j = recent.iloc[j]
                body = abs(bar_j['close'] - bar_j['open'])
                upper_shadow = bar_j['high'] - bar_j['close'] if bar_j['close'] > bar_j['open'] else bar_j['high'] - bar_j['open']
                
                if upper_shadow > body * 0.8 and bar_j['close'] < bar_j['open']:
                    return True, "double_top", f"双顶: 两次测试高点 {highs[i]:.2f} 和 {highs[j]:.2f}, 第二次出现长上影阴线"
    
    return False, "", ""


def _is_climax_reversal(df: pd.DataFrame, direction: str) -> Tuple[bool, str]:
    """
    检查是否有高潮后反转结构
    
    Brooks定义:
    - 一根超大实体K线（通常是趋势末端）
    - 紧随其后的反向K线（收盘价突破前一根K线中点）
    """
    if len(df) < 5:
        return False, ""
    
    recent = df.iloc[-5:].copy()
    avg_range = (recent['high'] - recent['low']).mean()
    
    for i in range(len(recent) - 1):
        bar1 = recent.iloc[i]
        bar2 = recent.iloc[i + 1]
        
        range1 = bar1['high'] - bar1['low']
        body1 = abs(bar1['close'] - bar1['open'])
        body2 = abs(bar2['close'] - bar2['open'])
        
        # 第一根是超大实体K线
        if range1 > avg_range * 2 and body1 > range1 * 0.7:
            midpoint1 = (bar1['open'] + bar1['close']) / 2
            
            if direction == "up":
                # 上升趋势末端的高潮后反转：大阳线后紧跟阴线收盘低于中点
                if bar1['close'] > bar1['open'] and bar2['close'] < midpoint1:
                    return True, f"高潮后反转: {bar1['date']}超大阳线后,{bar2['date']}阴线收盘低于中点"
            else:
                # 下降趋势末端的高潮后反转：大阴线后紧跟阳线收盘高于中点
                if bar1['close'] < bar1['open'] and bar2['close'] > midpoint1:
                    return True, f"高潮后反转: {bar1['date']}超大阴线后,{bar2['date']}阳线收盘高于中点"
    
    return False, ""


def _is_final_flag(df: pd.DataFrame, direction: str, swing_points: List) -> Tuple[bool, str]:
    """
    检查是否有最终旗形结构
    
    Brooks定义:
    - 趋势末端出现的紧凑小K线区间（3-5根小实体K线）
    - 然后向趋势方向突破
    """
    if len(df) < 8:
        return False, ""
    
    recent = df.iloc[-8:].copy()
    recent['body'] = (recent['close'] - recent['open']).abs()
    recent['range'] = recent['high'] - recent['low']
    recent['body_pct'] = recent['body'] / recent['range']
    
    # 找连续3-5根小实体K线
    small_bars = recent['body_pct'] < 0.4
    
    for i in range(len(recent) - 2):
        if small_bars.iloc[i] and small_bars.iloc[i+1] and small_bars.iloc[i+2]:
            # 检查这几根K线是否紧凑（高点相近、低点相近）
            flag_highs = recent['high'].iloc[i:i+3]
            flag_lows = recent['low'].iloc[i:i+3]
            
            if (flag_highs.max() - flag_highs.min()) / flag_highs.mean() < 0.01:
                if (flag_lows.max() - flag_lows.min()) / flag_lows.mean() < 0.01:
                    # 检查最后一根是否突破
                    last_bar = recent.iloc[-1]
                    if direction == "up" and last_bar['close'] > flag_highs.max():
                        return True, f"最终旗形: 趋势末端3根小实体紧凑K线后向上突破"
                    elif direction == "down" and last_bar['close'] < flag_lows.min():
                        return True, f"最终旗形: 趋势末端3根小实体紧凑K线后向下突破"
    
    return False, ""


def _check_h2_l2_setup(df: pd.DataFrame, swing_points: List, direction: str) -> Tuple[bool, str, str]:
    """
    检查是否有H2或L2结构
    
    Brooks定义:
    - H2: 上升趋势中，回调形成H1（ Higher Low 1），然后再次回调形成H2（ Higher Low 2），随后突破前高
    - L2: 下降趋势中，反弹形成L1（ Lower High 1），然后再次反弹形成L2（ Lower High 2），随后跌破前低
    
    【自迭代 #8】L2做空增加多级确认：需连续2+个LH + 均线向下
    """
    if not swing_points or len(swing_points) < 3:
        return False, "", ""
    
    # 提取最近的高低点类型
    recent_types = [sp.type for sp in swing_points[-6:]]  # 扩展至6个
    recent_prices = [sp.price for sp in swing_points[-6:]]
    
    if direction == "up":
        # 寻找H2: 需要 HL -> (回调) -> HL 或 HH -> (回调) -> H2 setup
        if "HL" in recent_types:
            hl_idx = recent_types.index("HL")
            hl_price = recent_prices[hl_idx]
            current = df['close'].iloc[-1]
            if current > hl_price * 1.01:
                return True, "H2", f"H2结构: 最近HL在{hl_price:.2f}, 当前价格{current:.2f}已反弹"
    
    elif direction == "down":
        # 【自迭代 #8】L2做空多级确认
        # 条件1: 至少2个连续LH（确认空头趋势）
        lh_count = sum(1 for t in recent_types if t == "LH")
        if lh_count < 2:
            return False, "", ""
        
        # 条件2: 均线方向向下（5日 < 20日）
        if 'close' in df.columns and len(df) >= 20:
            ma5 = df['close'].iloc[-5:].mean()
            ma20 = df['close'].iloc[-20:].mean()
            if ma5 > ma20:
                return False, "", ""  # 均线未向下，拒绝L2
        
        # 条件3: 最近LH价格递减（H2 < H1）
        lh_indices = [i for i, t in enumerate(recent_types) if t == "LH"]
        if len(lh_indices) >= 2:
            h1_price = recent_prices[lh_indices[0]]  # 较早的LH
            h2_price = recent_prices[lh_indices[-1]]  # 最近的LH
            if h2_price >= h1_price:
                return False, "", ""  # H2 >= H1，非严格LH递减
        
        # 条件4: 当前价格已跌破最近的LH
        lh_idx = lh_indices[-1]
        lh_price = recent_prices[lh_idx]
        current = df['close'].iloc[-1]
        if current < lh_price * 0.99:
            return True, "L2", f"L2结构: 连续{lh_count}个LH确认空头趋势, 最近LH在{lh_price:.2f}, 当前价格{current:.2f}已回落"
    
    return False, "", ""


def _is_breakout_entry(df: pd.DataFrame, direction: str, atr: float) -> Tuple[bool, str, str]:
    """
    Focus v1 精选突破检测（10大形态#3 + Channel 75%过滤）。

    三条件全满足（Brooks精选标准——只做那25%的优质突破）:
      1. 收盘突破 lookback(20) 前高/前低
      2. 收盘位于信号棒区间上/下 30% 极端（收在极端，不能是长上影的弱突破）
      3. 信号棒区间 ≥ 1.2×ATR（区间扩张，大棒定律）

    Returns: (is_breakout, signal_direction('buy'/'sell'), reason)
    """
    import focus_config
    cfg = focus_config.CHANNEL_FILTER
    n = len(df)
    lookback = cfg["breakout_lookback_bars"]
    if atr <= 0 or n < lookback + 2:
        return False, "", ""

    last = df.iloc[-1]
    last_close = float(last['close'])
    last_high = float(last['high'])
    last_low = float(last['low'])
    bar_range = last_high - last_low

    # condition 3: range expansion
    if bar_range < cfg["breakout_min_range_atr"] * atr:
        return False, "", ""

    prior = df.iloc[-(lookback + 1):-1]
    prior_high = float(prior['high'].max())
    prior_low = float(prior['low'].min())

    extreme_pct = cfg["breakout_close_extreme_pct"]

    # upside: close breaks prior high AND close in top 30% of bar
    # [S0-05/F03 修正] 顶部30%极端收盘：pos_in_bar >= extreme_pct(0.7)。
    # 旧代码误写为 >= (1-extreme_pct)=0.3，导致收于40%的弱多头棒也被放行。
    if last_close > prior_high:
        pos_in_bar = (last_close - last_low) / bar_range if bar_range > 0 else 0.5
        if pos_in_bar >= extreme_pct:
            return True, "buy", (
                f"精选突破: 收盘{last_close:.2f}突破{lookback}棒前高{prior_high:.2f}, "
                f"收于棒体上部{pos_in_bar:.0%}(极端, 需>={extreme_pct:.0%}), 棒区间{bar_range:.2f}≥{cfg['breakout_min_range_atr']}×ATR"
            )
        return False, "", ""

    # downside: close breaks prior low AND close in bottom 30%
    # [S0-05/F03 修正] 底部30%极端收盘：pos_in_bar <= 1-extreme_pct(0.3)。
    if last_close < prior_low:
        pos_in_bar = (last_close - last_low) / bar_range if bar_range > 0 else 0.5
        if pos_in_bar <= (1 - extreme_pct):
            return True, "sell", (
                f"精选突破: 收盘{last_close:.2f}跌破{lookback}棒前低{prior_low:.2f}, "
                f"收于棒体下部{pos_in_bar:.0%}(极端), 棒区间{bar_range:.2f}≥{cfg['breakout_min_range_atr']}×ATR"
            )
    return False, "", ""


def predict_signals(
    df: pd.DataFrame,
    analysis: MarketStructure,
) -> List[SignalPrediction]:
    """
    Focus v1 (2026-10-11): 双核四结构 + 区间开关, A股30m专用。

    延续核: H2/L2(回调) + breakout(精选突破)
    反转核: wedge(三推) + final_flag(最终旗形)
    区间核: tr_fade(仅明确range regime+宽度≥2.5ATR)

    H1/L1/climax/measured_move/fallback 已按 FOCUS_V1_ARCHITECTURE 移除。
    """
    import focus_config

    predictions = []
    phase = analysis.phase
    direction = analysis.direction
    key_levels = analysis.key_levels
    swing_points = analysis.swing_points
    atr = getattr(analysis, 'atr', 0.0) or 0.0

    # ========== 候选池: focus_config 驱动 ==========
    if direction == "up":
        trade_ready_candidates = ["H2"]
    elif direction == "down":
        trade_ready_candidates = ["L2"]
    else:
        trade_ready_candidates = ["H2", "L2"]

    # 反转核: wedge 任何环境候选(检测在K线里), final_flag 仅 transition/趋势末端环境
    if phase in ("transition", "trend"):
        research_candidates = ["final_flag"]
    else:
        research_candidates = []
    if phase == "range":
        research_candidates.append("tr_fade")

    candidate_signals = trade_ready_candidates + research_candidates + ["wedge", "breakout"]

    # ========== 检测 ==========
    is_wedge, wedge_reason = _is_three_push_wedge(df, direction)
    is_flag, flag_reason = _is_final_flag(df, direction, swing_points)
    is_h2l2, h2l2_type, h2l2_reason = _check_h2_l2_setup(df, swing_points, direction)
    is_breakout, breakout_dir, breakout_reason = _is_breakout_entry(df, direction, atr)

    # ========== 生成: 延续核 ==========
    # H2/L2（趋势延续·回调入场）
    if is_h2l2 and h2l2_type in candidate_signals:
        trigger = key_levels.get("recent_low" if direction == "up" else "recent_high", 0)
        sig_dir = "buy" if "H" in h2l2_type else "sell"
        predictions.append(SignalPrediction(
            signal_type=h2l2_type,
            direction=sig_dir,
            confidence=0.65,
            reason=h2l2_reason,
            trigger_price=trigger,
            trigger_condition=f"突破{h2l2_type}确认点"
        ))

    # breakout（精选突破·动能入场）
    if is_breakout:
        predictions.append(SignalPrediction(
            signal_type="breakout",
            direction=breakout_dir,
            confidence=0.6,
            reason=breakout_reason,
            trigger_price=float(df['close'].iloc[-1]),
            trigger_condition="突破棒收盘成立; 回测突破位不破可加仓"
        ))

    # ========== 生成: 反转核 ==========
    # 楔形三推（40%胜率换≥2:1盈亏比, TBTL最小目标）
    if is_wedge and "wedge" in candidate_signals:
        current = df['close'].iloc[-1]
        wedge_dir = "buy" if direction == "down" else "sell"
        predictions.append(SignalPrediction(
            signal_type="wedge",
            direction=wedge_dir,
            confidence=0.6,
            reason=wedge_reason,
            trigger_price=current,
            trigger_condition="等待楔形边界突破确认; 最小目标=TBTL(10棒2腿,RR≥2)"
        ))

    # 最终旗形（趋势末端延续失败→反转, 40%胜率换≥2:1）
    if is_flag and "final_flag" in candidate_signals:
        current = df['close'].iloc[-1]
        flag_dir = "buy" if direction == "up" else "sell"
        predictions.append(SignalPrediction(
            signal_type="final_flag",
            direction=flag_dir,
            confidence=0.55,
            reason=flag_reason,
            trigger_price=current,
            trigger_condition="突破旗形边界; 最小目标=TBTL(10棒2腿,RR≥2)"
        ))

    # ========== 生成: 区间核(开关) ==========
    # tr_fade — 双重门控: phase==range AND 区间宽度≥2.5×ATR(明确range regime)
    if phase == "range" and "tr_fade" in candidate_signals:
        support = key_levels.get("support", 0)
        resistance = key_levels.get("resistance", 0)
        current = df['close'].iloc[-1]
        range_width = (resistance - support) if (support > 0 and resistance > support) else 0.0

        if focus_config.tr_fade_range_ok(range_width, atr):
            if current < support * 1.02:
                predictions.append(SignalPrediction(
                    signal_type="tr_fade",
                    direction="buy",
                    confidence=0.65,
                    reason=f"价格接近区间下沿{support:.2f}(区间宽度{range_width:.2f}≥2.5×ATR), 可能反弹",
                    trigger_price=support,
                    trigger_condition="在区间下沿出现反转K线"
                ))
            elif current > resistance * 0.98:
                predictions.append(SignalPrediction(
                    signal_type="tr_fade",
                    direction="sell",
                    confidence=0.65,
                    reason=f"价格接近区间上沿{resistance:.2f}(区间宽度{range_width:.2f}≥2.5×ATR), 可能回落",
                    trigger_price=resistance,
                    trigger_condition="在区间上沿出现反转K线"
                ))

    # ========== Channel 75%过滤: 强趋势逆势禁令 ==========
    if (focus_config.CHANNEL_FILTER["enabled"]
            and getattr(analysis, 'confidence', 0) >= focus_config.CHANNEL_FILTER["strong_trend_confidence"]
            and direction in ("up", "down")):
        filtered = []
        for p in predictions:
            counter = (direction == "up" and p.direction == "sell") or \
                      (direction == "down" and p.direction == "buy")
            if counter and not focus_config.strong_trend_allows(p.signal_type, "counter"):
                continue
            filtered.append(p)
        predictions = filtered

    # Focus v1: 无形态 = 无信号 = 观望。不再生成fallback提示信号。

    predictions.sort(key=lambda x: x.confidence, reverse=True)
    return predictions[:3]


def predict_signals_for_all(
    analyses: Dict[str, MarketStructure],
    dataframes: Dict[str, pd.DataFrame],
) -> Dict[str, List[SignalPrediction]]:
    """
    批量预判所有标的的信号
    
    返回: {symbol: [SignalPrediction, ...]}
    """
    results = {}
    for symbol, analysis in analyses.items():
        df = dataframes.get(symbol)
        if df is not None and len(df) > 0:
            results[symbol] = predict_signals(df, analysis)
        else:
            results[symbol] = []
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Brooks PA 信号预判引擎测试")
    print("=" * 60)
    
    import pandas as pd
    from pathlib import Path
    from market_analyzer import analyze_market_structure
    
    # 测试茅台
    csv_path = Path(__file__).parent.parent / "data" / "stocks" / "600519_d_2025-05-01_2026-05-20.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        analysis = analyze_market_structure(df)
        preds = predict_signals(df, analysis)
        
        print(f"\n标的: 600519 贵州茅台")
        print(f"市场环境: {analysis.phase} | {analysis.direction}")
        print(f"预判信号 ({len(preds)} 个):")
        for p in preds:
            print(f"  - {p.signal_type}: 信心度{p.confidence}, 触发价{p.trigger_price:.2f}")
            print(f"    理由: {p.reason}")
            print(f"    条件: {p.trigger_condition}")
