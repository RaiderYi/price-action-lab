---
title: "MC 10+2 架构评分系统"
phase: [trend, range, breakout, transition]
signal_types: []
tags: [abr, 市场阶段, 价格控制, ctx, 缺口]
difficulty: intermediate
related: [ctx-scoring, brooks-signal-catalog, signal-scoring-synthesis, trend-strength-filter, climax, trading-range-quality, journal-mes-daily-review-collection]
char_count: 1113
---
# MC 10+2 架构评分系统

## 一句话定义
huangzongprice 用于评估单个交易架构质量的 12 因子评分体系，K线形态/棒位/缺口/市场阶段/价格控制/ABR/时间/腿2比例各占权重。

## 核心要点
- **评分范围**：每项 -5% ~ +5%，关键项 -20%
- **12 因子**：K线(±5%)、Cprior L/H(±5%)、重叠度(±5%)、Doji(±5%)、Tick gap(±5%)、BO/市场阶段(-10%~-20%)、价格控制(+5%)、主要摆动点(+5%)、ABR(+5%)、时间控制(+5%)、腿2比例(+5%)
- **负面因子**：晚腿(-20%) > BO 中市场阶段(-10%) > 其他(-5%)
- **正面因子**：价格控制 = 摆动点 = ABR = 时间控制 = 腿2比例 = +5%
- **典型阈值**：总分 < -30% 为弱势架构，> +15% 为强势架构

## 与相关概念的关系
- [[ctx-scoring]]：ctx 是宏观背景评分，MC 10+2 是微观架构评分——ctx 通过后的"入场确认层"
- [[brooks-signal-catalog]]：MC 10+2 为信号目录中的每个信号提供量化评估标准
- [[signal-scoring-synthesis]]：lFin/sFin 评分位于更高抽象层，MC 10+2 是可作为其输入的子评分
- [[trend-strength-filter]]：MC 10+2 的趋势相关因子（BO/市场阶段/晚腿）与趋势过滤重叠
- [[climax]]：遇到高潮棒时 MC 10+2 自动给 BO 和晚腿打负分
- [[trading-range-quality]]：TTR 判定标准与 MC 10+2 的重叠度和 K 线形态因子互补

## 实战应用
对每个候选入场架构跑一遍 12 项清单：K线强弱→收盘位置→重叠→Doji→缺口→BO阶段→谁控盘→摆动点→ABR→时间→腿2%。总分过低则否决入场。

## 来源支撑
- [[journal-mes-daily-review-collection]]（约 100 个复盘文件中反复使用）
- 首次完整出现：MES20260305 复盘

## 矛盾与待验证
- MC 10+2 的精确权重（尤其是负面因子之间的相对重要性）未经回测验证
- 各因子的评分阈值（如 ABR 多少算 +5% vs +0%）在复盘中未明确公开
- 与 [[ctx-scoring]] 的联动规则（ctx 通过后 MC 10+2 的最低通过分）尚未定义
