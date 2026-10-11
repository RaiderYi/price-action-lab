---
title: "背景否决（Background Veto）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, wedge, failed-breakout]
tags: [veto, and, bgvetolong, 逻辑, 禁止原因]
difficulty: intermediate
related: [background-scoring-engine, emergency-exit, momentum-health, phase-transition-detection, late-breakout, signal-priority-system, article-20260520-wedge-gravity-brooks-context-v3]
char_count: 3558
---
# 背景否决（Background Veto）

## 一句话定义
WG Brooks V3 背景裁决层中的绝对禁止机制——四条硬规则，任何一条命中即 bgVeto=true，覆盖所有其他信号，即使信号棒满分也不允许入场。

## 核心要点

### 四条否决条件（源码精确版）

#### Veto #1：区间中部 + 震荡区间
```
bgVetoLong = midRangeLocation AND phaseIsRange
```
- **逻辑**：价格在区间正中央 + 市场处于震荡——最差的位置 + 最不确定的环境
- 「区间中部」= 距 Donchian 中线 ≤ 区间宽 × 20% 且 距支撑/阻力均 > 1.0 ATR
- 「震荡区间」= FSM 状态=Range（phaseState==2）
- **禁止原因**：中部没有任何 S/R 参照，纯随机区域，无法判断方向

#### Veto #2：健康趋势 + 方向相反（且无反转结构支撑）
```
bgVetoLong = phaseDir == -1 AND phaseTrendHealthy
             AND exhaustRiskS < 0.55
             AND NOT fallingWedge AND NOT h2
```
- **逻辑**：市场处于健康的空头趋势中做多（或无楔形/H2 反转结构）
- `phaseTrendHealthy` = 趋势态（phaseIsTrend）且 置信度≥0.70 且 EMA 陡峭 且 重叠度<0.24 且 非过渡
- `exhaustRiskS < 0.55`：空头衰竭风险不高——空头还很健康，不应逆势做多
- `NOT fallingWedge AND NOT h2`：没有下降楔形或 H2 反转结构——缺乏反转理由
- **禁止原因**：健康趋势中逆势交易 = 接飞刀

#### Veto #3：贴近对向 S/R + 追价突破
```
bgVetoLong = atBearResistance AND lateBreakoutLong
```
- **逻辑**：贴近空头阻力位 + 正在追多突破——价格已到阻力且入场已晚
- `atBearResistance`：距最近阻力（ph0/DonchianH/EMA/Fib50）≤ 0.60 ATR
- `lateBreakoutLong`：已明显脱离旧 Donchian 上轨（>0.60 ATR）且远离支撑、贴近阻力
- **禁止原因**：在阻力位追多 = 入场即面临双重不利（位置差 + 时机差）

#### Veto #4：高成熟度/高衰竭 + 当前腿转弱 + 追价突破（三重叠加）
```
bgVetoLong = (trendMaturityL ≥ 0.65 OR exhaustRiskL ≥ 0.60)
             AND currentLegWeakeningL ≥ 0.50
             AND lateBreakoutLong
```
- **逻辑**：趋势已老/衰竭 + 动能正在减速 + 还在追价——三重负面叠加
- `trendMaturityL ≥ 0.65`：楔形+追价+衰竭棒+目标临近 → 趋势已高度成熟
- `exhaustRiskL ≥ 0.60`：逃生+楔形+高重叠度+目标临近 → 衰竭风险极高
- `currentLegWeakeningL ≥ 0.50`：冲击力递减+高重叠度+EMA走平+楔形 → 当前腿明显减速
- **禁止原因**：这是"所有最坏情况同时发生"的场景

### 否决 vs 冲突 vs 支持 的关系

```
                          bgScore ≥ 0.58?
                        /              \
                      YES               NO
                     /                    \
              检查 bgVeto?            检查 bgConflict?
             /          \            /              \
           NO           YES         NO              YES
           |             |           |               |
      bgSupport      bgVeto     bgSupport       bgConflict
      (允许入场)    (禁止入场)   (允许入场)      (不推荐入场)
```

- **否决 > 支持**：即使 bgScore 很高（≥0.72，BULL_STRONG），否决条件命中直接禁止
- **否决 ≠ 冲突**：冲突是"不太确定"（bgScore 0.42-0.58 之间或有对立证据），否决定是"绝对不行"
- 否决条件在代码中检查顺序：先检查否决、再检查冲突、最后判断支持

### 否决与紧急逃生的区别

| 维度 | 背景否决 (bgVeto) | 紧急逃生 (emergExit) |
|------|------------------|---------------------|
| 层级 | 背景裁决层（第 4 层） | 预警层（第 0 层，先于背景） |
| 作用 | 禁止入场 | 预警退出 + 扣减趋势健康分 |
| 触发方式 | 4 条组合逻辑规则 | 3 种单根 K 线信号（假突破/衰竭/竭尽） |
| 持续时间 | 每根 K 线独立判定 | 瞬态（仅触发根前后） |
| 对持仓影响 | 不影响已有持仓 | 建议检查/退出 |

## 与相关概念的关系
- [[background-scoring-engine]]：否决是该引擎的最终输出——bgScore 计算完成后，否决条件做最后一次过滤
- [[emergency-exit]]：紧急逃生是否决的输入信号之一（Veto #4 的 exhaustRisk 因子）
- [[momentum-health]]：Veto #4 的三个条件全部来自动量健康度子系统（trendMaturity/exhaustRisk/currentLegWeakening）
- [[phase-transition-detection]]：Veto #2 使用 phaseTrendHealthy 判定——过渡态中趋势不健康，Veto #2 不触发
- [[late-breakout]]：Veto #3 和 #4 都依赖追价判定
- [[signal-priority-system]]：否决是该系统"硬规则"层的一部分——优先级高于所有软评分

## 实战应用
- 信息面板「背景否决」行：任一方否决时以紫红色高亮显示 → **最醒目的禁止信号**
- `bgVetoLong` = true 时，即使 `h2` 或 `fallingWedge` 触发，`longSigNow` 仍为 false（代码行 808：`longSigNow = longCandidate AND bgSupportLong AND NOT bgVetoLong`）
- Veto #2 是量化系统中「顺势为王」的终极体现——健康趋势中逆势 = 直接否决

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 完整 Pine Script 源码，第 737-745 行）

## 矛盾与待验证
- Veto #2 的 `exhaustRiskS < 0.55` 阈值：为什么是 0.55 而非与 bgThr（0.58）对齐？源码中未见说明
- Veto #4 的三重条件使用 AND 连接——如果仅满足 maturity≥0.65 和 lateBreakoutLong 但 legWeakening < 0.50，不否决。这可能是合理的（"趋势老但还没减速"），但从未经验证
- 否决条件未区分"做多否决"和"做空否决"的严重程度——Veto #2 在强多头趋势中做空的风险理论上应与强空头趋势中做多对称，但代码中使用的阈值完全相同
