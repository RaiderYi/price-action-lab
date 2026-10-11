---
title: "G7 信号可靠性管道（Signal Reliability Pipeline）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, breakout-entry, reversal-entry, failed-breakout]
tags: [layer, atr, lfin, 关闭, tier]
difficulty: intermediate
related: [signal-scoring-synthesis, emergency-exit, fsm-market-cycle, fsm-strategy-constraints, wedge-gravity-dual-core, signal-priority-system, confirmation-bar, article-wedge-gravity-v14-source, article-20260519-wedge-gravity-v41-flowchart, article-huangzongprice-execution-layer-v1]
char_count: 4338
---
# G7 信号可靠性管道（Signal Reliability Pipeline）

## 一句话定义
从 lFin/sFin 达标到最终入场信号之间的 7 层可配置过滤管道——每层独立开关，逐层把关，最下游输出 `longSig`/`shortSig`。

## 核心要点

### 管道全景（7 层，按优先级从高到低）

| 层序 | 名称 | 参数开关 | 默认状态 | 核心逻辑 |
|------|------|---------|---------|---------|
| 1 | **结构优先级** | — | 始终开启 | 楔形 > H2/L2；同时触发时优先楔形，不扩大触发范围 |
| 2 | **趋势/反转分离** | `i_useRevFilter` | 关闭 | 反转信号阈值 +0.10；趋势侧重动量(0.7)/反转侧重位置(0.6) |
| 3 | **确认 K 线** | `i_useConfirm` | 关闭 | 信号延后一根；需下一根突破信号高/低 ≥ 0.6×ATR14 |
| 4 | **失败过滤** | `i_useFailFilter` | 关闭 | 紧急逃生触发 → 硬否决，无例外 |
| 5 | **重叠/置信过滤** | `i_useOlpFilter` | 关闭 | `avgOlp ≤ 0.35` + `fsmConf ≥ 0.55` |
| 6 | **关键位分层** | `i_useKeyFilter` | 关闭 | Tier-1(≤1.0×ATR) / Tier-2(≤0.8×ATR) / 引力场触发 → 放行 |
| 7 | **信号分级** | `i_useGradeFilter` | 关闭 | A(≥0.80)/B(≥0.60)/C(<0.60)，最低等级可配置 |

### 各层详解

#### Layer 1：结构优先级（始终开启）
```pinescript
longStructW = fallingWedge      // 下降楔形 → 多头
longStructH = h2                 // H2 计数 → 多头
longStruct  = longStructW or longStructH
// 冲突时择优（不扩大触发范围）
longStruct  := longStructW and longStructH ? true : longStruct
```
**设计意图**：楔形比 H2/L2 覆盖更长周期，结构级别更高。两者同时触发时，标记为 "WEDGE>H2" 或 "WEDGE>L2"，但 `longStruct` 仍为 `true`——优先级仅影响标签显示和后续评分分配，不扩大触发范围。

#### Layer 2：趋势/反转分离
- `longIsTrend = fsmDir==1`（顺势做多），`shortIsTrend = fsmDir==-1`（顺势做空）
- `longIsRev = fsmDir==-1`（逆势反转做多），`shortIsRev = fsmDir==1`（逆势反转做空）
- **趋势信号**：`extraBonus = (momScore×0.70 + posScore×0.30) × 0.10`——侧重动量
- **反转信号**：`extraBonus = (posScore×0.60 + momScore×0.40) × 0.10`——侧重位置
- 反转可选更高阈值：`lThr = i_sigThr + (i_useRevFilter and longIsRev ? i_revAdd : 0.0)`

#### Layer 3：确认 K 线
信号延后一根 K 线触发，要求确认 K 线的突破幅度达标：
- 做多确认：`close > high[1] + 0.6×ATR14`
- 做空确认：`close < low[1] − 0.6×ATR14`
- `longSig = i_useConfirm ? longSigNow[1] and longConfirm : longSigNow`

**取舍**：牺牲一根 K 线的反应速度，换取更高的入场可靠性。默认关闭（偏好即时信号）。

#### Layer 4：失败过滤（紧急逃生硬否决）
`failFilterOK = not i_useFailFilter or not emergExit`

紧急逃生三种条件之一触发 → 自动否决所有信号（无论多空、无论分数）：
1. 假突破：近 3 根突破 ph0 但收盘回落
2. 实体衰竭：连续 2 根重叠度 > 0.7
3. 竭尽 K 线：实体 ≥ avgBody20×1.5 + 波幅 > ATR14×1.2

#### Layer 5：重叠度 / 置信度过滤
`olpFilterOK = not i_useOlpFilter or (avgOlp ≤ i_olpMax and fsmConf ≥ i_confMin)`

- 高重叠度（`avgOlp > 0.35`）→ 市场混沌，信号不可靠 → 否决
- 低 FSM 置信度（`fsmConf < 0.55`）→ 周期判断不确定 → 否决
- 两项同时达标才放行

#### Layer 6：关键位分层
`keyOK = not i_useKeyFilter or gravOK or nearT1 or nearT2`

| 层级 | 关键位列表 | 距离阈值 |
|------|-----------|---------|
| Tier-1 | 最近 ph0 / pl0 / donchH / donchL | ≤ 1.0×ATR14 |
| Tier-2 | 最近 ph1 / pl1 / EMA20 / fib50 | ≤ 0.8×ATR14 |
| 引力场 | — | `gravOK = gScore > 5.0` |

任一满足即可放行。**设计意图**：信号只有在关键位置附近才有意义——远离所有关键位的随机波动中的信号大概率是噪音。

#### Layer 7：信号分级
```
lGrade = lFin ≥ 0.80 ? "A" : lFin ≥ 0.60 ? "B" : "C"
gradeOKL = not i_useGradeFilter or (lGrade对应的数字等级 ≥ i_gradeMin对应的数字等级)
```
- A = lFin ≥ 0.80（信号极强）
- B = lFin ≥ 0.60（信号可接受）
- C = lFin < 0.60（弱信号）

### 管道下游：综合入场信号
```pinescript
longBase  = longStruct ∧ lFin ≥ lThr ∧ close > midPt ∧ allowLong
longSigNow = longBase ∧ failFilterOK ∧ olpFilterOK ∧ keyOK ∧ gradeOKL
longSig = i_useConfirm ? longSigNow[1] ∧ longConfirm : longSigNow
```

管道之前有 3 个硬前置（结构/分数/中点/周期许可），管道内 7 层逐层过滤，管道出口为最终 `longSig`/`shortSig`。

## 与相关概念的关系

- [[signal-scoring-synthesis]]：本管道是 lFin/sFin 的下游消费者——lFin/sFin 达标后才进入管道
- [[emergency-exit]]：Layer 4 失败过滤器直接消费紧急逃生状态
- [[fsm-market-cycle]]：Layer 2 趋势/反转分离 + Layer 5 置信过滤依赖 FSM 状态
- [[fsm-strategy-constraints]]：管道的硬前置之一 `allowLong/allowShort` 来自 FSM 策略约束
- [[wedge-gravity-dual-core]]：本管道是软评分核（核 B）→ 最终入场信号的最后一段流水线
- [[signal-priority-system]]：V4.1 引入的 5 级信号优先级体系（硬规则→逃生→结构→背景→信号）是对本管道的更高层抽象
- [[confirmation-bar]]：v3 确认 K 线模块——本管道 Layer 3 的独立化版本

## 实战应用

全部 7 层默认关闭时，信号最多（假信号也多）。建议渐进开启：
1. 先开 **Layer 6 关键位分层**——最有效，过滤大量远离关键位的噪音信号
2. 再开 **Layer 4 失败过滤**——紧急逃生否决可靠性最高
3. 最后开 **Layer 7 信号分级 = "B"**——过滤 C 级弱信号

不建议同时开启 Layer 3（确认 K 线）+ Layer 5（重叠过滤）+ Layer 7（分级到 A）——信号过少，可能错失有效入场。

## 来源支撑
- [[article-wedge-gravity-v14-source]]（V1.4 Pine Script 第 63-87 行（G7 参数组定义）+ 第 560-701 行（7 层过滤实现））
- [[article-20260519-wedge-gravity-v41-flowchart]]（V4.1 信号优先级体系——本管道的更高层抽象）
- [[article-huangzongprice-execution-layer-v1]]（执行层 v1 设计稿——确认 K 线 + 分级系统的独立设计）

## 矛盾与待验证
- Layer 5 的 `i_olpMax=0.35` 和 `i_confMin=0.55` 是 V1.4 作者经验值。在极端趋势（重叠度极低）和宽幅震荡（重叠度自然高）市场中，固定阈值可能分别过于宽松或过于严格。
- Layer 6 的 Tier-1/Tier-2 距离阈值（1.0×ATR / 0.8×ATR）针对不同波动率市场可能需要调整——高波动市场信号很少落在 1.0×ATR 内。
- V1.4 的 G7 管道全默认关闭，后续版本（V4.1/V5.0）逐步将某些层内嵌或默认开启——这是设计哲学从「用户自主」到「系统推荐」的演进，未见对比数据支撑哪种更好。
