---
title: "背景评分引擎（Background Scoring Engine）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, swing]
tags: [背景否决, 分值, bgscore, 背景评分, 权重]
difficulty: intermediate
related: [gravity-field, fsm-market-cycle, emergency-exit, signal-scoring-synthesis, wedge-gravity-dual-core, article-20260519-wedge-gravity-v41-flowchart, article-20260520-wedge-gravity-brooks-context-v3, article-huangzongprice-context-engine-v3-rebuild, phase-transition-detection]
char_count: 3183
---
# 背景评分引擎（Background Scoring Engine）

## 一句话定义
WG Brooks V4.1 的三层加权背景评分系统——Location(40%) + Phase(35%) + Momentum(25%) → bgScore，与阈值比较产出"背景支持"或"背景否决"决策。

## 核心要点

### 背景分计算公式
```
bgScore = locScore × 0.40 + phaseScore × 0.35 + momScore × 0.25
```

### 背景支持判断
- bgScore ≥ i_bgThr（默认 0.58）
- bgScore ≥ 对立方向分数 - 0.02
- NOT 背景冲突
- NOT 背景否决
→ **bgSupport = true**

### Layer 1: Location 位置分（权重 40%）
```
locScore = 基础分(0.10) + 加分项 - 减分项
```

| 做多加分项 | 分值 | 做空加分项 | 分值 |
|-----------|------|-----------|------|
| atBullSupport | +0.30 | atBearResistance | +0.30 |
| nearBullSupport | +0.18 | nearBearResistance | +0.18 |
| 引力场触发(gScore>阈值) | +0.12 | 引力场触发 | +0.12 |
| 接近50%斐波那契位 | +0.08 | 接近50%斐波那契位 | +0.08 |
| 收盘在EMA下方 | +0.05 | 收盘在EMA上方 | +0.05 |

| 做多减分项 | 分值 | 做空减分项 | 分值 |
|-----------|------|-----------|------|
| 中部位置 | -0.28 | 中部位置 | -0.28 |
| 追多(晚突破) | -0.20 | 追空(晚突破) | -0.20 |
| 靠近空头阻力位 | -0.28/-0.14 | 靠近多头支撑位 | -0.28/-0.14 |
| 接近多头目标位 | -0.16 | 接近空头目标位 | -0.16 |

### Layer 2: Phase 阶段分（权重 35%）

**做多阶段分 (phaseScoreL)**：
| 趋势状态 | 条件 | 分值 |
|---------|------|------|
| 多头趋势 | 趋势健康 | +0.52 |
| 多头趋势 | 趋势转弱 | +0.30 |
| 多头趋势 | 普通趋势 | +0.20 |
| 空头趋势 | 下降楔形+H2+近支撑（潜在反转） | +0.22 |
| 中性 | 震荡区间+近支撑 | +0.24 |
| 中性 | 其他 | +0.10 |

**减分项**：
- 双边势/非近支撑：-0.14
- 多头健康趋势（对做空而言）：-0.26

### Layer 3: Momentum 动量分（权重 25%）
```
momScore = 基础分(0.10) + 冲击分(0.30) + 趋势健康(0.28) + 波动比(0.12) + 加分项 - 减分项
```

| 组成部分 | 计算方式 |
|---------|---------|
| impulseScore（冲击分） | 实体占比×0.55 + 收盘位占比×0.45 |
| trendHealth（趋势健康） | EMA陡峭性 + 低重叠度 + 无紧急逃生 |
| swingCompare（波动比） | 当前波动/前期波动 的接近程度 |
| 加分项 | 空头时出现H2/L2结构 +0.12 |
| 减分项 | 趋势成熟度 -0.20 / 衰竭风险 -0.18 / 当前腿转弱 -0.12 |

### 背景否决条件（绝对禁止交易）
1. **中部位置 AND 震荡区间**：最差的位置+最不确定的环境
2. **健康趋势与策略方向相反**（且无楔形/H2 支撑）：逆势在健康趋势中极危险
3. **晚突破位置 + 晚突破方向**：已错过最佳入场点
4. **高成熟度/高衰竭风险 + 当前腿转弱 + 晚突破**：多重负面叠加

→ **bgVeto = true**

## 与相关概念的关系
- [[gravity-field]]：引力场是 Location 层的加分来源之一（+0.12），位置层是对引力场的加权使用
- [[fsm-market-cycle]]：FSM 决定 Phase 层的趋势方向和阶段分类
- [[emergency-exit]]：紧急逃生不触发时，趋势健康分量才能获得满分
- [[signal-scoring-synthesis]]：背景评分是下游 lFin/sFin 的"环境预筛选"，v3 中进一步演化为执行分的 bg×0.55 权重
- [[wedge-gravity-dual-core]]：背景评分引擎是双核架构中"软评分核"的背景版——在结构评分和信号评分之外独立运行

## 实战应用
- bgScore ≥ 0.58 且无否决 → 背景绿灯，可以向下游信号评分传递
- 中部位置 -0.28 是一个很大的惩罚项——价格在区间中部时几乎不可能达到 bgThr=0.58（基础分仅 0.10+0.35×0.10+0.25×0.10 = 0.16），强烈鼓励在关键位置（支撑/阻力/引力场）交易
- 背景否决是绝对禁止，即使信号棒满分也不能覆盖

- V6 的是对 V5/V4 momScore 的拆分重构——将原本 25% 权重的二级子项升级为独立的并行双维度
- V6 的是 V5 背景否决的进一步简化——从 4 条件扩展到 6 条件（含阶段×位置组合 + 兜底）
- V6 的抛弃了三层加权结构——不用加权求和，用效率+重叠度直接阈值判定阶段

## 来源支撑
- [[article-20260519-wedge-gravity-v41-flowchart]]（V4.1 设计文档）
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 完整 Pine Script 源码——三层权重 40/35/25、否决四条件、所有加减分值精确实现）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 源码：背景评分引擎完整 Pine Script 落地，含5过渡检测的精确 transitionCount 计数器 + 4类否决条件的代码）

## 矛盾与待验证
- 三层权重（40/35/25）和各分项分值全部是经验参数，未经过回测数据驱动的优化。这些参数的最优值可能因品种/周期而异
- ✅ **已解决**：Phase 层的健康/转弱/普通分类标准在 V3 源码中已精确量化：`phaseTrendHealthy = phaseIsTrend && phaseConfidence>=0.70 && emaSteep && avgOlp<0.24 && NOT phaseIsTransition`。详见 [[phase-transition-detection]] 的五证据系统
- 「接近多头目标位 -0.16」和「靠近空头阻力位 -0.28」可能重叠——如果多头目标位恰好是空头阻力位，源码中两者独立加减分（加减分列表顺序执行），即实际会叠加（共 -0.44）。这可能过于激进
