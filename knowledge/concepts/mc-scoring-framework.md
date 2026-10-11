---
title: "MC 微通道评分框架"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry, swing]
tags: [climax, regime, 评估, 评分评估, mes]
difficulty: intermediate
related: [ctx-scoring, signal-scoring-synthesis, momentum-health, trend-weakening-sequence, climax, micro-channels, journal-mes-review-collection]
char_count: 1309
---
# MC 微通道评分框架

## 一句话定义
将一段微通道（MC）的每根K棒按 11 项加权因子逐一打分，累计评估该段微通道的健康度、成熟度和反转概率。

## 核心要点
- **触发条件**：一段微通道至少包含 10 根 K 线（MC10+），加额外 2 根确认棒
- **评分范围**：从 -65%（最弱）到 +20%（最强），典型范围 -20%~+5%
- **核心洞见**：MC=Climax=TR —— 当微通道累计扣分过多时，它本身就是高潮，预期转为交易区间
- **评分维度（11项）**：
  - K棒形态 (-5%)：非趋势棒
  - 前收盘vs收盘不利 (-5%)
  - Doji/十字星 (-5% ~ -20%)：根据严重程度
  - 无tick gap (-5%)：无跳空=动能不足
  - BO标记/Regime不利 (-10%)：当前Regime与信号方向冲突
  - Late Leg (-20%)：已走完多腿，延迟入场
  - 价格控制 +5%：swing point 在 1ABR 范围内
  - 时间控制 +5%：走势持续时间达标
  - MC类型标签（定性，非数值）：climax/climactic reversal/TR/wedge

## 与相关概念的关系
- [[ctx-scoring]]：ctx-scoring 评估「大背景」（价位/阶段/动能/否决），MC评分评估「微结构」（当前这一段通道的健康度），两者一个宏观一个微观
- [[signal-scoring-synthesis]]：信号评分评估「入场质量」，MC评分评估「通道健康度」，健康度低的通道中即使信号好也应降权
- [[momentum-health]]：都是评估动能的框架，MC评分更偏逐棒计数，动能健康框架更偏统计特征
- [[trend-weakening-sequence]]：MC评分可视为趋势减弱序列的**量化落地**——12项减弱征兆对应MC评分的11项扣分因子
- [[climax]]：MC评分直接产出「MC=Climax」的判定，与Brooks高潮理论形成量化-理论对照
- [[micro-channels]]：微通道是MC评分的分析对象（≥6根连续无回调K线），MC评分是分析工具

## 实战应用
在图表上：找到一段连续10+根K线的单向走势 → 逐棒检查11项因子 → 累计评分。如果总分<-30%且出现「MC=Climax=TR」标签 → 预期该段走势即将反转或进入区间，准备反向入场或观望。

## 来源支撑
- [[journal-mes-review-collection]]（40+份MES复盘中系统化使用）

## 矛盾与待验证
- 评分权重是否最优：当前权重来自 huangzongprice 的实战经验，未经过统计回测验证
- 与 [[ctx-scoring]] 的权重可能有重叠（如 "BO mark regime" 在两层评分中均有），组合使用时需注意避免双重惩罚
- MC评分目前仅见于 MES 5min 复盘，是否适用于其他品种/时间框架需要验证
