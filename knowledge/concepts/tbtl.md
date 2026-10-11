---
title: "TBTL（十棒两腿）"
phase: [range, transition]
signal_types: [pullback-entry, reversal-entry]
tags: [tbtl, climax, post, brooks, two]
difficulty: intermediate
related: [climax, brooks-signal-catalog, atr-scaling, article-brooks-pa-verification, README-summary]
char_count: 1031
---
# TBTL（十棒两腿）

## 一句话定义
Post Climax 反转信号的唯一确认机制：高潮后须形成至少 10 根K线、两腿结构的回调/反弹。

## 核心要点
- TBTL = Ten Bars Two Legs，即"十棒两腿"
- 高潮K（实体 > 1.8 ATR）之后，市场需要冷却：至少 10 根 K 线的两腿结构才能确认反转
- 在代码中位于 classify 层（非检测层），即先检测到 Post Climax 信号，再由 classify 判断 TBTL 是否完成
- 未完成 TBTL 的 Post Climax 信号会被过滤掉，不输出

## 与相关概念的关系
- [[climax]]：TBTL 是 Post Climax 的**唯一确认条件**——无 TBTL 即无有效信号
- [[brooks-signal-catalog]]：TBTL 仅用于 Post Climax，不参与其他 14 种信号的过滤
- [[atr-scaling]]：TBTL 的前置条件是高潮K实体超过 1.8 ATR

## 实战应用
实盘中看到极端大K线（高潮K）后，不急于入场——等待至少 10 根 K 线的两腿回调（做多）或反弹（做空）完成后才考虑入场。TBTL 的本质是"给市场时间确认反转"。

## 来源支撑
- [[article-brooks-pa-verification]] §2.4
- [[README-summary]]（Post Climax 策略中提及但未详述 TBTL）

## 矛盾与待验证
- "10 根K线"的阈值来自 Brooks 原著还是代码作者的工程经验？需查 Brooks 原著确认
- "两腿"的精确定义（如何判定一腿的起点/终点）在验证文档中未展开，需查阅代码实现细节
- **书本 vs 实现差异（post_climax TBTL）**： 发现实现的 `two_legs_after_climax_approx`（近似两腿，允许不精确匹配）与书本的 `two_legs_after_climax` 存在差异。更重要的是，TBTL 自动否决（`ann.tbtl_active=True → is_valid=False`）将 Brooks 的"不应过早入场"软建议提升为硬规则——可能过于保守，也可能恰好是合理的工程防护。高潮条幅阈值 >1.8 ATR 是纯实现层决策，Brooks 原著未给出精确数字。
