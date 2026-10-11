---
title: "多时间框架背景透视"
phase: [trend, range, breakout, transition]
signal_types: [breakout-entry, pullback-entry]
tags: [min, 突破, 通道, 趋势, 判断今天]
difficulty: intermediate
related: [fsm-market-cycle, binary-decisions, always-in, context-engine-v2, journal-mes-daily-reviews, article-huangzongprice-context-execution-linkage-setup, course-notes-12-18-market-cycle]
char_count: 1377
---
# 多时间框架背景透视

## 一句话定义
从高 TF 到低 TF 递进判定市场背景：45min 定方向（趋势/TR）→ 15min 定阶段（突破/回调/通道）→ 5min 定入场——高 TF 约束低 TF 交易方向。

## 核心要点
- 三层递进：45min → 15min → 5min（部分晚期复盘增加 1min）
- 高 TF 优先原则：当 45min TR 时，5min 的趋势信号只做 fade BO（不做突破跟随）
- 45min 定调：判断今天是趋势日还是 TR 日——这一判断统治全天的交易策略
- 时间框架冲突处理：低 TF 趋势在高 TF 的 S/R 位置必须暂停/反向

## 各 TF 的角色

| TF | 角色 | 核心问题 |
|----|------|---------|
| 45min | 日型判定 | 今天是趋势日还是 TR 日？ATR 水平？ |
| 15min | 阶段定位 | 当前处于突破/通道/TR 的哪个阶段？腿位？ |
| 5min | 入场执行 | 哪个信号可交易？入场棒是哪根？ |
| 1min | 微调确认 | （2026年后Gemini辅助）精细入场时机 |

## 与相关概念的关系
- [[fsm-market-cycle]]：多 TF 透视直接应用了 Brooks 四部分周期框架——在 45min 上判断当前处于哪个周期阶段
- [[binary-decisions]]：四问二元决策（趋势/TR → 突破/通道 → 窄/宽 → 大/小反转）在每个 TF 上都要问一遍
- [[always-in]]：45min 的 AIL/AIS 判定决定 5min 的逆势交易许可
- [[fsm-market-cycle]]：Pine Script 的 FSM 状态机在单一 TF 上运行，多 TF 透视需要多个 FSM 并行
- [[context-engine-v2]]：V3 Context Engine 的多 TF 支持（multi_tf）与此概念直接对应

## 实战应用
每天开盘先看 45min 图（2-3 天数据），判断今天是趋势日还是 TR 日。如果是 TR 日，所有 5min 突破信号都过滤掉（80% 法则——TR 中 80% 突破失败），只做边界反转。如果是趋势日，只在趋势方向上做回调入场，禁逆势。

## 来源支撑
- [[journal-mes-daily-reviews]]（每份 MES 复盘的首行和 TF 标注）
- [[article-huangzongprice-context-execution-linkage-setup]]（multi_tf 信号页面）
- [[course-notes-12-18-market-cycle]]（Brooks 多 TF 市场周期教学）

## 矛盾与待验证
- A 股由于 T+1 限制，30min 可能是更合适的高 TF（而非 MES 的 45min）
- 4 个 TF 的信息过载问题——复盘中偶有只标注 45min/5min 跳过了 15min，似乎 15min 在某些市场环境下不提供额外信息
- Gemini 辅助的 1min 分析是否真的提高了入场精度（还是增加了噪音）——当前样本量不足以判断
