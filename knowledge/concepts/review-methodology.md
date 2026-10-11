---
title: "复盘方法论"
phase: [trend, range, breakout, transition]
signal_types: [wedge]
tags: [min, brooks, 多时间框, 状态, trend]
difficulty: intermediate
related: [mes-review-scoring, atm-straddle-gauge, brooks-four-step-context, fsm-market-cycle, review-methodology, review-mes-huangzongprice-collection]
char_count: 1648
---
# 复盘方法论

## 一句话定义
huangzongprice 的三层日复盘框架：日型总判 → 逐棒信号评分 → 多时间框架交叉验证。

## 核心要点

### 三层结构

#### 第一层：日型总判（一句话）
每份复盘以一行日型总结开头，将当日归类到 Brooks 的日型体系中：
- **趋势日**：`bear trend from the open` / `bull trend from the open`
- **高潮反转日**：`sell climax from the open then HL MTR`
- **楔形反转日**：`wedge bottom then HL MTR`
- **区间日**：`trading range all day`
- **混合日**：`climactic reversal then trading range` / `trend trading range all day`

#### 第二层：逐棒信号评分（MC10+2）
对当日每一段行情的关键信号棒进行 12 因子评分（见 [[mes-review-scoring]]），格式为：
```
B1-B10 MC10+2 [-5%K, -5% Cprior H, ..., +5% time control leg2 65%]
```
评分结果为负的信号放弃；为正的标记入场时机。

#### 第三层：多时间框架交叉验证
- **1min**：微观入场时机（精确到棒）
- **5min**：主交易周期，信号棒识别
- **15min / 35min / 45min**：中周期背景确认（TR 状态、趋势结构）
- 不同时间框架的信号方向必须一致才入场

### 复盘模板常量
- **"Best Loser Wins"** — Tom Hougaard 交易心理书引用，每份复盘末尾签名
- **"by SC2"** — 模板来源
- **Matthew 6:21** — 时间戳标记
- **ATM Straddle** — 波动率预期（见 [[atm-straddle-gauge]]）
- **TR 占比** — 5min TR% 和 45min TR 状态

### 信息密度
单份复盘通常 ≤2KB，高度压缩的速记格式。全量约 150 份覆盖 7 个月（2025-08 ~ 2026-03），在 2025-12 后增加了 Gemini AI 辅助解读。

## 与相关概念的关系

- [[mes-review-scoring]]：复盘第二层的核心工具
- [[atm-straddle-gauge]]：复盘第一层和第二层之间的波动率桥梁
- [[brooks-four-step-context]]：三层复盘法本质上是对 Brooks 四步上下文分析（价位→阶段→动能→否决）的日频应用
- [[fsm-market-cycle]]：复盘第一层的日型判断直接对应 FSM 状态
- [[review-methodology]]：本页自身——复盘作为元认知工具

## 实战应用
每日收盘后按三层框架复盘：(1) 判断日型；(2) 逐棒评分，标记所有错过的和抓住的信号；(3) 多时间框架比对，确认入场时的背景一致性。**关键在于记录"为什么没做"而不是"为什么做了"**——错过的信号比做错的交易更有学习价值。

## 来源支撑
- [[review-mes-huangzongprice-collection]]

## 矛盾与待验证
- 复盘中的 "leg2 完成度 65%" 的计算方法（如何量化腿的完成百分比？）未说明
- Gemini AI 解读的质量和一致性未经验证（AI 是否理解了 Brooks 语境？是否产生了幻觉？）
- "Best Loser Wins" 的交易心理框架与 Brooks "I don't care size" 的互补关系待深入分析
