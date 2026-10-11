# Brooks PA Execution Engine v2（联动版）— 源码

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6）
- 原始位置：`raw/articles/huangzongprice/brooks_pa_execution_engine_v2_linked.txt`
- 配套脚本：`brooks_pa_context_engine_v2_linkable.txt`（Context Engine v2）
- 操作手册：[[article-huangzongprice-context-execution-linkage-setup]]
- 后续版本：v3（lean linked — [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]）

## 一句话摘要
huangzongprice Brooks PA 系统 v2 执行层 Pine Script 源码——通过 25 个 `input.source` API 绑定从 Context Engine v2 接收背景状态，运行 H2/L2 和楔形两条信号路线，经三因子加权评分（bg×0.55 + struct×0.25 + sig×0.20）输出 A/B/C 分级交易信号。

## 核心论点

### 1. 整体架构（v2 = 两层分离的首个实现）
v2 是 huangzongprice 系统中**第一个将背景层与执行层物理分离为两个独立指标的版本**。此前 V1.5（WG_V15）是单指标内嵌双核。v2 的做法：
- **Context Engine v2**：作为独立指标先加载，通过 invisible plot 导出 25 个 data window 字段
- **Execution Engine v2**：后加载，通过 `input.source` 逐项绑定 Context 的 data window 输出
- 这种架构保证了「背景层是唯一权威来源」，背景与执行不再漂移

### 2. H2/L2 状态机（4 阶段 FSM）
v2 的 H2/L2 实现采用 4 阶段有限状态机（比 V1.5 更简洁）：

| 阶段 | 多头链（H2） | 空头链（L2） |
|------|-------------|-------------|
| Phase 0 | 等待 Pivot Low | 等待 Pivot High |
| Phase 1 | PL 出现，记录 `hRefLow` | PH 出现，记录 `lRefHigh` |
| Phase 2 | 上破 high[1] → H1 形成，记录 `hRefHigh` | 下破 low[1] → L1 形成，记录 `lRefLow` |
| Phase 3 | 回撤 + 再上破 hRefHigh → **H2 出信号** | 反弹 + 再下破 lRefLow → **L2 出信号** |

- **孕线规则**：`insideBar`（内含棒）不推进阶段计数
- **超时机制**：`i_timeoutH2L2`（默认 25 bars）超时后状态机自动重置
- **过滤项**：`i_requireTrendH2`（默认开）要求 H2 仅顺势触发；`i_h2l2MinStruct`（默认 0.45）最低结构分门槛

### 3. 楔形检测（纯 Pivot 判定）
v2 的楔形检测基于 3 组 pivot high/low 的位置关系：

- **上升楔形（偏空结构）**：`ph2b < pl1b < ph1b`（时间序）且 `ph1 > ph2`、`pl0 > pl1`（价格收敛），跨度在 `[i_wedgeSpanMin, i_wedgeSpanMax]` 之间
- **下降楔形（偏多结构）**：`pl2b < ph1b < pl1b`（时间序）且 `pl1 < pl2`、`ph0 < ph1`，跨度同上
- 不做 V1.5 那样的多维加权评分（对称性/收口/跨度）——v2 的楔形是布尔判定 + 简单结构分累加

### 4. 背景许可门控（6 状态 — 核心创新）
这是 v2 执行引擎的**核心控制层**，将背景引擎的输出翻译为 6 种许可状态：

```pine
allowLong           = (!useFilter | bgSupportLong)  & !bgVetoLong  & linkOk
allowShort          = (!useFilter | bgSupportShort) & !bgVetoShort & linkOk
allowTrendLong      = allowLong  & phaseDir == 1
allowTrendShort     = allowShort & phaseDir == -1
allowReversalLong   = allowLong  & (phaseDir == -1 | transition | range)
allowReversalShort  = allowShort & (phaseDir == 1  | transition | range)
```

不同路线使用不同的许可以防信号冲突：
- **H2/L2 顺势路线**：使用 `allowTrend*`（要求 phaseDir 同向）
- **楔形反转路线**：使用 `allowReversal*`（要求 phaseDir 反向或过渡/震荡）
- `bgVeto`（否决）直接阻断对应方向所有信号
- `bgConflict`（冲突）降低结构分但不阻断

### 5. 信号棒评分（3 项准则）
v2/v3 共用同一套简化信号棒评分（区别于 V1.5 的 lFin/sFin 五因子合成）：

**做多信号棒**（满分 1.0）：
- 收盘 ≥ low + 0.75×range → +0.40（收盘靠近高极值）
- body ≥ avgBody5 × 1.20 → +0.30（实体超过近期平均的 1.2 倍）
- (close−low) ≥ 0.60×range → +0.30（下影线占比 ≥ 60%）

**做空信号棒**：对称规则。

最低阈值：`i_sigThr`（默认 0.40）。

### 6. 结构分计算
**H2/L2 结构分**（5 项累加后 clamp）：allowLong/Short（0.30）+ allowTrend（0.20）+ bgScore ≥ 阈值（0.20）+ !veto（0.15）+ !conflict（0.15）

**楔形结构分**：detected（0.55）+ allowReversal（0.20）+ transition（0.15）+ exhaustRisk ≥ 0.5（0.10）

### 7. 共振机制（Confluence）
当 H2 与下降楔形（或 L2 与上升楔形）在**同一 bar 同时触发**时，双方结构分各 +0.10。这是 v2 独有的机制——v3 是否保留待确认。

### 8. 执行评分与等级
三因子加权：`execScore = bgScore×0.55 + structScore×0.25 + sigBarScore×0.20`
- A 级（≥0.80）/ B 级（≥0.60）/ C 级（其余）
- `i_gradeMin` 可设最低等级门槛
- `i_useConfirm`（默认关）启用确认 K 线入场

### 9. 止损/入场/目标计算
```pine
longSL  = majorSL - max(mintick, 0.5×ATR20)     # 止损在主要摆动低点下方
longEnt = high + max(mintick, 0.1×ATR14)         # 入场在当前 bar 高点上方
longRisk = max(longEnt - longSL, 0.5×ATR14)      # 风险 ≥ 0.5 ATR
longTP  = longEnt + 2.0×longRisk                 # 固定 2:1 R:R
```

### 10. 信息面板（18 行）
v2 的信息面板比 v3（7 行）详细得多：联动状态、API 版本、API Ready、背景状态、市场阶段、方向、H2/L2、楔形、多头结构/等级、空头结构/等级、背景分 L/S、执行分 L/S、信号棒分 L/S、多头候选、空头候选、最终信号、共振。

### 11. 报警条件（10 条）
H2 形成、L2 形成、上升楔形、下降楔形、多头候选、空头候选、做多信号、做空信号、多头共振、空头共振。

## 提取出的新概念
- [[background-permission]] — 6 状态背景许可门控系统
- [[confluence-trading]] — H2+楔形共振加成机制

## 与现有知识的冲突
- v2 的 H2/L2 状态机与 V1.5 的 `bPh`/`sPh` 实现不同（v2 是 4-phase FSM，V1.5 是双变量状态追踪）。已在 [[h2-l2-state-machine|H2/L2 State Machine]] 中标注差异。
- v2 的楔形检测比 V1.5 简化——不做对称/收口/跨度评分。已在 [[three-push-wedge|Three Push Wedge]] 中标注。
- v2 的信号棒评分（3 项）比 V1.5 的 lFin/sFin（5 因子）大幅简化。已在 [[signal-scoring-synthesis]] 中标注差异。

## 版本定位
| 版本 | Context | Execution | 架构 |
|------|---------|-----------|------|
| V1.5 | 单指标内嵌 | 单指标内嵌 | 双核（硬规则 FSM + 软评分量化）|
| **v2** | **独立 Context Engine v2** | **独立 Execution Engine v2** | **两层分离（input.source 绑定）** |
| v3 | Context Engine v2（同 v2） | Execution Engine v3 lean | 两层分离（精简面板 + 简化评分）|
