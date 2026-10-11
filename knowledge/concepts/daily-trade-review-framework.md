---
title: "每日交易复盘框架"
phase: [trend, range, transition]
signal_types: []
tags: [min, 评分, 一句话日, 标注, 复盘中的]
difficulty: intermediate
related: [brooks-four-step-context, ctx-scoring, trade-management-system, climax, live-trading-monitor, review-huangzongprice-mes-daily-reviews]
char_count: 1144
---
# 每日交易复盘框架

## 一句话定义
收盘后对当日交易进行多周期标注+MC评分+执行回顾的结构化复盘方法论。

## 核心要点
- **一句话日概**：复盘第一步——用一句话定义当日市场类型（开盘趋势/趋势恢复/TR反转/MTR等），确定主导叙事
- **多周期标注**：自上而下（45min→5min→1min），逐级标注关键价位、主要摆动点、EMA位置、通道线
- **MC 评分**：对每段行情标注 Market Context 评分（10+2 项目，含 ±% 调节），量化每笔交易的背景质量
- **交易执行记录**：逐笔标注入场方式（STP/O/B）、出场（STC/STB）、目标管理（BE/1R/2R/3R/4R）、追踪止损触发
- **来源引用**：标注 Brooks 交易课程参考视频号（如 14E/29B）和 PTM（Prior Trading Memory）日期，连接理论与实战

## 与相关概念的关系
- [[brooks-four-step-context]]：复盘中的"一句话日概 + MC评分"是 Brooks 四步上下文在盘后的落地应用
- [[ctx-scoring]]：MC10+2 评分是 ctx 评分系统的实战版本，复盘中的 % 调节项提供了 Pine Script 中未公开的校准参考
- [[trade-management-system]]：复盘中的 STP/BE/1R/2R 注记是交易管理系统的实战执行记录
- [[climax]]：复盘中频繁标注 cxbar（高潮棒），验证了高潮识别在实战中的高优先级
- [[live-trading-monitor]]：复盘笔记是 live-trading-monitor 的离线文本版——前者是实时"看什么"，后者是盘后"记什么"

## 实战应用
每日收盘后，按以下步骤执行：① 写出当日一句话日概；② 在 45min/5min/1min 三周期图表上标注关键结构；③ 对每段可交易行情标注 MC 评分；④ 记录每笔实际交易的入场/出场/目标管理；⑤ 标注 Brooks 课程参考和 PTM 历史记忆索引。

## 来源支撑
- [[review-huangzongprice-mes-daily-reviews]]（52 篇 MES 每日复盘原始笔记）

## 矛盾与待验证
- 复盘框架与量化系统（WG V1.5/V3）的"双轨制"关系尚未在 Wiki 中系统化对比——人工定性判断与代码量化信号如何互补/冲突？
- MC10+2 评分的 % 调节值（如 `-5%K`, `+5% price control`）在 Pine Script 中是否有对应的权重参数，还是纯粹的人工商量？
