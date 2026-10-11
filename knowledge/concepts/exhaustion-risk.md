---
title: "衰竭风险 (Exhaustion Risk)"
phase: [trend, range, breakout, transition]
signal_types: [wedge, failed-breakout]
tags: [衰竭风险, 突破失败, brkfail, emg, 高重叠率]
difficulty: intermediate
related: [trend-maturity, exhaustion-risk, failed-breakout-reversal, climax, buy-vacuum-sell-vacuum, emergency-exit, article-huangzongprice-context-engine-v2, article-20250519-brooks-pa-execution-engine-v1]
char_count: 1585
---
# 衰竭风险 (Exhaustion Risk)

## 一句话定义
量化当前趋势被反向力量"耗尽"的风险——突破失败、楔形、高重叠率、目标接近四因子合成。

## 核心要点
- 衰竭风险是执行引擎 v1 中**动量评分（momScore）**的扣分项，与 [[trend-maturity]] 互补
- 四个子因子加权合成：
  - **突破失败**（0.40）：价格突破前高但收盘跌回（brkFail_EMG）——最重的扣分
  - **楔形出现**（0.25）：上升楔形→多头衰竭；下降楔形→空头衰竭
  - **高重叠率**（0.15）：avgOlp > 0.35，表明市场失去方向性
  - **目标接近**（0.20）：价格接近反向目标区→获利盘涌出
- 输出为 0~1 的归一化分数，clamp01
- 衰竭风险 ≥ 0.60 且目标接近时，触发**背景否决**（bgVeto）

## 与相关概念的关系
- [[trend-maturity]]：紧密互补——成熟度看"走了多久"，衰竭风险看"是否被耗尽"
- [[exhaustion-risk]] 中的 `brkFail_EMG` 与 Brooks 的 [[failed-breakout-reversal]] 直接对应
- [[climax]]：高潮中的衰竭K线（exhCdl）是衰竭风险的一个触发因子
- [[buy-vacuum-sell-vacuum]]：买卖真空引发剧烈反向——衰竭风险的物理机制解释
- [[emergency-exit]]：紧急逃生中的假突破检测与本概念的突破失败检测有重叠（但 v1 的紧急逃生机制更简单）

## 实战应用
突破前高后收盘跌回（brkFail）→ 楔形三推到位 → 重叠率飙升 → 价格接近目标 → 四个条件叠加时，衰竭风险极高，不建议顺势入场。

## 评分公式

**exhaustRiskL**（多头衰竭风险）：
```
= clamp01(
    brkFail_EMG ? 0.40 : 0.0        // 突破失败（最重）
  + risingWedgeBg ? 0.25 : 0.0      // 上升楔形
  + avgOlp > 0.35 ? 0.15 : 0.0      // 高重叠率
  + bullTargetNearby ? 0.20 : 0.0   // 目标接近
  )
```

**exhaustRiskS**（空头衰竭风险）：
```
= clamp01(
    brkFail_EMG ? 0.40 : 0.0        // 突破失败（最重）
  + fallingWedgeBg ? 0.25 : 0.0     // 下降楔形
  + avgOlp > 0.35 ? 0.15 : 0.0      // 高重叠率
  + bearTargetNearby ? 0.20 : 0.0   // 目标接近
  )
```

## 来源支撑
- [[article-huangzongprice-context-engine-v2]]（v2 Context Engine 实现 exhaustRisk 四因子评分源码）
- [[article-20250519-brooks-pa-execution-engine-v1]]（v1 执行引擎首次引入衰竭风险评估，但评分公式未公开）

## 矛盾与待验证
- 衰竭风险评分仅出现在 v1 中，v3 和 V1.5 无此维度
- 突破失败（brkFail_EMG）的检测窗口为 3 根K线（high[1]/high[2]/high[3]），此参数未经敏感性测试
- 权重分配（0.40/0.25/0.15/0.20）是否与回测结果匹配——未公开
