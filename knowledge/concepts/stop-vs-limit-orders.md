---
title: "止损单 vs 限价单 (Stop vs Limit Orders)"
phase: [trend, range, breakout]
signal_types: [breakout-entry, pullback-entry, scalp, swing]
tags: [止损单, 量化系统, stop, brooks, fade]
difficulty: intermediate
related: [fsm-market-cycle, breakout-mechanics, trading-range-quality, swing-vs-scalp, book-brooks-price-action-manual, al-brooks]
char_count: 982
---
# 止损单 vs 限价单 (Stop vs Limit Orders)

## 一句话定义
Brooks 为不同水平交易者推荐的入场订单类型选择框架——新手用止损单跟随动量，老手可用限价单逆势入场。

## 核心要点
- **止损单入场（Stop Entry）**：在市场突破某关键价位时入场。优势：市场正在朝你的方向走（至少一个 tick）。Brooks 建议新手只用止损单。
- **限价单入场（Limit Entry）**：在市场回调到某价位时入场。优势：更好的入场价格、更小的止损距离。劣势：逆势入场、胜率低。
- **止损单市场 vs 限价单市场**：强突破 = 止损单市场（顺势追）；交易区间 = 限价单市场（逆势 fade）。
- **每一张限价单都是另一方的止损单**：你以限价单卖出=买入方以止损单买入。双方都有数学理由。
- **入场方式选择取决于市场阶段**：突破阶段→止损单；通道阶段→混合；交易区间→限价单 fade。

## 与相关概念的关系
- [[fsm-market-cycle]]：市场阶段直接决定入场方式选择
- [[breakout-mechanics]]：强突破中必须用止损单追，因为 pullback 可能很久不来
- [[trading-range-quality]]：宽区间可用限价单 fade 边界；紧区间不应交易
- [[swing-vs-scalp]]：止损单入场→通常波段（高概率但止损远）；限价单入场→通常刮头皮（低概率但止损近）

## 实战应用
- 新手铁律：只用止损单入场——市场正在朝你的方向走，心理上更容易管理
- 在交易区间顶部看到大阳线→不要追多（那是买盘真空测试阻力），用限价单做空
- 在强突破中的第四根 K 线上追入：概率 60%+ 但止损可能 50 pip 外→降低仓位

## 来源支撑
- [[book-brooks-price-action-manual]]（第 78-83 页专章：Stop Orders）
- [[al-brooks]]

## 矛盾与待验证
- 与 huangzongprice 量化系统的信号触发方式对比：量化系统通常使用限价单在特定价位入场（而非止损单突破入场）——这是因为量化系统可以精确计算概率，而 Brooks 手动交易者的概率判断更依赖直觉。
