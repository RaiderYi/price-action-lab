---
title: "加仓 (Scaling In)"
phase: [trend, range, transition]
signal_types: [pullback-entry, scalp, swing]
tags: [加仓, video, 加仓交易, 加仓策略, scaling]
difficulty: intermediate
related: [trader-equation, z-score, trade-management-system, position-sizing, course-notes-30-36-prerequisites]
char_count: 986
---
# 加仓 (Scaling In)

## 一句话定义
在已持有盈利仓位的基础上增加第二笔（或更多）同向仓位——以恶化风险回报比为代价，提高整体赚钱的概率。

## 核心要点
- **本质**：加仓 = 概率 + 风险 + 回报的同时博弈
  - 加仓提高最终赚钱的概率（因为更多仓位在正确的方向上）
  - 但增加了总风险（更多资金暴露），减少了平均风险回报比
- **操作方式**（Brooks 示例）：
  - 第一笔：在回调棒下方卖出（空头）
  - 第二笔（加仓）：在 Low 2 卖出信号棒下方再卖出
  - 第一笔保本退出，第二笔获利 → 净盈利
- **只在初始仓位盈利时加仓**：如果第一笔已亏损，加仓只会放大亏损
- **加仓的陷阱**：用刮头皮方式管理加仓交易会亏钱——加仓交易应按波段逻辑管理（趋势恢复时持有），而非赚一点就跑
- **加仓 vs 一次满仓**：加仓降低初始风险（第一笔仓位小），但给了趋势确认后再增加暴露的灵活性

## 与相关概念的关系
- [[trader-equation]]：加仓改变了方程——提高概率项但恶化 RR 项（增加总风险、减少单笔平均回报）
- [[z-score]]：加仓策略改变策略的 Z 值，需要重新检验
- [[trade-management-system]]：加仓后需要调整止损/BE 的管理逻辑——加仓部分和初始仓位的管理规则可能不同
- [[position-sizing]]：加仓的总暴露不能超过仓位规模上限

## 实战应用
在趋势确认的方向上：初始小仓位入场 → 趋势延续/回调结束 → 在第二个信号处加仓 → 将两笔仓位的止损调整到保本 → 按波段逻辑持有至趋势衰竭。加仓前确认：第一笔是否盈利？总风险是否仍在账户 1-2% 以内？

## 来源支撑
- [[course-notes-30-36-prerequisites]]（Video 30B Slide 7, Video 35A/B/C）

## 矛盾与待验证
- Brooks 在 Video 30B 演示空头加仓（Scaling into short），在 Video 35 详细展开加仓策略。两处描述一致，无明显矛盾。
- 本 Wiki 的 A 股分析系统中是否实现了加仓逻辑？如果未实现，加仓是手动执行还是自动化候选？
