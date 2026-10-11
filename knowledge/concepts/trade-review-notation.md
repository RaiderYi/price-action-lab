---
title: "复盘速记记号体系"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, breakout-entry]
tags: [stp, bar, buy, 入场, sell]
difficulty: intermediate
related: [daily-trade-review-framework, brooks-signal-catalog, climax, trade-management-system, review-huangzongprice-mes-daily-reviews]
char_count: 1585
---
# 复盘速记记号体系

## 一句话定义
huangzongprice 在 MES 每日复盘中使用的一套简洁英文字母缩写，用于在图表上快速标注交易信号、执行动作和市场状态。

## 核心要点
- **入场记号**：`STP`（Stop Entry，止损价入场/突破入场）、`OB`（Order Block / Outside Bar 突破）、`buy STP`（买入止损入场）、`sell STP`（卖出止损入场）
- **出场记号**：`STC`（Sell/Buy The Close，收盘价出场）、`STB`（Stop-out Break-even，止损触发出场）、`BE`（Break-even，移至盈亏平衡）
- **目标记号**：`1R`/`2R`/`3R`/`4R`（以初始风险 R 为单位的利润目标）、`MM`（Measured Move，测量走势目标）
- **K 线类型**：`cxbar`（Climax Bar，高潮棒）、`spike`（尖峰棒）、`doji`（十字星）、`IB`（Inside Bar，内包棒）、`OB`（Outside Bar，外包棒）
- **市场结构**：`TTR`（Tight Trading Range，紧密交易区间）、`TR`（Trading Range，交易区间）、`MTR`（Major Trend Reversal，主要趋势反转）、`HL`（Higher Low）/`LH`（Lower High）
- **通道与走势**：`channel`（通道）、`EMA`（指数移动均线附近）、`leg1/leg2`（第一腿/第二腿）、`MC`（Market Context 评分标注）
- **特殊记号**：`CHOB`（Close Higher Open Bar）、`RSK`（Relative Strength K-line，相对强弱 K 线）、`PTM`（Prior Trading Memory + 日期，历史交易记忆索引）
- **惊喜/陷阱**：`Bull Surprise`/`Bear Surprise`（方向性惊喜棒）、`failed wedge`（失败楔形）、`climactic reversal`（高潮反转）

## 与相关概念的关系
- [[daily-trade-review-framework]]：速记记号是复盘框架的语言载体——没有这套记号，多周期标注无法在图表上高效执行
- [[brooks-signal-catalog]]：速记记号中的信号类型（H1/H2/L1/L2）是 Brooks 16 种信号体系的简化实战版
- [[climax]]：`cxbar` 是高端的实战简写
- [[trade-management-system]]：`STP/BE/1R/2R/STB/STC` 是交易管理六组件在图表上的速记映射

## 实战应用
在复盘图表上，用 3-5 个字母即可标注一笔完整交易的入场逻辑和执行动作。例如：`B37 L2 sell STP, B38 B39 B40 i1R spike` 表示 "B37 棒作为 Low 2 卖出止损入场，B38-B40 三棒形成尖峰达到 1 倍风险目标"。

## 来源支撑
- [[review-huangzongprice-mes-daily-reviews]]（52 篇 MES 每日复盘中的全部记号实例）

## 矛盾与待验证
- 此记号体系是 huangzongprice 个人惯例还是更广泛使用？Brooks 原著中使用的术语（如 "H2 buy signal"）与复盘中的 "H2 buy STP" 是否完全等价？
- `PTM` 索引机制（标注历史日期引用类似形态）——这种费曼式记忆锚定法是否在其他交易者中也有使用？
