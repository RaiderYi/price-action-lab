---
title: "MC 每日评分系统"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, swing]
tags: [leg, 加分, 提取, huangzongprice, brooks]
difficulty: intermediate
related: [micro-channels, trend-strength-filter, ctx-scoring, h2-l2-state-machine, journal-huangzongprice-mes-review-collection]
char_count: 1635
---
# MC 每日评分系统

## 一句话定义
huangzongprice 将 Brooks 微通道理论落地为可操作的 10+2 项加权评分清单，用于每日复盘中对每个微通道进行系统质量评估。

## 核心要点
- MC（Micro Channel）评分是 huangzongprice 复盘系统的核心组件，每份复盘对当日出现的每个微通道执行独立评分
- 评分格式为 `MC 10+2`：10 项基础维度 + 2 项额外维度，每项赋予正负百分比权重
- 评分项覆盖：K 线质量、前后背景、市场阶段、时间/价格控制、趋势强度
- 目的：将 Brooks "这个通道看起来强/弱" 的定性判断转化为可量化的多维度评估
- 负分项（扣分）= 减弱通道可靠性的因素；正分项（加分）= 增强通道可靠性的因素

## MC 10+2 评分维度（从复盘中提取）

### 基础维度（10 项）

| 维度 | 典型权重 | 含义 |
|------|---------|------|
| K 线质量 | -5% | 通道内 K 线是否有影线、是否为 doji |
| C prior H/L | -5% | 收盘价是否突破前高/前低 |
| 前值延续 | -5% | 是否延续前一棒的方向 |
| doji | -5%~-10% | 通道内是否出现十字星（削弱趋势强度） |
| tick gap | -5% | 是否存在跳价缺口 |
| BO / mrk regime | -10%~-20% | 当前市场阶段——突破 vs 交易区间（TR 阶段大幅扣分） |
| late leg | +5% | 通道是否出现在趋势晚期（加分——晚期通道往往是衰竭信号） |
| price control / swing point | +5% | 是否有明确的波段点价格控制 |
| 1ABR | +5% | 通道幅度是否达到 1 个 ATR 的合理范围 |
| time control / leg2 | +5%~+65% | 通道在时间维度上是否充分——leg2 比 leg1 时间更充分则大幅加分 |

### 额外维度（2 项）
具体内容因 PDF 图表损毁未能完整提取，推测为：
- 通道斜率/角度
- 通道内棒线数量

### 评分汇总
- 最终得分 = 基础分（各项加权求和）→ 用于判断该 MC 作为入场/持仓依据的可靠程度
- 高评分 MC 配合 H1/H2/L1/L2 信号时具有更高的执行优先级

## 与相关概念的关系
- [[micro-channels]]：Brooks 的理论定义——MC 是理论，MC 评分是将理论量化为操作清单
- [[trend-strength-filter]]：v3 趋势强度过滤的四维评估——MC 评分是其最细粒度的实战版本
- [[ctx-scoring]]：Ctx 上下文评分——MC 评分是上下文评分在微通道维度的专项深化
- [[h2-l2-state-machine|H2/L2 State Machine]]：H2/L2 状态机——MC 评分直接为 H2/L2 入场提供背景质量依据

## 实战应用
在每份 MES 复盘中对当日出现的每个微通道块执行 10+2 评分，高分 MC 标记为可靠入场区，低分 MC 标记为谨慎区或跳过区。

## 来源支撑
- [[journal-huangzongprice-mes-review-collection]]

## 矛盾与待验证
- 各项评分的精确权重公式因 PDF 图表损毁未能完整提取，需要 huangzongprice 本人确认或从原始 PDF 图表中手动提取
- MC 评分与 [[ctx-scoring]] 的权重分配是否有重叠/冲突——两者的 Step1（S/R 检测）和 MC 评分中的 "price control / swing point" 维度存在交叉
