---
title: "过渡检测系统（Transition Detection System）"
phase: [trend, range, breakout, transition]
signal_types: [wedge, failed-breakout]
tags: [transitioncount, avgolp, phaseistransition, ema, 含义]
difficulty: intermediate
related: [three-push-wedge, phase-context-scoring, fsm-market-cycle, emergency-exit, wedge-gravity-dual-core, article-huangzongprice-wg-brooks-context-v3]
char_count: 3197
---
# 过渡检测系统（Transition Detection System）

## 一句话定义
v3 背景引擎的 5 信号独立检测 + 计数聚合框架——用于判定市场是否从趋势/区间进入过渡状态，是阶段健康分类和过渡判定的核心输入。

## 核心要点
- **5 种独立过渡证据**，每种为一个布尔变量
- **聚合规则**：`transitionCount = 五项之和；phaseIsTransition = transitionCount ≥ 2`
- **最少 2 项才触发**——防止单一假信号误判过渡（如重叠度高但 EMA 仍陡 → 不判定过渡）
- **过渡是双向的**：趋势→过渡 和 区间→过渡 都适用同一框架
- **过渡信号之间存在相关性**（如楔形出现时重叠度通常也高），但独立计数可以捕捉多信号共振

## 五项过渡证据

### 1. transitionByOverlap（重叠度过渡）
```
avgOlp > 0.32
```
- **含义**：5 周期重叠度均值超过 0.32——K 线实体之间大幅重叠，方向性减弱
- **Brooks 对应**：通道走宽、趋势棒变十字星——市场从「趋势」进入「双向」
- **敏感度**：中等。重叠度升高是趋势减弱的最早信号之一

### 2. transitionBySlopeLoss（斜率丧失）
```
not emaSteep or emaFlat
```
- **含义**：EMA20 的 3 周期斜率 < 0.5×ATR20 或 10 周期斜率 < 0.5×ATR20——趋势动能衰减
- **Brooks 对应**：EMA 走平意味着市场失去方向性
- **敏感度**：较高。EMA 斜率对噪音敏感，单根异常 K 线可能导致暂时性丧失

### 3. transitionByBroadChannel（宽通道过渡）
```
phaseState == 1（通道）and avgOlp > 0.24 and phaseConfidence < 0.72
```
- **含义**：在通道阶段中，重叠度升高且置信度下降——通道从「紧通道趋势」退化为「宽通道」
- **Brooks 对应**：通道→交易区间的演变——宽通道是区间的前兆
- **敏感度**：较低。需要同时满足阶段匹配 + 重叠 + 低置信三个条件

### 4. transitionByWedge（楔形过渡）
```
risingWedge or fallingWedge
```
- **含义**：三推楔形形态出现——趋势末段的经典信号
- **Brooks 对应**：楔形 = 趋势衰竭 + 即将反转。上升楔形→空头过渡，下降楔形→多头过渡
- **敏感度**：较低但质量最高。楔形需要多个极点满足时间/空间/收敛条件（见 [[three-push-wedge|Three Push Wedge]]）

### 5. transitionByFailedBreakout（突破失败过渡）
```
brkFail_EMG or emergExit
```
- **含义**：假突破失败（突破 ph0 后收盘跌回）或紧急逃生触发
- **Brooks 对应**：突破失败是反转的最高置信度信号之一
- **敏感度**：时效性最强——一旦出现基本确定过渡

## 五项证据的协变关系

过渡证据并非独立——它们存在自然的因果关系链：

```
EMA 斜率丧失（2）
    ↓
重叠度升高（1）            楔形形态（4）
    ↓                         ↓
宽通道过渡（3）  ←→  趋势成熟度升高
    ↓
突破失败（5）
```

通常的过渡进程：先有斜率丧失和重叠升高（最早信号）→ 然后出现宽通道或楔形（中期信号）→ 最后突破失败（末期确认）。当 3+ 项同时触发时，过渡置信度极高。

## 与阶段健康分类的关系

```
phaseIsTransition = transitionCount ≥ 2

phaseTrendHealthy   = phaseIsTrend & confidence≥0.70 & emaSteep & avgOlp<0.24 & NOT phaseIsTransition
phaseTrendWeakening = phaseIsTrend & transitionCount ≥ 1 & (avgOlp>0.24 | !emaSteep)
phaseTwoSided       = phaseIsRange | phaseIsTransition | avgOlp > 0.35
```

- **TrendHealthy** 隐式要求 transitionCount = 0（所有四项条件都满足才能拿到最低重叠、最陡 EMA）
- **TrendWeakening** 只需 1 项过渡证据（比 phaseIsTransition 的 ≥2 更宽松）
- **TwoSided** 等价于「任何过渡信号 + 任何区间信号 + 任何高重叠信号」的并集

## 在信息面板中的展示

V3 右上角信息面板第 13 行显示 `transitionCount + " 项"`——背景色在 count ≥ 2 时变为橙色警示。

## 与相关概念的关系
- [[phase-context-scoring]]：transitionCount → phaseIsTransition → 阶段健康分类 → phaseScoreL/S 的完整链路
- [[fsm-market-cycle]]：FSM 输出的 phaseState/avgOlp/emaSteep/emaFlat 是 3 项过渡证据的直接输入
- [[three-push-wedge|Three Push Wedge]]：risingWedge/fallingWedge 是第 4 项过渡证据
- [[emergency-exit]]：brkFail_EMG/emergExit 是第 5 项过渡证据
- [[wedge-gravity-dual-core]]：过渡检测系统是三层引擎中「阶段层」连接「FSM 传感器」和「背景裁决」的关键管道

## 实战应用
- **transitionCount = 0** 且 phaseIsTrend → 趋势健康——顺势入场最可靠
- **transitionCount = 1** → 趋势减弱——顺势仍可做，但降低仓位或收紧止损
- **transitionCount ≥ 2** → phaseIsTransition 为真——进入「等待观察」模式，两可环境下逆势信号可能比顺势更可靠
- **transitionCount ≥ 3** 且 emergExit → 大概率市场即将反转——考虑反向入场或退出所有持仓

## 来源支撑
- [[article-huangzongprice-wg-brooks-context-v3]]（V3.0 源码——首次公开完整 5 证据过渡检测框架）

## 矛盾与待验证
- 阈值 `avgOlp > 0.32` 和 `avgOlp > 0.24` 的区别使用：前一个是独立过渡证据，后一个仅在通道阶段中有效——两个阈值的最优值是否应通过回测确定？
- 五项证据的权重相等（各计 1 分）——但突破失败（5）和重叠度（1）的信息量显然不同。加权计数（如 5 号证据计 2 分）是否更合理？
- `transitionCount` 在 30 行面板中仅显示数量，不显示具体是哪些证据触发——诊断价值有限。
