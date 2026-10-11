---
title: "Z 值 (Z-Score)"
phase: [range, transition]
signal_types: [h2-entry, l2-entry, scalp, flag]
tags: [值越高, 破产风险, 简化版, 值系统, brooks]
difficulty: intermediate
related: [trader-equation, position-sizing, scaling-in, signal-scoring-synthesis, course-notes-30-36-prerequisites]
char_count: 944
---
# Z 值 (Z-Score)

## 一句话定义
衡量交易策略结果可靠性的统计指标——Z 值越高，策略的系统性越强、破产风险越低。

## 核心要点
- **用途**：检验回测/实盘结果的统计显著性，判断盈利是来自真正的优势还是随机运气
- **Z 值公式**（Brooks 简化版）：`Z = (N×(R−0.5)−X) / √(X×(X−N)/(N−1))`，其中 N=总交易数，R=赢/输序列数，X=2×W×L
- **高 Z 值系统（≈5）**：高胜率 + 盈利规模均匀 → 结果可靠、容错率高、可错过交易仍赚钱 → 适合刮头皮策略（如 H2/L2 旗形反转）
- **低 Z 值系统（<2）**：低胜率 + 靠少数大赢利支撑 → 结果不可靠、容错率低、错过一笔大赢利则系统亏损 → 不要交易这类策略
- **优秀交易者的 Z 值**：通常 2-3，对应每笔交易可冒账户 2% 风险
- **破产风险**：低 Z 值意味着盈亏标准差大，连续亏损导致爆仓的概率高

## 与相关概念的关系
- [[trader-equation]]：交易者方程告诉你单笔交易是否合理，Z 值告诉你整个策略在一系列交易后是否可信
- [[position-sizing]]：Z 值越高，每笔交易可冒的百分比风险越大
- [[scaling-in]]：加仓策略会改变 Z 值——提高胜率可能提升 Z，但增大单笔风险可能降低 Z
- [[signal-scoring-synthesis]]：RS 评分是信号级过滤，Z 值是策略级检验——两者在不同层级保证质量

## 实战应用
回测或实盘运行 30+ 笔交易后，计算 Z 值：如果 Z < 2，策略不可信，需要改进或弃用；如果 Z > 3，说明策略统计可靠，可以逐步放大仓位。

## 来源支撑
- [[course-notes-30-36-prerequisites]]（Video 30C: Slide 2-8）

## 矛盾与待验证
- Brooks 给出的 Z 值公式是简化版，Quant 领域通常使用正态分布标准化公式 `Z = (X−μ)/σ`。两种公式对同一交易序列的结果是否相近？本 Wiki 的分析系统是否应内置 Z 值自动计算？
