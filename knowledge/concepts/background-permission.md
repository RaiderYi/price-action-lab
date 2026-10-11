---
title: "背景许可层"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, failed-breakout]
tags: [phasedir, 许可, 执行引擎, allowlong, allowreversallong]
difficulty: intermediate
related: [execution-layer, fsm-market-cycle, h2-l2-state-machine, three-push-wedge, article-huangzongprice-execution-layer-v1, wedge-gravity-dual-core, execution-scoring, emergency-exit, trend-maturity, exhaustion-risk, article-20250519-brooks-pa-execution-engine-v1, article-huangzongprice-wg-brooks-context-v3, execution-engine-architecture, linkage-failure-safety, confluence-trading, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-context-execution-linkage-setup, book-huangzongprice-context-analysis-steps]
char_count: 6234
---
# 背景许可层

## 一句话定义
执行层入口——将背景层的多维度方向判断翻译为布尔许可变量，拆分顺势许可（H2/L2 用）和反转许可（楔形用），确保不同结构类型匹配正确的环境前提。

## 核心要点
- **输入端**（来自背景层）：`bgSupportLong/Short`、`bgVetoLong/Short`、`phaseDir`、`phaseIsTrend/Range/Transition`、`locScore`、`momScore`
- **基础许可**：`allowLong = bgSupportLong AND NOT bgVetoLong`（空头镜像）
- **顺势许可**（用于 H2/L2）：`allowTrendLong = allowLong AND phaseDir == 1`（仅在多头阶段才允许顺势做多）
- **反转许可**（用于楔形）：`allowReversalLong = allowLong AND (phaseDir == -1 OR phaseIsTransition OR phaseIsRange)`（仅在空头/过渡/区间阶段才允许反转做多）
- **设计原理**：H2/L2 的核心环境是顺势（趋势中再进入），楔形的核心环境是衰竭反转（趋势末端/过渡阶段），因此背景许可必须拆分，否则会混乱
- **输出变量**：`allowLong`、`allowShort`、`allowTrendLong`、`allowTrendShort`、`allowReversalLong`、`allowReversalShort`

## 与相关概念的关系
- [[execution-layer]]：背景许可层是执行层的入口模块（模块 A）
- [[fsm-market-cycle]]：提供 `bgSupport/Veto`、`phaseDir`、`phaseState` 等上游变量
- [[h2-l2-state-machine|H2/L2 State Machine]]：消费 `allowTrend` 许可——H2 候选 = h2 AND allowTrendLong
- [[three-push-wedge|Three Push Wedge]]：消费 `allowReversal` 许可——做多楔形候选 = fallingWedge AND allowReversalLong

## 实战应用
在编码时，背景许可层应作为执行引擎的入口函数，在所有结构检测之前运行。若 `allowLong` 和 `allowShort` 均为 False（背景否决一切方向），直接跳过后续结构检测，节约计算。

## 来源支撑
- [[article-huangzongprice-execution-layer-v1]]

## 矛盾与待验证
- WG V1.5 代码中已有 `allowLong`/`allowShort`（来自 FSM），但未拆分 trend/reversal 许可。当前实现中楔形和 H2/L2 共用同一套许可——本文认为这是缺陷，应在下一步编码中拆分。拆分后是否真能提升信号质量需要回测验证。


---

## Merged Content (from background-permission-filter)

# 背景许可过滤 (Background Permission Filter)

## 一句话定义
执行引擎 v1 的三层过滤机制——硬否决→软冲突检测→净许可判定——决定做多/做空是否被背景允许。

## 核心要点
- 位于背景评分（bgScore）与执行信号之间的**闸门层**
- 三层过滤：
  1. **硬否决（bgVeto）**：环境绝对不允许，直接拒绝信号
  2. **软冲突（bgConflict）**：环境有矛盾，但未到否决级别
  3. **净许可（bgSupport）**：通过所有检查，允许执行
- 六个背景状态字符串：否决 / 多强 / 多可 / 空强 / 空可 / 中性
- 可通过 `i_useBgFilter` 开关全局关闭（不建议长期关闭）

## 硬否决条件（bgVeto）

**多头否决（bgVetoLong）**（任一触发）：
| 条件 | 含义 |
|------|------|
| midRangeLocation & phaseIsRange | 区间中部震荡——无方向性 |
| phaseDir==-1 & phaseTrendHealthy & exhaustRiskS<0.55 | 空头健康趋势中的多头信号 |
| atBearResistance & lateBreakoutLong | 阻力位晚期突破——假突破风险 |
| (trendMaturityL≥0.65 或 exhaustRiskL≥0.60) & bullTargetNearby | 趋势成熟/衰竭 + 目标已到 |

**空头否决（bgVetoShort）**（同理反向）：
| 条件 | 含义 |
|------|------|
| midRangeLocation & phaseIsRange | 区间中部震荡 |
| phaseDir==1 & phaseTrendHealthy & exhaustRiskL<0.55 | 多头健康趋势中的空头信号 |
| atBullSupport & lateBreakoutShort | 支撑位晚期跌破 |
| (trendMaturityS≥0.65 或 exhaustRiskS≥0.60) & bearTargetNearby | 趋势成熟/衰竭 + 目标已到 |

## 软冲突条件（bgConflict）

**多头冲突（bgConflictLong）**：
- 背景分不足（>0.42 但 <i_bgThr）— 边缘区域
- 空头背景分显著高于多头（差 > i_confThr=0.18）
- 两面市场 + 不接近支撑

**空头冲突（bgConflictShort）**（同理反向）

## 净许可条件（bgSupport）

```
bgSupportLong  = bgScoreL ≥ i_bgThr
               & bgScoreL ≥ bgScoreS - 0.02
               & 无冲突
               & 无否决

bgSupportShort = bgScoreS ≥ i_bgThr
               & bgScoreS ≥ bgScoreL - 0.02
               & 无冲突
               & 无否决
```

## 背景状态映射

```
否决：任一方向被硬否决
多强：bgSupportLong & bgScoreL ≥ 0.72
多可：bgSupportLong & bgScoreL < 0.72
空强：bgSupportShort & bgScoreS ≥ 0.72
空可：bgSupportShort & bgScoreS < 0.72
中性：以上均不满足
```

## 与相关概念的关系
- [[wedge-gravity-dual-core]]：双核架构中的硬规则 FSM 与许可过滤是同一思路——先硬规则过滤，再软评分量化
- [[execution-scoring]]：许可过滤是执行评分的前置闸门——过滤不过，execScore 不计算
- [[emergency-exit]]：紧急逃生是许可过滤的**事后补救**——许可过滤在入场前拒绝，紧急逃生在入场后止损
- [[trend-maturity]] / [[exhaustion-risk]]：这两个评分是许可过滤第 4 条否决条件的核心输入
- [[fsm-market-cycle]]：FSM 的 phaseIsRange/phaseIsTrend 是许可过滤的第一个否决条件

## 实战应用
背景状态面板（v1 信息面板第 1 行）直接显示当前状态。交易者应只在"多强/多可"时考虑做多，"空强/空可"时考虑做空。"中性"时等待，"否决"时绝对不动。

## V3.0 否决条件细化

V3.0 源码对多头否决第 4 条做了更严格的复合条件：
```
V1/v2: (trendMaturityL≥0.65 或 exhaustRiskL≥0.60) & bullTargetNearby
V3.0: (trendMaturityL≥0.65 或 exhaustRiskL≥0.60) & currentLegWeakeningL≥0.50 & lateBreakoutLong
```
V3 用「腿弱化 ≥ 0.50 且追价突破」替代了「目标接近」——要求衰竭/成熟信号必须伴随动量衰减和追价行为才触发否决。这是更精确的设计：目标接近不一定是坏事（强趋势中目标被不断上移），但「成熟+腿弱+追价」三者共振才是真正的危险信号。空头侧同理。

## 来源支撑
- [[article-20250519-brooks-pa-execution-engine-v1]]（v1 执行引擎首次定义此三层过滤）
- [[article-huangzongprice-wg-brooks-context-v3]]（V3.0 源码——否决条件精化为三元复合条件）

## 矛盾与待验证
- 软冲突阈值 `i_confThr=0.18` 和否决阈值 `i_bgThr=0.58` 的默认值来源不明
- v3 执行引擎中许可过滤逻辑更简化（无软冲突层，仅硬否决+净许可），但 v3 Context Engine 保留了软冲突层——Context Engine 输出冲突标志，由下游执行引擎决定如何消费
- Brooks 原著中无"背景许可过滤"这一概念——这是 huangzongprice 在量化实现层的原创设计
- V3 否决条件从二元变为三元复合——增加了「追价」作为否决前提，可能放松了对成熟趋势末端的保护


---

## Merged Content (from background-permission-gating)

# 背景许可门控（6 状态）

## 一句话定义
执行引擎的背景许可层将 Context Engine 的背景分、否决、冲突、阶段方向翻译为 6 种布尔许可状态，精确控制哪些执行路线在哪些方向上激活。

## 核心要点
- **6 种许可状态**（3 对 × 2 方向）：
  | 许可 | 多头 | 空头 | 使用场景 |
  |------|------|------|---------|
  | 通用许可 | `allowLong` | `allowShort` | 基础门控：bkgSupport=1 且 !bkgVeto 且 linkOk |
  | 顺势许可 | `allowTrendLong` | `allowTrendShort` | H2/L2 路线：通用 + phaseDir 同向 |
  | 反转许可 | `allowReversalLong` | `allowReversalShort` | 楔形路线：通用 + (phaseDir 反向 或 过渡 或 震荡) |
- **否决优先**：`bgVeto` 直接阻断所有方向许可，无论 bgSupport 为何值
- **冲突降权**：`bgConflict` 不阻断许可但扣结构分（−0.15），让信号更难通过
- **可关闭**：`i_useBgFilter = false` 时通用许可始终为真（测试/调试用）
- **联动总闸**：`linkOk = apiVersionOk and apiReadyOk` 是所有许可的前提——联动失败则全部关闭

## 设计意图
- **顺势 vs 反转路线分离**：H2 做多需趋势方向为多（`allowTrendLong`），楔形做多需趋势方向为空或过渡（`allowReversalLong`），防止在上涨趋势中出做空 H2 信号
- **阶段敏感**：过渡期和震荡期同时开放趋势和反转许可，让市场自己决定方向
- **否决保护**：背景引擎判定环境极端不利时（`bgVeto`），执行引擎不输出任何方向信号

## 与相关概念的关系
- [[execution-engine-architecture]]：门控层是执行引擎架构中「背景导入后、路线分发前」的关键关卡
- [[fsm-market-cycle]]：`phaseDir`（1/0/-1）和 `phaseIsTransition`/`phaseIsRange` 来自 FSM 状态机输出
- [[h2-l2-state-machine|H2/L2 State Machine]]：H2 候选使用 `allowTrendLong`（顺势许可），不是通用 `allowLong`
- [[three-push-wedge|Three Push Wedge]]：楔形候选使用 `allowReversalLong/Short`（反转许可），不是通用许可
- [[execution-scoring]]：`bgSupport`/`bgVeto`/`bgConflict` 三个布尔值直接影响结构分计算
- [[linkage-failure-safety]]：`linkOk` 是门控层的总闸——联动失败时全部 6 许可为 false
- [[confluence-trading]]：共振信号需同时满足 H2 的顺势许可和楔形的反转许可

## 实战应用
若信号过少，检查面板中「背景状态」——若是「否决」，所有方向信号被压制。若仅是「多可」/「空可」，顺势信号应正常。若信号质量低（等级 C），检查 `bgConflict` 是否频繁为真——冲突环境下结构分被扣 0.15。

## 来源支撑
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 执行引擎源码首次实现 6 状态门控）
- [[article-huangzongprice-context-execution-linkage-setup]]（联动设置手册中描述 25 个 API 字段的传递关系）
- [[book-huangzongprice-context-analysis-steps]] — Brooks 四步法实操清单中明确提出「背景拥有对信号的『一票否决权』」原则——背景与信号冲突时必须放弃交易，这是 6 状态门控的原始思想来源

## 矛盾与待验证
- `allowReversalLong` 的条件是 `(phaseDir == -1 or transition or range)`——在趋势方向为中性（phaseDir=0）时也会开放反转许可。phaseDir=0 是否真适合做反转交易，尚无回测数据支撑。
