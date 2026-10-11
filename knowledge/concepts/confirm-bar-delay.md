---
title: "确认K线延迟机制"
phase: [trend, range, breakout]
signal_types: [breakout-entry, failed-breakout]
tags: [确认, atr, 默认, 入场, confatrmul]
difficulty: intermediate
related: [signal-scoring-synthesis, confirmation-bar, breakout-mechanics, article-wg-v2-master]
char_count: 842
---
# 确认K线延迟机制

## 一句话定义
可选信号延迟机制：信号触发后不立即入场，等下一根 K 线收盘且其突破幅度 ≥ ATR×confAtrMul（默认0.60）时才确认入场。

## 核心要点
- **启用开关**：`i_useConfirm`（默认 false）
- **确认条件**：下一根 K 线的收盘价突破信号K线的高/低点，且突破幅度 ≥ `i_confAtrMul × ATR14`（默认 0.60×）
- **延迟逻辑**：`longSig = longSigNow[1] and longConfirm`——取上一根K线的原始信号 + 当前K线确认
- **同时适用多空**：多头需 `close > high[1] + confNeed`，空头需 `close < low[1] - confNeed`
- **与其他过滤器的关系**：确认K线是最后一个过滤器，在 Brooks 否决之前执行

## 与相关概念的关系
- [[signal-scoring-synthesis]]：确认K线不改变评分本身，而是对「已触发信号」做二次验证
- [[confirmation-bar]]：V3 执行引擎也有确认K线概念，但机制不同（V3 是三因子评分后的入场确认，V2 是 ATR 幅度突破确认）
- [[breakout-mechanics]]：确认K线本质上是对「突破是否跟进」的微观验证

## 实战应用
启用确认K线会减少假突破信号（约减少30-40%信号量），但也会延迟入场（损失一根K线的利润空间）。在震荡区间或低波动市场中推荐启用，在强趋势中可关闭以更快入场。

## 来源支撑
- [[article-wg-v2-master]]

## 矛盾与待验证
- V2 的 ATR×0.60 确认阈值 vs V3 的确认K线机制（三因子评分后确认），哪一种对 A 股的假突破过滤效果更好？
- 确认K线延迟一根后，原来的止损/止盈参考线是否需要重新计算？
