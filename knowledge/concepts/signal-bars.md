---
title: "信号棒和入场棒"
phase: [trend, range, breakout, transition]
signal_types: [breakout-entry]
tags: [反转棒, 入场棒, 信号棒是, 信号棒, 号棒]
difficulty: intermediate
related: [reversal-bars, brooks-signal-catalog, setup-anatomy, bar-counting, confirmation-bar, execution-scoring, course-notes-8-11-chart-analysis, article-huangzongprice-execution-layer-v1, rs-scoring]
char_count: 1265
---
# 信号棒和入场棒

## 一句话定义
信号棒是发出交易信号的前一根棒，入场棒是实际进入交易的那根棒——两者可以是同一棒。

## 核心要点
- **信号棒（Signal Bar）**：之前的一棒发出了交易信号，你因为它而入场
- **入场棒（Entry Bar）**：你实际进入交易的那一棒
- **最好的信号棒 = 反转棒**（仅在背景良好的情况下）
- **信号棒有时也是入场棒**：例如强空头趋势棒收于低位，空头直接在收盘卖出
- **图表上大部分棒都是信号棒**：每根棒都在发出某种信号（做多或做空），但你不必每根都交易

### 强卖出信号棒的特征
1. 开盘接近或高于前棒收盘
2. 收盘远低于前棒收盘
3. 上影线约棒高 1/3 到 1/2
4. 小的或没有下影线
5. 与前棒没有太多重叠
6. 收盘反转多棒的收盘价和极值
7. 需要强的跟进卖出（信号棒后的棒不是十字星/内包/反转棒）

### 强买入信号棒的特征
1. 开盘接近或低于前棒收盘
2. 收盘远高于前棒收盘
3. 下影线约棒高 1/3 到 1/2
4. 小的或没有上影线
5. 与前棒没有太多重叠
6. 需要跟进买入

### 弱信号棒
- 弱信号棒仍然可能是好的：背景好的话，坏信号棒常导致好交易
- 过去 5 年计算机交易量增大，强信号棒越来越少
- **背景越好，信号棒越不重要**：计算机在支撑位买入、阻力位卖出
- 如果想买但被弱信号棒分散注意力，可以切换到条形图（隐藏信号棒外观）

## 与相关概念的关系
- [[reversal-bars]]：最强的信号棒就是反转棒
- [[brooks-signal-catalog]]：16 种 Brooks 信号类型的具体形态
- [[setup-anatomy]]：信号棒是架构的两大组成部分之一（信号棒 + 背景）
- [[bar-counting]]：High/Low 序列就是一系列信号棒
- [[confirmation-bar]]：延迟确认机制——等下一根 K 线突破信号棒极值，过滤假信号
- [[execution-scoring]]：信号棒质量评分（signalBarScore）占 execScore 权重的 20%

## 实战应用
进场前问自己两个问题：(1) 信号棒够强吗（实体、影线、重叠、收盘位置）？(2) 背景支持这个信号吗（趋势/区间/支撑阻力）？两者都弱就等二次信号。

## 来源支撑
- [[course-notes-8-11-chart-analysis]]（Video 8A：Slide 9-24；Video 8D：Slide 1-32）
- [[article-huangzongprice-execution-layer-v1]]（信号棒质量评分的量化加分/减分项）

## 矛盾与待验证
- Brooks 说「背景越好信号棒越不重要」，但 [[rs-scoring]] 中信号 K 线本身占评分权重——两者的边界在哪里需要在实际回测中验证
