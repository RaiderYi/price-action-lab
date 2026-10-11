---
title: "Money Stop（资金止损）"
phase: [trend, range, breakout]
signal_types: [scalp, swing]
tags: [stop, money, pips, price, action]
difficulty: intermediate
related: [protective-stops, position-sizing, trader-equation, course-slides-brooks-price-action-fundamentals]
char_count: 1095
---
# Money Stop（资金止损）

## 一句话定义
Brooks 的资金止损法：以金额/点数预设止损距离，不以技术位为准，而是基于平均日波幅或平均趋势棒尺寸的固定比例。

## 核心要点
- 日交易者的 Money Stop 通常设为**平均日波幅的 10-20%**，或约等于**平均趋势棒的尺寸**
- 对于 Emini/Forex 超短线（Scalp），Money Stop 通常 20-50 ticks/pips（即最小刮头皮利润的 2-5 倍）
- 不试图精确抓到底部/顶部，但确信底部/顶部在**该区域内**，所以用宽止损给前提以时间发挥
- "Never plan on letting stop be hit. Always try to exit before." —— 永远不计划让止损被触发，总是试图在此之前退出

## 与相关概念的关系
- [[protective-stops]]：保护性止损的两种方法之一。另一种是 Price Action Stop（以技术位为准，如信号棒外侧、量度目标外）。Money Stop 关注的是**资金风险控制**，Price Action Stop 关注的是**技术结构失效**。
- [[position-sizing]]：Money Stop 直接决定仓位大小——止损距离 × 每点价值 = 单笔最大亏损，反推手数。
- [[trader-equation]]：宽止损改善了胜率（给前提更多时间），但恶化了盈亏比（R:R）。80% 突破后有大跟进的情况适用宽止损（概率高，可以接受低 R:R）。

## 实战应用
在图中识别：找到最近 20 根 K 线的平均实体尺寸或平均日波幅（ADR），取 10-20% 作为止损距离。例如 ADR=100 pips，Money Stop ≈ 10-20 pips。入场后不要等待止损被触发——当前提不再清晰时立即退出。

## 来源支撑
- [[course-slides-brooks-price-action-fundamentals]] Slide 2606-2607（Video 30 区域）

## 矛盾与待验证
- 与 Price Action Stop 的选择权衡：Brooks 在教学中同时提及两种方法但未给出明确的"何时用哪种"决策规则。实战中可能需要根据市场状态（趋势 vs 区间）和交易类型（波段 vs 刮头皮）来动态选择。
- Money Stop 的 10-20% ADR 规则来自 Emini 市场，在 A 股（T+1、涨跌停限制）中的适配性需要验证。
