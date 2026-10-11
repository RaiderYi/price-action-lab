---
title: "ATR 归一化"
phase: [range, breakout, transition]
signal_types: [h2-entry, l2-entry, pullback-entry]
tags: [atr, 实体, 归一化, 标尺, 高潮]
difficulty: intermediate
related: [brooks-signal-catalog, trading-range-quality, tbtl, gravity-field, signal-scoring-synthesis, article-brooks-pa-verification, README-summary]
char_count: 1083
---
# ATR 归一化

## 一句话定义
使用 ATR（平均真实波幅）作为统一标尺，将所有信号的深度、价差、实体阈值归一化为 ATR 倍数。

## 核心要点
- ATR = Average True Range，衡量近期平均波动幅度
- 所有信号阈值均以 ATR 倍数表示，而非绝对价格，从而实现跨品种/跨周期泛化
- 阈值范围因信号类型而异：回调深度从 0.3 ATR（H1）到 5 ATR（H2/L2），高潮K要求 >1.8 ATR

## 阈值速查表

| 参数 | 适用信号 | 阈值 |
|------|---------|------|
| 回调/反弹深度 | H1/L1 | 0.3 ~ 5 ATR |
| 回调/反弹深度 | H2/L2 | 0.5 ~ 5 ATR |
| 双底/双顶价差 | Double Bottom/Top | ≤ 0.5 ATR |
| 高潮K实体 | Post Climax | > 1.8 ATR |
| TR区间宽度 | TR Fade | （通过区间K线数间接约束） |

## 与相关概念的关系
- [[brooks-signal-catalog]]：所有 16 种信号中，至少 10 种直接依赖 ATR 阈值
- [[trading-range-quality]]：TR Fade 不直接用 ATR 约束区间宽度，但区间识别本身依赖波动率
- [[tbtl]]：Post Climax 的高潮K识别依赖 ATR（>1.8 ATR 实体）
- [[gravity-field]]：引力场的距离归一化完全依赖 ATR 标尺（高斯衰减用 ATR14 归一化，2×ATR 截断）
- [[signal-scoring-synthesis]]：lScore/sScore 中「实体 vs 5 均实体」的比较以 ATR 为基准

## 实战应用
在回测和实盘中，ATR 周期通常取 14 或 20 根K线。不同品种/周期应使用**最近 N 根K线的 ATR** 而非固定绝对值，以保证信号的一致性。

## 来源支撑
- [[article-brooks-pa-verification]] §2 各形态对照表
- [[README-summary]]（RS 评分和风控参数涉及 ATR 但未显式标注）

## 矛盾与待验证
- 各阈值的来源：Brooks 原著中有明确的 ATR 倍数建议，还是代码作者根据经验后设的？验证文档未标注每个阈值的来源
- ATR 计算周期（14 vs 20）在当前文档中未明确，可能因品种而异
