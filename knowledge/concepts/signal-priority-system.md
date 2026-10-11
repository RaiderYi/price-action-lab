---
title: "信号优先级体系（Signal Priority System）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, failed-breakout]
tags: [level, 紧急逃生, fsm, 硬规则事, bgscore]
difficulty: intermediate
related: [fsm-market-cycle, emergency-exit, three-push-wedge, h2-l2-state-machine, background-scoring-engine, signal-scoring-synthesis, wedge-gravity-dual-core, dynamic-risk-control, article-20260519-wedge-gravity-v41-flowchart]
char_count: 1894
---
# 信号优先级体系（Signal Priority System）

## 一句话定义
WG Brooks 引擎中 5 级信号优先级层级——从硬规则事件到最终入场信号，每级有明确的触发条件和裁决权限，确保信号冲突时有确定的处理规则。

## 核心要点

### 五级优先级（从高到低）

| 级别 | 名称 | 权限 | 触发条件 |
|------|------|------|---------|
| **Level 1** | 硬规则事件 | **最高优先级，立即执行**，不受其他条件限制 | 周期状态切换（FSM 四状态转换） |
| **Level 2** | 紧急逃生预警 | 提示风险，但不阻止其他信号 | 假突破 / 双根高重叠 / 竭尽K线 |
| **Level 3** | 结构识别 | 提供潜在交易机会，需要背景确认 | 三推楔形(上升/下降) + Brooks H2/L2计数完成 |
| **Level 4** | 背景决策 | 否决 → 绝对禁止交易；支持 → 允许结构信号 | 三层评分(Location+Phase+Momentum) → bgScore vs bgThr |
| **Level 5** | 信号生成 | 最终入场信号 | 结构信号✓ + 信号棒评分≥阈值 + K线位置✓ + 背景支持✓ |

### 裁决逻辑
- Level 1 的 FSM 状态切换事件发生时，所有下游信号立即重新评估
- Level 2（紧急逃生）触发时不会阻断信号，但作为风险提示与 Level 4 的否决条件联动
- Level 3 的结构信号需要 Level 4 的背景许可才能进入 Level 5
- Level 4 的背景否决是绝对禁止——任何结构信号在背景否决条件下即使 Level 3 为真也无法进入 Level 5
- Level 5 需 Level 3 AND Level 4 同时满足，任一不满足则无信号

### 背景否决条件（Level 4 中的绝对禁止项）
1. 中部位置 AND 震荡区间
2. 健康趋势与策略方向相反（且无楔形/H2 支撑）
3. 晚突破位置 + 晚突破方向
4. 高成熟度/高衰竭风险 + 当前腿转弱 + 晚突破

### 信号冲突处理
- 多/空信号同时满足时：比较执行分（bgScore×0.55 + structScore×0.25 + sigScore×0.20），取高分方向
- 多/空执行分相差 < 0.02 时：背景冲突 → 均不出信号

## 与相关概念的关系
- [[fsm-market-cycle]]：Level 1 硬规则事件即 FSM 四状态转换
- [[emergency-exit]]：Level 2 紧急逃生预警的三种触发条件
- [[three-push-wedge|Three Push Wedge]] + [[h2-l2-state-machine|H2/L2 State Machine]]：Level 3 结构信号的两个来源
- [[background-scoring-engine]]：Level 4 背景决策的三层评分引擎
- [[signal-scoring-synthesis]]：Level 5 信号生成中信号棒评分的来源
- [[wedge-gravity-dual-core]]：整个优先级体系是双核架构的执行层调度规则
- [[dynamic-risk-control]]：Level 5 信号确认后立即触发 SL/ENT/TP 计算

## 实战应用
调试"为什么没有信号"时，按优先级从高到低排查：
1. FSM 状态是否允许该方向？(Level 1)
2. 紧急逃生是否触发（非阻断，但提示风险）？(Level 2)
3. 是否有结构信号（楔形/H2/L2）？(Level 3)
4. 背景是否支持（bgScore≥0.58 且无否决）？(Level 4)
5. 信号棒分数是否达标（≥0.40）+ 收盘位置是否正确？(Level 5)

## 来源支撑
- [[article-20260519-wedge-gravity-v41-flowchart]]

## 矛盾与待验证
- 「硬规则事件立即执行」的具体执行方式（是否强制平掉反向持仓？是否触发新的入场？）文档未详细说明
- 多/空冲突时执行分对比的阈值 0.02（`i_confThr=0.18`）与信号评分合成中的阈值含义不同——前者是方向冲突容忍，后者是背景支持判定中的对立方向差
