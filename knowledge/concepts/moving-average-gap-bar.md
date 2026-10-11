---
title: "移动平均缺口棒 (MAGB)"
phase: [trend, range, transition]
signal_types: [pullback-entry]
tags: [magb, mtr, 移动平均, 熊市趋势, ema]
difficulty: intermediate
related: [gaps, major-trend-reversal, forty-sixty-rule, channel, encyclopedia-brooks-price-action-manual]
char_count: 1191
---
# 移动平均缺口棒 (MAGB)

## 一句话定义
K线实体完全在移动平均线的另一侧——趋势末期最可靠的逆转预警信号之一。

## 核心要点
- MAGB = Moving Average Gap Bar：一根或多根K线的**最低点与均线之间存在间隙**（完全在均线上方/下方）
- 牛市趋势中：K线完全跌到均线下方 → MAGB → 可能见顶，卖方开始主导
- 熊市趋势中：K线完全涨到均线上方 → MAGB → 可能见底，买方开始主导
- MAGB 通常是**趋势最后一段的信号**，随后大概率出现 MTR（主要趋势反转）
- MAGB 的本质：均线是多空平衡的参照线，价格穿越均线意味着平衡被打破

## Brooks 原始描述

> 例如，如果存在强劲的熊市趋势，现在正在反弹，并且一个或多个柱形图现在完全高于移动平均线，我将这些柱形图称为间隙柱形图（柱形图的最低点与移动平均线之间存在间隙）。交易者通常会在前一根柱线低点下方一个基点处做空，寻找熊市低点的测试。然而，由于反弹强劲，这种抛售通常会伴随着主要趋势反转和两条腿的上涨。

## 交易含义

| 场景 | MAGB 信号 | 预期走势 |
|------|----------|---------|
| 熊市趋势中 K线全部 > EMA | MAGB 向上 | 做空→测试熊市低点，但可能反转上涨（MTR） |
| 牛市趋势中 K线全部 < EMA | MAGB 向下 | 做多→测试牛市高点，但可能反转下跌（MTR） |
| MAGB 出现后反弹持续 | MAGB 失败 | 趋势反转确认——反转涨幅通常≥熊市趋势的1/3 |

## 与相关概念的关系
- [[gaps]]：MAGB 是缺口的一种特殊类型——K线与均线之间的缺口，而非价-价缺口
- [[major-trend-reversal|Major Trend Reversal]]：MAGB 是 MTR 的前兆信号之一
- [[forty-sixty-rule]]：MAGB 之后再顺原趋势交易的概率降低，逆趋势概率升高
- [[channel]]：MAGB 常在通道向交易区间过渡时出现

## 实战应用
在5分钟图上叠加20EMA，当K线实体完全穿越均线（注意是"完全在另一侧"，不仅是K线穿越），且反弹/回调已有数根K线时，警惕趋势末段。

## 来源支撑
- [[encyclopedia-brooks-price-action-manual]] 第12章（支撑和阻力）

## 矛盾与待验证
- Brooks 同时说"MAGB 之后做空测试熊市低点"和"MAGB 之后通常伴随MTR上涨"——这取决于反弹的强度。如果MAGB后出现强牛棒（大实体收于高点），反转概率更高；如果MAGB后反弹疲弱，可继续做空。需要量化界定"强反弹"的标准。
