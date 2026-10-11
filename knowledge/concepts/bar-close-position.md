---
title: "收盘位置规则"
phase: [breakout]
signal_types: [h2-entry, l2-entry, failed-breakout]
tags: [close, bar, mid, 位置, position]
difficulty: intermediate
related: [brooks-signal-catalog, btc-stc, signal-scoring-synthesis, emergency-exit, article-brooks-pa-verification, README-summary]
char_count: 1147
---
# 收盘位置规则

## 一句话定义
以K线中点（bar_mid）为界，收盘在上半部才做多、下半部才做空的信号质量过滤规则。

## 核心要点
- 做多信号要求 `close > bar_mid`（收盘在棒线上半部）
- 做空信号要求 `close < bar_mid`（棒线下半部）
- 体现 Brooks 的"收盘位置反映市场控制权"理念——收盘近高点=多头控盘，收盘近低点=空头控盘
- BTC/STC 进一步收紧至端点附近（close_position > 0.75 / < 0.25）

## 适用信号矩阵

| 信号 | 要求 | 阈值 |
|------|------|------|
| H2 多头 | close > bar_mid | >50%位置 |
| L2 空头 | close < bar_mid | <50%位置 |
| BTC | close_position 高 | >75%位置（推测） |
| STC | close_position 低 | <25%位置 |
| 双底多头 | close > bar_mid | >50%位置 |
| 双顶空头 | close < bar_mid | <50%位置 |

> 注：H1/L1 仅要求阳线/阴线（body_ratio ≥ 0.10），不强制校验收盘位置。

## 与相关概念的关系
- [[brooks-signal-catalog]]：半数以上的 Brooks 信号依赖此规则
- [[btc-stc]]：收盘位置规则的最严格形态（端点附近）
- [[signal-scoring-synthesis]]：`longBase` 要求 `close > midPt`，即收盘在上半部，分数达标但收盘不对也不入场
- [[emergency-exit]]：假突破检测依赖收盘位置的回归（上破 ph0 但收盘跌回）

## 实战应用
在代码中通过比较 `close` 与 `(high+low)/2` 或直接使用 close_position 指标。H2 和双底/双顶中此规则作为必须满足的硬性过滤，BTC/STC 则进一步收紧。

## 来源支撑
- [[article-brooks-pa-verification]] §2.2, §2.3, §2.6
- [[README-summary]]（RS 评分中的"收盘位置强弱"维度）

## 矛盾与待验证
- H1/L1 不校验收盘位置是刻意设计还是简化？Brooks 原著中 H1 是否也要求收盘位置过滤？待查证
- BTC/STC 的精确 close_position 阈值（0.75/0.25）来自代码经验值还是 Brooks 原著？原文未明确标注
