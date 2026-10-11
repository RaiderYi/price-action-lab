---
title: "紧密交易区间"
phase: [trend, range, breakout, transition]
signal_types: [pullback-entry, scalp, swing]
tags: [紧密, doji, 重叠, 压倒一切, 任何方向]
difficulty: intermediate
related: [trading-range-characteristics, barbwire, buy-vacuum-sell-vacuum, breakout-mode, swing-vs-scalp, book-brooks-trading-ranges]
char_count: 1420
---
# 紧密交易区间

## 一句话定义
一种特殊的交易区间子类型：棒线高度重叠、范围狭窄、多 DOJI 和影线、双向身体并存——**压倒一切**（Trumps Everything），任何方向的突破概率不超过 55%，止损入场全部失败。

## 核心要点

### 识别标准
- 2 根或以上棒线的水平通道，棒间大量重叠
- 多次反转、大量 DOJI、突出影线、牛熊身体交替
- 在 Emini 日平均波动 10-15 点时，区间高度 ≤ 3 点为紧密 TR
- 如果棒线本身很大，4-5 点的区间也可能表现为紧密 TR

### 「压倒一切」规则（Trumps Everything）
- **无论你在图表上看到什么其他信号**，一旦市场进入紧密 TR，市场告诉你它失去了方向
- 任何方向的突破概率不超过 55%（如果前置趋势强可能 55%，否则仅 51-53%）
- 在趋势后形成的紧密 TR：顺势突破概率最多 55%
- 在高潮反转后形成的紧密 TR：两个方向概率均等
- 所有基于突破的止损入场 → **都会失败**

### 交易规则
- **新手不得交易紧密 TR**
- 只有最稳定的盈利交易者才能交易 — 而且必须用**限价单**入场
- 大多数人应等待：
  1. 出现强力突破
  2. 评估突破是否会继续（强力跟进）或失败
  3. 然后进场 — 追趋势、等回调入场、或做失败的突破

### 为什么止损入场失败
- 紧密 TR 的 math 对止损入场不利 — 风险通常会大于回报
- 限价单的 trader's equation 虽可能有利，但判断何时限价有利太难
- 紧密通道（斜的紧密 TR）同样规则适用

### 最终会突破
- 多头/空头在区间内逐步加仓达到最大头寸规模
- 当一方无力继续加仓抵抗时 → 突破
- 突破时另一方被迫止损 → 加速突破（Short Covering / Long Liquidation）

## 与相关概念的关系
- [[trading-range-characteristics]]：紧密 TR 是交易区间的特殊子类型，特征清单中的极端形式
- [[barbwire]]：紧密 TR 的一种具体表现形式 — 3+ 棒重叠含 DOJI 且影线突出
- [[buy-vacuum-sell-vacuum]]：紧密 TR 中的微真空效应 — 微观买卖压力缺失
- [[breakout-mode]]：紧密 TR 本身不是突破模式 — 它是「方向完全不确定」的模式
- [[swing-vs-scalp]]：紧密 TR 中「刮头皮」都很难做 — 空间不够

## 实战应用
当屏幕上的价格波动突然收窄到极小范围（如 BTC 在 100 点内横盘超过 5 根 K 线），停止一切入场操作。不要被「看起来要突破了」的微型尖刺诱惑。等待一根大实体棒真正突破紧密区间且**有跟进**（第二根棒继续同向）再考虑入场。此时做突破回调入场比直接追突破更安全。

## 来源支撑
- [[book-brooks-trading-ranges]] — Chapter 22（pp.736-742）

## 矛盾与待验证
- Brooks 的「3 点」阈值针对 Emini — A 股/BTC 的相对阈值是多少？建议用 ATR 的百分比来定义
- 「55% 最多」是否可量化验证？需要大量采样统计
