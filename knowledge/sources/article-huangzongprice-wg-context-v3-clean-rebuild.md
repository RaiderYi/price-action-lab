# Wedge-Gravity Brooks Context Engine V3 Clean Rebuild — 防缩放版

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6 指标，"V3 Clean Rebuild"）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_brooks_context_clean_v3_rebuild.txt`
- 代码行数：1201 行
- 脚本类型：独立 overlay 指标（单体架构——Context + Execution 合并在同一指标内）
- 版本定位：V3 系列的最精致版本——"Clean Rebuild" 意味着从头重写以解决 TradingView 自动缩放问题

## 一句话摘要
WG Brooks Context Engine 的 V3 单体清洁重写版——将背景分析（三层加权评分+否决闸）与执行层（结构触发+信号评分+分级+入场/止损/止盈计算）合并为单一 Pine Script v6 指标，并通过 plotchar/plotshape 渲染层彻底解决 TradingView autoscale 干扰问题。

## 核心论点

### 1. 架构：从两层分离到单体合一

**此前 V3 架构**（如 [[execution-engine-architecture]] 所述）：
```
Context Engine（独立指标）→ input.source API 绑定(25字段) → Execution Engine（独立指标）
```

**V3 Clean Rebuild 架构**：
```
单个指标 = 参数层 → 分析层(FSM/楔形/引力/H2L2/逃生) → 背景决策层(位置+阶段+动能→bgScore→否决) → 结构触发层(楔形+H2/L2) → 执行评分层(lFin/sFin) → 风控计算(ENT/SL/TP) → 渲染层 → 警报层
```

**关键差异**：
- 不再依赖 `input.source` API 跨指标绑定——所有数据在单一指标内流通
- 消除了 [[linkage-failure-safety]] 所述的联动失败风险（无外部依赖就没有断联）
- 代价：指标代码量膨胀到 1201 行，单文件维护复杂度上升
- 信息面板从 v3 执行引擎的 7 行决策面板扩展为 30 行全量诊断面板

### 2. 防缩放显示架构（核心工程创新）

这是本版本名称"防缩放版"的来源。TradingView 的 autoscale 机制会将所有 `label`、`box`、`line` 对象纳入 Y 轴范围计算——导致如果标签文字出现在极端价位，整个图表会被拉伸变形。

**V3 Clean Rebuild 的解决方案**：
- **事件标记**（文字标签如"多"、"空"、"H2"、"⚠"）：全部使用 `plotchar`/`plotshape`——这些是 Pine Script 原生 plot 对象，**不参与 autoscale**
- **视觉形状**（楔形连线、信号K线高亮框、ENT/SL/TP 参考线）：使用 `line`/`box`/`label`——这些参与 autoscale 但仅限视觉元素
- **信息面板**：使用 `table` 固定在右上角——完全不参与价格轴
- **单例渲染模式**：用 `var line/box/label` 变量 + 创建一次/后续仅更新坐标的模式管理图形对象生命周期，在不需要时主动 `delete` 并置 `na`

```
渲染分层决策：
plotchar/plotshape ← 事件标签（不参与缩放）
line/box/label     ← 视觉形状（参与缩放）
table              ← 信息面板（不参与缩放）
```

### 3. 完整的分析流水线（与已有概念对照）

以下模块在之前的 ingest 中已建立完整概念页，V3 Clean Rebuild 是它们的**可运行实现参考**：

| 模块 | 代码行 | 已有概念页 | V3 Clean Rebuild 中的实现特征 |
|------|--------|-----------|------|
| FSM 市场周期 | 152-237 | [[fsm-market-cycle]] | 4 状态 BREAKOUT→CHANNEL→RANGE→NEW_BREAKOUT，三条转移路径 + 置信度动态更新 |
| 三推楔形 | 241-296 | [[three-push-wedge|Three Push Wedge]] | 上升/下降楔形，对称分+收敛分+跨度分三维质量评分 |
| 引力场 | 300-318 | [[gravity-field]] | 6 个引力源（EMA/PH0/PL0/PH1/PL1/Fib50/缺口区）高斯加权 → gScore |
| H1/H2/L1/L2 状态机 | 322-397 | [[h2-l2-state-machine|H2/L2 State Machine]] | 双独立状态机，含超时重置（25 bars）和内包棒过滤 |
| 紧急逃生 | 401-417 | [[emergency-exit]] | 三类型：假突破(brkFail_EMG) + 衰竭重叠(exhBars) + 竭尽K线(exhCdl) |
| 位置层评分 | 421-464 | [[position-layer-scoring]] | 6 价位 ATR 归一化距离 → 5 位置分类 → locScore |
| 阶段层评分 | 467-509 | [[fsm-market-cycle]] / [[ctx-scoring]] | 5 过渡信号计数 → 阶段健康分类 → phaseScore |
| 动能层评分 | 513-568 | [[momentum-health]] | 四维（冲动+趋势健康+成熟度-衰竭风险-腿弱化）→ momScore |
| 背景综合与否决 | 572-596 | [[background-scoring-engine]] | bgScore = loc×0.40+phase×0.35+mom×0.25 → 四类否决 → bgState 六态 |
| 信号棒评分 | 518-534 | [[signal-bars]] | 收盘位(75%)+实体大小(1.2×avgBody5)+突破幅度(60%) |
| 结构触发与评分 | 601-620 | [[execution-scoring]] | wedge×score + H2/L2×0.55 → structureScore |
| 执行分合成 | 622-634 | [[execution-scoring]] | lFin = bg×0.55 + struct×0.25 + sig×0.20 → A/B/C 三级 |
| 风控计算 | 649-658 | [[dynamic-risk-control]] | ENT/SL/TP：SL=结构极值±0.5ATR20，ENT=突破±0.1ATR14，TP=2R |
| 确认K线 | 625-627, 643-644 | [[confirmation-bar]] | 可选延迟确认：close > high[1]+0.60×ATR14 |
| 背景许可 | 576-596, 646-647 | [[background-permission]] | allowLong/Short = bgSupport AND NOT bgVeto |

### 4. 30 行信息面板（全量诊断）

V3 Clean Rebuild 的面板是最完整的版本，30 行 × 2 列覆盖：

| 行 | 显示内容 | 行 | 显示内容 |
|----|---------|----|---------|
| 0 | 标题 + 品种·周期 | 15 | 成熟度 L/S |
| 1 | 市场周期状态 | 16 | 衰竭风险 L/S |
| 2 | 趋势方向 | 17 | 楔形形态 |
| 3 | 置信度 / R² | 18 | H/L 计数 |
| 4 | 背景结论 | 19 | 结构优先级 |
| 5 | 位置分 L/S | 20 | 信号棒分 L/S |
| 6 | 阶段分 L/S | 21 | 结构分 L/S |
| 7 | 动量分 L/S | 22 | 执行分 / 等级 |
| 8 | 背景分 L/S | 23 | 多头背景许可 |
| 9 | 背景支持 | 24 | 空头背景许可 |
| 10 | 背景否决 | 25 | 紧急逃生 |
| 11 | 位置特征 | 26 | 候选信号 |
| 12 | 阶段特征 | 27 | 前方目标 |
| 13 | 过渡证据 | 28 | 引力场得分 |
| 14 | 动能健康 L/S | 29 | 综合信号 |

### 5. 警报条件（10 种）

```
做多入场 / 做空入场 / 新突破确认 / 突破转通道 / 进入震荡区间
H2 多头计数 / L2 空头计数 / 紧急逃生预警
背景转强做多 / 背景转强做空 / 背景否决触发
背景允许+多头候选 / 背景允许+空头候选
```

### 6. 关键参数默认值

| 参数组 | 关键参数 | 默认值 |
|--------|---------|--------|
| FSM | 唐奇安周期 N | 20 |
| FSM | 重叠度均值窗口 | 5 |
| FSM | 新突破 Path-A 实体倍数 | 1.5×ATR20 |
| 信号阈值 | 信号棒最低分 | 0.40 |
| 信号阈值 | 背景支持阈值 | 0.58 |
| 信号阈值 | 背景冲突差阈值 | 0.18 |
| 执行权重 | 背景:结构:信号棒 | 0.55:0.25:0.20 |
| 楔形校验 | 空间对称比 | 0.25~2.50 |
| 楔形校验 | 时间对称比上限 | 3.00 |
| H/L 计数 | 超时重置 | 25 bars |
| 图形显示 | 回看窗口 | 300 bars |

## 提取出的新概念

本次 ingest 未创建全新概念页。V3 Clean Rebuild 的核心算法（FSM/楔形/引力/H2L2/评分/否决/风控）均已在之前的 ingest 中被提取为独立概念页。本文档的核心增量是：

1. **可作为所有已有概念的"权威实现参考"**——这份 1201 行源码是 huangzongprice 系统中经过多次迭代后最精致的版本，每个已有概念页中描述的算法都可以在此找到精确的 Pine Script 实现。
2. **单体架构 vs 两层分离的对比**——与 [[execution-engine-architecture]] 所述的两层分离形成对照，说明两种架构选择的工程权衡。
3. **防缩放工程实践**——TradingView Pine Script 的渲染层最佳实践，虽非交易概念但作为工程参考。

## 与现有知识的衔接

- [[wedge-gravity-dual-core]]：V3 Clean Rebuild 是双核架构的最终单体演化形态——V1.5 单指标双核 → V3 两层分离 → V3 Clean Rebuild 单体合一
- [[execution-engine-architecture]]：V3 Clean Rebuild 抛弃了两层分离，证明在 Pine Script v6 的 `max_lines_count=400` 等新约束下，单体架构是可行的替代方案
- [[background-scoring-engine]]：本文档包含完整的 bgScore 计算代码（与文档描述一致，无偏差）
- [[momentum-health]]：四维动能框架的完整实现，包括 `currentLegWeakening`（当前腿弱化）的精确计算
- [[emergency-exit]]：三种逃生类型的精确判定条件
- [[dynamic-risk-control]]：ENT/SL/TP 的缓冲区参数（0.5×ATR20 / 0.1×ATR14）和 2R 止盈规则

## 与现有知识的冲突

- **架构矛盾**：此前 ingest 中 [[execution-engine-architecture]] 描述了 Context→Execution 两层分离作为 V3 的核心特征，但 V3 Clean Rebuild 回归了单体架构。这并非矛盾而是**工程演进**——两层分离解决了模块化问题，但引入了联动失败风险和操作复杂度；单体架构消除了这些风险，但增加了单文件复杂度。两种架构各有适用场景。
- **无算法层面的冲突**：所有评分公式、权重、阈值与之前文档中记录的一致。

## 代码质量特征

- 使用 `var` 变量实现跨 bar 持久化状态（FSM、H2/L2 状态机、单例图形对象）
- `f_clamp01`、`f_ratioScore`、`f_distAtr`、`f_gauss` 等工具函数封装
- `visWin` 基于 `i_visBars`（默认 300 bars）的显示窗口控制
- `barstate.islast` 仅在新 bar 出现时更新信息面板（性能优化）
- 单例模式管理 `line`/`box`/`label` 生命周期（创建一次 → 仅更新坐标 → 不需要时删除）
