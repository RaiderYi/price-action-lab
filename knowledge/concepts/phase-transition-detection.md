---
title: "阶段过渡检测（Phase Transition Detection）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, wedge, pullback-entry, failed-breakout]
tags: [ema, 通道, avgolp, fsm, 假突破]
difficulty: intermediate
related: [three-push-wedge, emergency-exit, fsm-market-cycle, background-scoring-engine, momentum-health, channel-to-trading-range, article-20260520-wedge-gravity-brooks-context-v3]
char_count: 3653
---
# 阶段过渡检测（Phase Transition Detection）

## 一句话定义
WG Brooks V3 中判断市场是否从「趋势/区间」向「过渡态」演变的五项证据系统——重叠度增加、EMA 斜率丧失、宽通道出现、楔形形成、假突破——任何 2 项触发即宣告 phaseIsTransition=true。

## 核心要点

### 五项过渡证据

| # | 证据变量 | 触发条件 | 含义 |
|---|---------|---------|------|
| 1 | `transitionByOverlap` | avgOlp > 0.32 | K 线重叠度均值超过 32%——多空争夺加剧 |
| 2 | `transitionBySlopeLoss` | NOT emaSteep OR emaFlat | EMA 斜率丧失或已走平——趋势动能衰减 |
| 3 | `transitionByBroadChannel` | phaseState==1（通道）且 avgOlp>0.24 且 phaseConfidence<0.72 | 宽通道中重叠度偏高+置信度下降 |
| 4 | `transitionByWedge` | risingWedge OR fallingWedge | 三推楔形出现——趋势末端结构 |
| 5 | `transitionByFailedBreakout` | brkFail_EMG OR emergExit | 假突破或紧急逃生触发——突破失败信号 |

### 过渡判定逻辑

```
transitionCount = Σ(证据 1~5 触发 ? 1 : 0)

phaseIsTransition = transitionCount ≥ 2                    // 核心规则：≥2 项
  OR (phaseState==1 AND avgOlp > 0.30)                     // 通道+高重叠=天然过渡
  OR (phaseState==3 AND transitionByFailedBreakout)        // 新突破+假突破=过渡
```

### 过渡态对阶段分的影响

过渡态不直接否决交易，但改变阶段评分：

**做多方面**：
- `phaseTwoSided = phaseIsRange OR phaseIsTransition OR avgOlp > 0.35` → 双边势标记
- `phaseTwoSided AND NOT nearBullSupport` → **-0.14 扣分**
- `phaseTrendHealthy` （趋势健康时）不受过渡影响——健康趋势中的过渡信号只是"值得警惕"但不足以降级

**做空方面**：镜像逻辑

### 过渡证据与 FSM 状态的互动

```
    ┌───────────┐     过渡证据累积      ┌────────────┐
    │  TREND    │ ──────────────────→  │ TRANSITION │
    │ (0/1/3)   │                      │ (临时判定)  │
    └───────────┘                      └──────┬─────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                        进入 RANGE      趋势恢复健康     趋势继续但双面化
                        (ch2rng触发)   (过渡消散)      (phaseTwoSided)
```

- 过渡态是**临时判定**，每根 K 线重新计算
- FSM 状态转换（如 ch2rng：通道→区间）是**事件驱动**，独立于过渡检测
- 过渡态可以发生在趋势中而不触发 FSM 状态切换——它是"环境颜色"而非"状态机事件"

### 五项证据的技术定义

#### 1. 重叠度增加（transitionByOverlap）
- `avgOlp`：最近 5 根 K 线重叠比例的均值
- `olpRaw = max(0, min(close[1], close) - max(open[1], open))`：当前与前一根的实体重叠量
- `olpRt = barBody>0 ? olpRaw/barBody : 0`：重叠比例（0=无重叠, 1=完全重叠/内包）
- 阈值 0.32：最近 5 根平均有 32% 以上的实体互相重叠 → 方向性减弱

#### 2. EMA 斜率丧失（transitionBySlopeLoss）
- `emaS3 = ema20 - ema20[3]`：3 根 K 线的 EMA 位移
- `emaSteep = |emaS3| > 0.5 × atr20v`：EMA 在陡峭移动
- `emaFlat = |emaS10| < 0.5 × atr20v`：10 根 K 线内 EMA 基本未移动
- 触发条件：不陡峭 OR 已走平

#### 3. 宽通道（transitionByBroadChannel）
- 仅在 FSM 状态=通道（phaseState==1）时评估
- 通道+偏高重叠（>0.24）+ 低置信度（<0.72）→ 宽通道=趋势尾声
- 窄通道（重叠度低+置信度高）不触发

#### 4. 楔形（transitionByWedge）
- risingWedge：连续三个 HH+HL 的上升楔形（多头动能衰减）
- fallingWedge：连续三个 LL+LH 的下降楔形（空头动能衰减）
- 详见 [[three-push-wedge|Three Push Wedge]]

#### 5. 假突破（transitionByFailedBreakout）
- `brkFail_EMG`：最近 3 根曾有 K 线突破 ph0 但收盘回落至 ph0 之下
- `emergExit`：假突破 OR 双根重叠衰竭 OR 竭尽K线
- 详见 [[emergency-exit]]

## 与相关概念的关系
- [[fsm-market-cycle]]：FSM 决定基础状态（趋势/通道/区间/新突破），过渡检测在此之上叠加"过渡颜色"
- [[background-scoring-engine]]：过渡检测的结果直接影响 phaseScore（双边势-0.14、逆势-0.26）
- [[momentum-health]]：过渡信号出现时，趋势健康度（trendHealth）通常会降低、当前腿转弱（legWeakening）升高
- [[three-push-wedge|Three Push Wedge]] / [[emergency-exit]]：分别是过渡证据 #4 和 #5 的详细实现
- [[channel-to-trading-range]]：宽通道过渡检测（#3）的 Brooks 理论基础

## 实战应用
- 信息面板「过渡证据」行：`transitionCount ≥ 2` 时橙色高亮 → 这是最直观的过渡警告
- 过渡 ≠ 反转：过渡态只是"原有趋势的健康度下降"——可能转区间、可能恢复趋势、可能反转
- 过渡态中做顺势交易的执行分会被压低（phaseScore 降低 → bgScore 降低 → lFin/sFin 降低）

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 完整 Pine Script 源码，第 626-667 行）

## 矛盾与待验证
- 五项证据等权计数（每项 1 分，≥2 触发）——但证据的重要性显然不同：楔形/假突破比重叠度增加更具决定性。等权设计可能过于简化
- `transitionBySlopeLoss` 使用 `NOT emaSteep OR emaFlat`——`NOT emaSteep` 意味着"EMA 不再加速"即可触发，这在趋势正常减速时（如回调期）也会触发，可能过于敏感
- 过渡检测结果未持久化（每根 K 线独立计算），可能在趋势恢复时立即消失——false positive 率高
