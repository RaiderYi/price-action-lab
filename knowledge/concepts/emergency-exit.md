---
title: "紧急逃生（EmergExit）"
phase: [trend, range, breakout, transition]
signal_types: [wedge, failed-breakout]
tags: [emergexit, step, and, 紧急逃生, 假突破]
difficulty: intermediate
related: [fsm-market-cycle, signal-scoring-synthesis, wedge-gravity-dual-core, bar-close-position, article-20260520-wedge-gravity-brooks-context-v3, article-wg-v15-analysis, article-20260519-wedge-gravity-brooks-v1-pine, article-20260519-wedge-gravity-v41-flowchart, article-20250519-brooks-context-4-pine, article-wedge-gravity-v14-source, article-huangzongprice-context-engine-v3-rebuild]
char_count: 2221
---
# 紧急逃生（EmergExit）

## 一句话定义
三种条件任满足其一即触发紧急逃生标记，用于可选硬过滤和 Brooks Step4 否决——防止假突破、双根高重叠、极端波动场景下入场。

## 核心要点
- **三种触发条件**（三选一即 `emergExit`）：
  1. **假突破**：近几根曾上破 `ph0` 但收盘跌回其下
  2. **双根高重叠**：相邻两根实体高度重叠（相对实体幅度）
  3. **大实体+大振幅**：实体相对 20 均实体大，且振幅相对 ATR 大
- **用途**：
  - `failFilterOK` 可选硬过滤
  - Brooks Step3 评分参考
  - Brooks Step4 否决（逃生+顺势结构否决）

## 与相关概念的关系
- [[fsm-market-cycle]]：紧急逃生与 FSM 方向许可共同构成信号否决层
- [[signal-scoring-synthesis]]：紧急逃生不影响分数，在分数达标后的过滤层起作用
- [[wedge-gravity-dual-core]]：紧急逃生是双核架构之外的另一层安全网
- [[bar-close-position]]：假突破检测依赖收盘位置的回归（上破 ph0 但收盘跌回）

## 实战应用
emergExit 触发时，即使分数达标、FSM 许可，信号也可能被否决。特别在 Brooks Step4 `i_vetoEmergTrend` 开启时：逃生 + 顺势结构 → 入场被否决。

## V1.5.2 源码实现细节（来自 Pine Script，第 684–719 行）

**三种触发的精确条件**：

1. **假突破** `brkFail_EMG`：`not na(ph0) and (high[3]>ph0 or high[2]>ph0 or high[1]>ph0) and close < ph0`——最近 3 根任意一根上破最近高点但收盘跌回
2. **双根实体衰竭** `exhBars`：相邻两根的重叠度相对各自实体比例均 > 0.7——`(ol01/mb01)>0.7 and (ol12/mb12)>0.7`
3. **竭尽K线** `exhCdl`：`实体 ≥ 20均实体×1.5 AND 振幅 > ATR14×1.2`

**双重角色**：
- **Step3 压低 ctx3_score**：emergExit 时 `emergPart = 0.0`（否则 0.26）——直接扣掉 26% 的动能分
- **Step4 否决**：`i_vetoEmergTrend and emergExit and longIsTrend and longBase`——逃生+顺势=禁止追价

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：三种逃生触发条件精确公式 + 对趋势健康(-0.20)和衰竭风险(+0.40)的量化影响）
- [[article-wg-v15-analysis]]
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — **Pine Script 源码**，揭示了三种触发的精确阈值和 emergPart=0.26 的权重细节
- [[article-20260519-wedge-gravity-v41-flowchart]]（三种预警精确触发条件：假突破=最近3K破ph0但close<ph0、实体衰竭=连续2K重叠>70%、竭尽K线=实体≥1.5×20均实体+波动>1.2×ATR14）
- [[article-20250519-brooks-context-4-pine]]（Step3 动能衰竭检测 + Step4 否决中 emergExit 的双重角色：压低 ctx3_score + 触发 vetoEmergL/S）
- [[article-wedge-gravity-v14-source]]（V1.4 源码第575-599行——三种紧急逃生的精确判定：brkFail_EMG 假突破 / exhBars 实体衰竭 / exhCdl 竭尽K线）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 源码第401-417行——三种紧急逃生条件完整代码，含emergNew边缘检测用于plotchar标记）

## 矛盾与待验证
- 三种条件的阈值（"近几根"、"高度重叠"、"大"的定义）均为经验参数。假突破检测仅看收盘跌回，未考虑后续 K 线是否重新收复——可能漏掉"刺探后真突破"。

## V6 一票否决 vs 紧急逃生

V6 的是紧急逃生概念的升级：
- emergExit 覆盖 3 种微观 K 线异常（假突破/衰竭/竭尽）
- V6 一票否决覆盖 6 种阶段×位置组合（4否决+2绿灯）
- emergExit 压低评分（−26% ctx3），V6 一票否决是独立二元闸门
- 两者的交集：「假突破」与「贴近S/R」在实际中常同时触发——V6 能将两者合并为一个阶段×位置的精确文本而非两个独立标记
