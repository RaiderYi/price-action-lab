---
title: "交易日志格式规范"
phase: [trend, range]
signal_types: [h2-entry, l2-entry, pullback-entry]
tags: [min, mes, ptm, 每日复盘, 评分]
difficulty: intermediate
related: [mc-checklist, prior-trading-memory, multi-timeframe-context, trade-management-system, journal-mes-daily-reviews]
char_count: 1189
---
# 交易日志格式规范

## 一句话定义
MES 每日复盘采用的标准化模板：日类型→多TF→MC评分→棒线结构→入场→自我管理，七步完成一次完整复盘。

## 核心要点
- 格式统一：151 份复盘全部使用相同结构，便于跨日期对比
- 时间效率：每份复盘 40-80 行，~5 分钟写完——格式的标准化是效率的关键
- 双语言混合：关键术语用英文（Brooks PA 原术语），注释用中文（个人思考）
- "Best Loser Wins" 结尾：每份复盘的心理锚定——无论盈亏，接受结果

## 七步格式模板

```
1. 日类型判定
   MES 5 Min: [bear/bull] trend [from the open] / trading range all day / ...

2. 多 TF 背景（45min → 15min → 5min）
   [ATR/TR/趋势] 45min → [背景] 15min → [入场TF] 5min
   可选：ATM Straddle ~X%（期权隐含波动参考）

3. 每段走势的 MC 10+2 评分
   对每段 Bn-Bm 序列：
   MC 10+2 [逐项评分] → leg2 XX%

4. 棒线结构标注
   Bn H1/H2/L1/L2/TR/MC/SPB 等结构标签

5. 入场与交易记录
   Bn [信号类型] STP，[入场理由简述]
   [±]nR / BE（结果）

6. PTM 交叉引用（可选）
   PTM[YYYYMMDD]（相似背景引用）

7. 心理锚定
   Best Loser Wins ... by SC2
```

## 与相关概念的关系
- [[mc-checklist]]：MC 评分清单是此格式的核心组件（第3步）
- [[prior-trading-memory]]：PTM 交叉引用是此格式的跨日期链接层（第6步）
- [[multi-timeframe-context]]：多 TF 背景是此格式的第2步
- [[trade-management-system]]：入场记录中的 SPB/BE/STP 操作对应交易管理系统的止损/BE/追踪组件

## 实战应用
开一个 Markdown 模板文件，每天复盘时复制粘贴，逐项填写。7 步写完不超过 5 分钟。周末统计本周的日型分布和交易结果（R 倍数总计）。

## 来源支撑
- [[journal-mes-daily-reviews]]（151 份 MES 每日复盘，全部使用统一格式）

## 矛盾与待验证
- 该格式是否适用于 A 股 T+1 的复盘（vs MES 日内 T+0）——A 股复盘可能需要增加"持仓隔夜评估"步骤
- 格式尚未包含"次日预判"——当前仅做当日回顾，未向前推演
