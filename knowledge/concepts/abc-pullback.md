---
title: "ABC 回调 (ABC Pullback / H2 L2)"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, pullback-entry]
tags: [回调, abc, 上升趋势, 下降趋势, 两条腿横]
difficulty: intermediate
related: [market-structure, always-in, brooks-signal-catalog, trend-bars-doji, fsm-market-cycle, course-1-7-intro, course-notes-8-11-chart-analysis]
char_count: 1065
---
# ABC 回调 (ABC Pullback / H2 L2)

## 一句话定义
趋势中的双腿回调模式——上升趋势中的 ABC 回调形成高点 2 (H2) 买入机会，下降趋势中形成低点 2 (L2) 卖出机会。

## 核心要点
- **上升趋势 ABC**：两条腿横盘至下跌 → 寻找高点 2 (H2) 回调 → 在信号棒上方止损买入
- **下降趋势 ABC**：两条腿横盘至上涨 → 寻找低点 2 (L2) → 在信号棒下方止损卖出
- **回调的最低要求**：多头趋势中一棒低点低于前棒低点；空头趋势中一棒高点高于前棒高点
- **隐含回调**：多头趋势中的空头棒/十字星即使不创新低也是隐含回调（低周期上的实际回调）
- **50% 回调**：最重要的回调位——概率偏向趋势恢复，风险/回报平衡
- 如果突破很大，需重新计数（新突破 → 新回调）
- 回调增长到 20+ 棒 → 无止境回调，多空概率各 50%
- "叫什么名字并不重要，你要寻找机会进入趋势"
- 回调是趋势恢复的信号（Brooks 认为它不同于交易区间）

## 与相关概念的关系
- [[market-structure]]：ABC 回调只存在于趋势中，是趋势延续的结构
- [[always-in]]：在 AIL 中只做 H2 买入，在 AIS 中只做 L2 卖出
- [[brooks-signal-catalog]]：bull_h2 和 bear_l2 是核心趋势延续信号
- [[trend-bars-doji]]：信号棒必须是趋势棒（收盘在有利方向）
- [[fsm-market-cycle]]：回调 = 通道的开始——一旦出现回调，突破阶段结束，市场进入通道阶段

## 实战应用
在上升趋势中，等待至少两条腿的横盘或小幅下跌 → 当出现多头趋势棒（信号棒）时，在其高点上方设置 buy stop 入场。

## 来源支撑
- [[course-1-7-intro]]（Slide 12-13）
- [[course-notes-8-11-chart-analysis]]（Video 9A：回调定义、50% 回调、隐含回调、无止境回调）
- [[brooks-signal-catalog]]（H2/L2 的代码化实现）

## 矛盾与待验证
- 回调与交易区间的边界：Brooks 说"当我认为趋势恢复而不是反转时，我称之为回调而不是交易区间"——这个判断是主观的
- 如何区分"大突破需要重新计数"和"正常回调"的客观标准？
