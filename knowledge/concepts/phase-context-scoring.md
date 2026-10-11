---
title: "阶段评分（Phase Context Scoring）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge]
tags: [phasescorel, phasedir, phl, trendhealthy, trendweakening]
difficulty: intermediate
related: [transition-detection-system, fsm-market-cycle, wedge-gravity-dual-core, momentum-health, background-permission, execution-scoring, article-huangzongprice-wg-brooks-context-v3]
char_count: 3292
---
# 阶段评分（Phase Context Scoring）

## 一句话定义
v3 背景引擎第二层的阶段打分系统——基于 FSM 趋势方向、过渡证据计数和阶段健康分类，量化「市场处于什么阶段」对做多/做空的有利程度。

## 核心要点
- **输出两个独立分**：`phaseScoreL`（做多阶段分）和 `phaseScoreS`（做空阶段分），各自 0-1
- **基础分**：双方均从 0.08 起步（阶段层的基础置信度低于位置层的 0.10——阶段判断难度更高）
- **阶段健康三级分类**决定加分幅度：
  - **TrendHealthy**（趋势健康）：顺势 +0.52
  - **TrendWeakening**（趋势减弱）：顺势 +0.30
  - **Trend/Other**（普趋势）：顺势 +0.20
- **逆势让步**：当 phaseDir 反向但出现反转结构信号（楔形/H2/接近支撑阻力）时，逆势方可获得 +0.22 让步分
- **区间交易**：phaseIsRange 且靠近边界时 +0.36（0.24 基础 + 0.12 边界加成）
- **两面惩罚**：phaseTwoSided 且不靠近边界时 -0.14（两可环境降低方向置信度）
- **强逆势抵消**：对方趋势健康时，本方 -0.26（最强的方向压制）

## 评分公式

### 做多阶段分（phaseScoreL）
```
phL = 0.08
if phaseDir == 1（多头趋势）:
    phL += TrendHealthy  ? 0.52 
         : TrendWeakening ? 0.30 
         : 0.20（普趋势）
elif phaseDir == -1（空头趋势）:
    phL += TrendWeakening & (fallingWedge | H2 | nearBullSupport) ? 0.22 : 0.02
else（中性 phaseDir==0）:
    phL += phaseIsRange & nearBullSupport ? 0.24 : 0.10

phL += phaseIsRange & nearBullSupport ? 0.12 : 0.0   // 区间边界加成
phL -= phaseTwoSided & !nearBullSupport ? 0.14 : 0.0  // 两面惩罚
phL -= phaseDir==-1 & TrendHealthy ? 0.26 : 0.0       // 强逆势抵消
phaseScoreL = clamp01(phL)
```

### 做空阶段分（phaseScoreS）
镜像逻辑——phaseDir 方向对调，支撑/阻力对调，risingWedge/fallingWedge 对调，H2/L2 对调。

## 阶段健康分类判定

阶段健康由 FSM 状态、过渡证据和 EMA/重叠度组合判定：

| 分类 | 条件 |
|------|------|
| **TrendHealthy**（趋势健康） | phaseIsTrend & confidence ≥ 0.70 & emaSteep & avgOlp < 0.24 & !phaseIsTransition |
| **TrendWeakening**（趋势减弱） | phaseIsTrend & transitionCount ≥ 1 & (avgOlp > 0.24 | !emaSteep) |
| **TwoSided**（双向市场） | phaseIsRange | phaseIsTransition | avgOlp > 0.35 |

TrendHealthy 必须同时满足四个条件——缺一即降级，体现了「趋势健康是稀缺状态」的设计哲学。

## 过渡检测（transitionCount）

5 种独立证据，由 [[transition-detection-system]] 详细记录：

1. **transitionByOverlap**：avgOlp > 0.32（高重叠度 → 方向性丧失）
2. **transitionBySlopeLoss**：!emaSteep | emaFlat（EMA 斜率丧失或走平）
3. **transitionByBroadChannel**：phaseState==1 & avgOlp > 0.24 & confidence < 0.72
4. **transitionByWedge**：risingWedge | fallingWedge（楔形 = 趋势末段信号）
5. **transitionByFailedBreakout**：brkFail_EMG | emergExit

`phaseIsTransition = transitionCount ≥ 2`——至少 2 项证据才判定为过渡态，防止单一假信号误判。

## 阶段分在背景裁决中的位置

```
bgScoreL = locScoreL × 0.40 + phaseScoreL × 0.35 + momScoreL × 0.25
```

阶段层权重 35%，介于位置（40%）和动能（25%）之间。阶段判断的「顺势加分 + 逆势惩罚」是背景裁决的核心方向锚定机制——在位置好但方向不对的情况下，阶段分可以大幅拉低 bgScore。

## 与相关概念的关系
- [[fsm-market-cycle]]：FSM 输出的 phaseState/phaseDir/phaseConfidence 是阶段健康分类的核心输入
- [[transition-detection-system]]：5 证据 → transitionCount → phaseIsTransition 的完整链路
- [[wedge-gravity-dual-core]]：阶段层是三层引擎的第二层（35% 权重）
- [[momentum-health]]：动能层的 TrendHealthy/TrendWeakening 是从阶段层借用的概念
- [[background-permission]]：阶段层的 phaseTwoSided 和 TrendHealthy 影响否决条件（强趋势逆势否决）
- [[execution-scoring]]：阶段分间接影响执行评分——bgScore 含 35% 阶段权重

## 实战应用
- **phaseScoreL ≥ 0.70**：多头趋势健康，EMA 陡峭，低重叠，无过渡信号——顺势做多的最佳阶段
- **phaseScoreL ≈ 0.30-0.40**：过渡态中靠近支撑区域——反转交易的机会窗口
- **phaseScoreL < 0.10**：空头趋势健康中的做多——背景强烈不支持，应避免
- 阶段分的最大杀手是「对方趋势健康」（-0.26）——比任何单一加分项都重

## 来源支撑
- [[article-huangzongprice-wg-brooks-context-v3]]（V3.0 源码——首次公开 phaseScoreL/S 完整计算公式）

## 矛盾与待验证
- 逆势让步 +0.22 的条件要求 `TrendWeakening & (楔形/H2/近支撑)`——三个条件缺一即降至 +0.02，这 20 倍的差距是否过于陡峭？
- phaseDir==0（中性）时的阶段分 = 0.18（区间近边界）或 0.10（其他），极低的基础分是否导致中性市场被过度压制？
- phaseIsRange & nearBullSupport → +0.36（0.24+0.12）——区间上沿做多仍能拿到 0.36 分，这可能在下跌趋势中的区间反弹时产生误导。
