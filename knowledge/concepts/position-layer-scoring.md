---
title: "位置层评分（Position Layer Scoring）"
phase: [range, breakout]
signal_types: [wedge, swing]
tags: [atr, min, 位置层评, 区间中部, ema]
difficulty: intermediate
related: [support-resistance, brooks-four-step-context, atr-scaling, ctx-scoring, late-breakout, article-huangzongprice-context-engine-v1, article-20260520-wedge-gravity-brooks-context-v3, article-huangzongprice-context-engine-v3-rebuild]
char_count: 2278
---
# 位置层评分（Position Layer Scoring）

## 一句话定义
将价格与关键支撑/阻力的距离统一归一化为 ATR 倍数，通过阈值判定和加权加减分生成 0-1 位置层评分，量化「市场在什么价位」。

## 核心要点
- **核心函数**：`f_distAtr(level, atrBase) = |close - level| / max(atrBase, mintick)`——所有距离归一化为 ATR 倍数
- **关键价位池**（6 个）：最近波段高点 ph0、波段低点 pl0、Donchian High(20)、Donchian Low(20)、EMA20、Fib50(ph0-pl0中点)
- **三级判定**：`at`（贴近，≤0.60 ATR）→ +0.30；`near`（靠近，≤1.20 ATR）→ +0.18；远离 → 不加分
- **惩罚项**：区间中部（距中线 ≤ 区间宽×20%）→ -0.28；追价突破 → -0.20；目标位临近 → -0.16
- **基础分**：0.10，多空双向独立计算，最终 `f_clamp01()` 钳位到 [0,1]

## 评分细则

### 加分项（多方 `locScoreL`）
| 条件 | 加分 | 含义 |
|------|------|------|
| 贴近多方支撑（pl0/DonchianL/EMA/Fib50 最近者 ≤ 0.60 ATR） | +0.30 | 价格在强支撑上 |
| 靠近多方支撑（≤ 1.20 ATR） | +0.18 | 价格在弱支撑附近 |
| 距 Fib50 ≤ 0.80 ATR | +0.08 | 波段中点磁力位 |
| 收盘 ≤ EMA20 + 0.3×ATR14 | +0.05 | 价格在均线之下或贴近 |

### 减分项（多方）
| 条件 | 减分 | 含义 |
|------|------|------|
| 区间中部 | -0.28 | 无方向参照的随机区域 |
| 多方向追价突破 | -0.20 | 已远离支撑，追高风险大 |
| 贴近空方阻力 | -0.28 | 价格在强阻力附近 |
| 靠近空方阻力 | -0.14 | 价格在弱阻力附近 |
| 多方目标位临近 | -0.16 | 盈利空间已压缩 |

（空方 `locScoreS` 为镜像逻辑）

### 距离计算逻辑
```
bullSupportDist = min(distToPl0Atr, distToDonchLAtr, distToEmaAtr, distToFib50Atr)
bearResistDist  = min(distToPh0Atr, distToDonchHAtr, distToEmaAtr, distToFib50Atr)
bullTargetDist  = min(distToPh0Atr, distToDonchHAtr)
bearTargetDist  = min(distToPl0Atr, distToDonchLAtr)
```
即：多方同时取距所有支撑的最小值（最近支撑）和距所有阻力的最小值（最近目标）；空方镜像。

## 与相关概念的关系
- [[support-resistance|Support/Resistance]]：理论基础——S/R 的识别方法和 16+ 种类型
- [[brooks-four-step-context]]：框架层级——位置层是四步法的第一步
- [[atr-scaling]]：工具基础——ATR 归一化阈值的标尺概念
- [[ctx-scoring]]：互补——ctx-scoring 描述评分框架，本页给出具体公式
- [[late-breakout]]：追价判定——位置层中 `lateBreakout` 的详细逻辑

## 实战应用
在 TradingView 图表上观察 `locScoreL`/`locScoreS`（显示在 data_window 中）：分数 ≥ 0.5 表示价格处于有利位置；分数接近 0 表示价格在区间中部或贴近对方阻力——此时即使信号出现也不建议入场。

## 来源支撑
- [[article-huangzongprice-context-engine-v1]]（v1 设计稿）
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：完整加减分表 + locScore = 0.10 + Σ加分 - Σ扣分 + clamp01 的精确实现）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 源码第421-464行——位置层评分完整实现：bullSupportDist/bearResistDist 六价位取最小值 + midRangeLocation判定 + 加减分细则）

## 矛盾与待验证
- 距离判定阈值（0.60/1.20 ATR）是针对什么品种/周期优化的？文档未说明，可能需跨品种验证
- `midRangePct` 默认 0.20——区间中部定义为距离中线 ≤ 区间宽度的 20%，这是较窄的定义
- 位置层权重在综合背景分中占 40%（`i_locWeight`），是三层中最高——反映了「位置是交易第一要素」的 Brooks 哲学
