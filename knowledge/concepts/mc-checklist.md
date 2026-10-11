---
title: "MC 10+2 评分清单"
phase: [trend, range, breakout, transition]
signal_types: [swing]
tags: [leg, regime, mes, mrk, ctx]
difficulty: intermediate
related: [brooks-four-step-context, ctx-scoring, brooks-signal-catalog, signal-scoring-synthesis, trend-strength-filter, journal-mes-daily-reviews]
char_count: 1722
---
# MC 10+2 评分清单

## 一句话定义
MES 每日复盘使用的 12 维度棒线评分系统，每项 ±5%~±10% 权重，快速量化当前价格行为的质量与方向信度。

## 核心要点
- 评分对象：每段趋势/TR 的棒线序列（如 B1-B7、B13-B34）
- 评分格式：`MC 10+2` — 10 项棒线质量 + 2 项宏观定位
- 扣分项（-5%~-10%）：棒型异常、收盘位置不佳、doji、无 tick gap、BO/TR 判断失误、腿晚期
- 加分项（+5%~+10%）：价格控制良好、时间控制紧凑、腿位在 SR 关键位置、突破判断正确
- 核心输出：`leg2 XX%` — 第二腿发生的概率估计（如 leg2 55%、leg2 70%）

## 评分维度详解

| # | 维度 | 扣分/加分 | 含义 |
|---|------|----------|------|
| 1 | 棒型 (K) | -5% | 是否为强趋势棒（大实体小影线） |
| 2 | 前棒收盘位置 (Cprior H/L) | -5% | 收盘在棒线高位=多头控盘，低位=空头控盘 |
| 3 | Cprior 方向确认 | -5% | 连续收盘方向一致性 |
| 4 | 无 Tick Gap | -5% | 棒间无跳空=趋势连续 |
| 5 | Doji | -5% | 出现十字星=犹豫/方向减弱 |
| 6 | BO/mrk regime | -10% | 突破判断 vs TR 判断正确率（权重最高） |
| 7 | Price Control | +5% | 一方完全控盘，无重叠 |
| 8 | Swing Point 1ABR | +5% | 位于关键摆动点（1倍ATR范围内） |
| 9 | Time Control | +5% | 棒线持续朝一个方向移动的时间控制 |
| 10 | Late Leg | -5%/ | 腿是否接近衰竭（腿位过高/过低） |
| 11 | Leg2% | 输出 | 第二腿发生概率（55%=弱、70%=强） |
| 12 | （上下文定制） | 变体 | 如 `climactic reversal`、`TTR`（tight trading range）等情景修正 |

## 与相关概念的关系
- [[brooks-four-step-context]]：MC 评分清单是对 Brooks 四步法的实操简化——将 4 步压缩为 12 个可快速打分的维度
- [[ctx-scoring]]：Ctx 评分（0-1 量化）是 Pine Script 工程化版本，MC 清单是人工主观快速版
- [[brooks-signal-catalog]]：MC 评分的结果决定哪些信号类型在当前背景下可交易
- [[signal-scoring-synthesis]]：lFin/sFin 是信号本身的质量评分，MC 是信号所在棒线序列的背景质量评分——两者互补
- [[trend-strength-filter]]：MC 清单中的 BO/mrk regime 和 leg2% 维度与趋势强度过滤的维度高度重叠

## 实战应用
在 MES 5min 图表上，对每段走势用笔快速写下 `MC 10+2` 逐项评分，leg2% 低于 50% 时不入场，高于 70% 时加仓。复盘时用红色/绿色标注评分差异，找到误判原因。

## 来源支撑
- [[journal-mes-daily-reviews]]（151 份 MES 每日复盘中的固定标注格式）

## 矛盾与待验证
- MC 清单的 12 项权重是否固定（±5% 始终不变，还是根据 market regime 调整）尚未明确——复盘中偶有变体（如 climax 场景下 late leg 权重翻倍）
- leg2% 的计算公式未在复盘中明确——是主观估计还是基于 checklist 的机械加总
- 与 Pine Script 版 Ctx 评分的映射关系（MC 的 "BO/mrk regime -10%" 对应 ctx 的哪个步骤）尚待对照
