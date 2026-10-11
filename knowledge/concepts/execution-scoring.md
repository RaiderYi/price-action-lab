---
title: "执行评分（Execution Scoring）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, reversal-entry, swing]
tags: [execscore, 信号棒评, abc, lfin, range]
difficulty: intermediate
related: [signal-scoring-synthesis, execution-engine-architecture, confirmation-bar, h2-l2-state-machine, three-push-wedge, article-huangzongprice-execution-layer-v1, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]
char_count: 2536
---
# 执行评分（Execution Scoring）

## 一句话定义
v1/v3 执行引擎共享的三因子加权评分公式 + ABC 等级过滤——替代 V1.5 的 lFin/sFin 五因子合成，更强调背景权重且砍掉引力加成和反转加成。

## 核心要点

### 三因子加权公式
```
execScore = bgScore × 0.55 + structureScore × 0.25 + signalBarScore × 0.20
```
全部权重为可调参数（`i_execBgW`/`i_execStW`/`i_execSbW`），默认值 0.55/0.25/0.20 体现"背景定方向 > 结构定位置 > K线定时机"的优先级。

### 信号棒评分（signalBarScore，0-1）
三个维度等权叠加：
- **收盘极值**（0.40）：做多时收盘 ≥ low + 0.75×range；做空时收盘 ≤ high - 0.75×range
- **实体强度**（0.30）：body ≥ 5均实体 × 1.20
- **影线占比**（0.30）：做多时 (close - low) ≥ 0.60×range（下影短）；做空时 (high - close) ≥ 0.60×range（上影短）

### 结构分（structureScore）
取 H2 路线和楔形路线的结构分较大值：
- H2 结构分：基于 allowLong/Short + allowTrend + bgScore + veto/conflict 状态的分项累加
- 楔形结构分：基于 fallingWedge/risingWedge + allowReversal + phaseIsTransition + exhaustRisk 的分项累加
### 共振加成（v1/v3 共有）
H2 趋势候选 + 楔形反转候选同时满足时，双方各 +0.10。v1 中定义为 `confluenceLong`/`confluenceShort`。

### v1 vs v3 vs V3.0 差异
| 维度 | v1 | v3 | V3.0 (本源码) |
|------|----|----|--------------|
| 背景分来源 | 内嵌计算（精简背景层） | `input.source` API 绑定 Context Engine | 内嵌完整三层引擎 |
| 动量评分 | 含趋势成熟度 + 衰竭风险（momScore） | 不含这两个维度 | 含完整四维 momScore（含 swingCompare） |
| 结构分 | H2: 四维度累加 / 楔形: 0.55基础+加成 | 与 v1 相同公式 | 楔形: 对称×0.40+收敛×0.35+跨度×0.25；H2: 固定0.55 |
| 信号棒评分 | 三维度（极值0.40/实体0.30/影线0.30） | 三维度，同 v1 | 三维度，同 v1（公式完全一致） |
| 最终执行分 | 同公式 | 同公式 | `lFin = clamp01(bgScoreL×0.55 + structureScoreL×0.25 + signalBarScoreL×0.20)` |

### ABC 等级系统
- **A 级**：execScore ≥ 0.80 — 高置信度
- **B 级**：execScore ≥ 0.60 — 中等置信度
- **C 级**：execScore < 0.60 — 低置信度
- 用户可配置 `i_gradeMin` 最低等级（A/B/C），低于该等级的信号不触发

### 信号生成链路
```
信号棒评分 ≥ i_sigThr(0.40) → 结构候选(H2或楔形) → 执行分计算 → 等级过滤 → 确认K线(可选) → 做多/做空信号
```

## 与相关概念的关系
- [[signal-scoring-synthesis]]：V1.5 的 lFin/sFin 五因子合成——本页的三因子公式是其简化替代方案
- [[execution-engine-architecture]]：本评分系统运行的架构容器
- [[confirmation-bar]]：评分之后的最终确认环节
- [[h2-l2-state-machine|H2/L2 State Machine]]：结构分来源之一（H2 路线）
- [[three-push-wedge|Three Push Wedge]]：结构分来源之二（楔形路线）

## 实战应用
决策面板的"等级"和"信号"行直接反映 execScore 结果。如果频繁看到 C 级候选但无信号，可降低 `i_gradeMin` 至 C 或提高 `i_sigThr` 以收紧信号棒要求。

## 来源支撑
- [[article-huangzongprice-execution-layer-v1]]（执行层 v1 设计稿首次提出三因子公式和 ABC 分级）
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 执行引擎是第一个实现三因子加权公式的版本——权重与 v3 完全一致）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 执行引擎沿用同一公式，仅精简了面板）

## 矛盾与待验证
- 三因子（v1/v3）vs 五因子（V1.5 lFin/sFin）：三因子更简洁、背景权重大（55%），但砍掉引力加成（位置环境分）和反转加成——趋势末端反转信号可能被降级。v1 在动量评分中保留了趋势成熟度和衰竭风险，v3 则连这两个也砍掉了。三者无对比回测数据。
- 信号棒评分的三维度（极值/实体/影线）是否足够？V1.5 还考虑了下影/上影的绝对占比和与前几根的比较，v3 版本更粗糙。
- ABC 等级阈值 0.80/0.60 是经验值，不同品种/周期的最优阈值需要回测确定。
