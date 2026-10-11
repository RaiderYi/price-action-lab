---
title: "抛物线楔形"
phase: [trend, range, breakout, transition]
signal_types: [wedge, reversal-entry]
tags: [抛物线楔, wedge, brooks, parabolic, climax]
difficulty: intermediate
related: [three-push-wedge, climax, wedge-gravity-dual-core, spike-and-channel, trend-from-the-open, measured-move, brooks-signal-catalog, book-brooks-reversals, book-brooks-reading-price-charts]
char_count: 1309
---
# 抛物线楔形

## 一句话定义
趋势末端 K 线实体和波幅逐根加速扩大、形成抛物曲线的反转形态——Brooks 价格行为学中最高频、最标志性的趋势反转信号。

## 核心要点
- **形态特征**：趋势末端 3-10+ 根 K 线，每根比前一根更大（实体更大、波幅更宽），形成加速抛物线
- **心理机制**：恐慌性追涨/杀跌 → 多头/空头耗尽 → 市场必然反转
- **位置要求**：必须在趋势末端（已经走了相当距离），而非趋势初期
- **多头版本**：Parabolic Wedge Top（抛物线楔形顶）→ 做空信号
- **空头版本**：Parabolic Wedge Bottom（抛物线楔形底）→ 做多信号（也叫 Parabolic Sell Climax）
- **与普通楔形的区别**：普通楔形 = 收敛（推升/推低越来越小），抛物线楔形 = 发散加速（越来越暴力）

## 与相关概念的关系
- [[three-push-wedge|Three Push Wedge]]：三推楔形是抛物线楔形的一种特殊情况（恰好 3 推）。抛物线楔形可以有 3-10+ 推，且关键在于"加速"而非"三推"
- [[climax]]：抛物线楔形就是 Buy Climax / Sell Climax 的视觉表现形式
- [[wedge-gravity-dual-core]]：WG V1.5 的楔形检测模块专门检测此形态
- [[spike-and-channel]]：抛物线楔形顶之后常见 "Spike and Trading Range"（尖刺反转后进入震荡整理）
- [[trend-from-the-open]]：开盘趋势日中，抛物线楔形顶是最常见的午盘反转信号
- [[measured-move]]：抛物线楔形突破后常用量度目标预测反转幅度

## 实战应用
在 5 分钟图上，当看到一连串阳线一根比一根大、速度越来越快时，不要在加速阶段追多——这是多头最后的狂欢，等待反转信号入场做空。Brooks 说"抛物线楔形之后，预期至少 2 条腿的横向到下跌运动"。

## 来源支撑
- [[brooks-signal-catalog]]：6747 页图表百科全书中，抛物线楔形出现 237 种不同场景（共 ~683 次标题出现），是 Brooks 最高频的概念之一
- [[book-brooks-reversals]]：布鲁克斯反转篇系统阐述抛物线楔形作为核心反转形态
- [[book-brooks-reading-price-charts]]：英文原版第 9 章覆盖高潮反转（含抛物线楔形）

## 矛盾与待验证
- **楔形定义分歧**：传统技术分析中 "wedge" = 收敛形态，Brooks 的 Parabolic Wedge 恰恰是"发散加速"。术语易混淆，已在 `three-push-wedge` 概念页中标注此分歧。
- **量化识别难度**：代码实现中，抛物线楔形的"加速"判断（每根 K 线比前一根更大）容易受噪声影响。WG V1.5 采用连续更高高+更宽波幅的组合条件。
