---
title: "Entry Test（入场回测）"
phase: [range, breakout]
signal_types: []
tags: [test, entry, 盈亏平衡, 回测, 合理入场]
difficulty: intermediate
related: [clarity-exit, protective-stops, signal-bars, scale-in-dynamics, course-slides-brooks-price-action-fundamentals]
char_count: 1062
---
# Entry Test（入场回测）

## 一句话定义
合理入场后，市场通常会在 1-3 根 K 线内回测入场点，为失望交易者提供盈亏平衡退出的机会。

## 核心要点
- 合理入场后，市场经常在**1-3 根 K 线内**回测（Test）入场价位（误差在 1-2 ticks/pips 以内）
- 如果 1-3 根内未被回测，仍可能在**20 根 K 线内**被回测（概率较低但存在）
- 回测期间，失望的交易者通常可以**盈亏平衡或小额亏损**退出
- "Test" 的定义：价格回到入场价的 1-2 ticks/pips 范围内
- 入场后立即出现 1 根以上的大反向 K 线 → 等待回测 → 回测时退出

## 与相关概念的关系
- [[clarity-exit]]：Entry Test 是 Clarity Exit 的执行窗口——当入场后前提不再清晰时，等待回测以最小化损失。
- [[protective-stops]]：回测失败（价格不回来）是止损被触发的常见场景。
- [[signal-bars]]：信号棒越强（大实体、小影线、收盘在极端），入场后被回测的概率越低。
- [[scale-in-dynamics]]：加仓者的入场价成为新的 S/R 位——加仓后的回测行为类似 Entry Test。

## 实战应用
入场后的操作流程：
1. **入场后出现反向 K 线** → 立即评估前提是否仍然有效
2. **前提不清晰** → 不要恐慌平仓，等待 1-3 根 K 线内的回测
3. **回测到来** → 盈亏平衡或小额亏损退出
4. **3 根后无回测** → 前提可能正确，继续持有但警惕 20 根内的延迟回测
5. **出现连续大反向实体** → 不要等待回测，直接退出（Clarity Exit 优先）

## 来源支撑
- [[course-slides-brooks-price-action-fundamentals]] Slide 5405-5406（Video 43 区域，Reasonable Entries: Tested）

## 矛盾与待验证
- 回测窗口（1-3 vs 20 根）是针对 5 分钟图的统计规律。不同时间框架下的窗口长度需要调整——日线图上 Entry Test 可能需要 1-3 天而非 1-3 根 5 分钟 K 线。
- 回测行为在强势突破（Strong BO）后的可靠性与弱突破后的可靠性可能有显著差异，Brooks 在幻灯片中未给出区分规则。
