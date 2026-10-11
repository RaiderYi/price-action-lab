---
title: "Brooks 四步上下文分析框架"
phase: [trend, range, breakout, transition]
signal_types: [wedge]
tags: [ctx, step, score, fsm, brooks]
difficulty: intermediate
related: [ctx-scoring, support-resistance, fsm-market-cycle, emergency-exit, signal-scoring-synthesis, wedge-gravity-dual-core, article-20250519-brooks-context-4-pine, article-huangzongprice-wedge-gravity-v2-master, article-huangzongprice-context-engine-v1, article-20260519-wedge-gravity-brooks-v1-pine, book-huangzongprice-context-analysis-steps, position-layer-scoring, article-huangzongprice-context-engine-v2, anti-repainting, momentum-health, indicator-visual-optimization, article-huangzongprice-context-engine-v6, atr-position-scoring, context-engine-v2]
char_count: 5161
---
# Brooks 四步上下文分析框架

## 一句话定义
Brooks「分析背景」方法论：在考虑任何交易前，依次回答四个问题——价位→阶段→动能→否决，每步产生 0-1 量化评分。

## 核心要点
- 四步是**顺序流水线**：Step1 的 S/R 结论影响 Step2 的阶段判断，Step2 的阶段影响 Step3 的动能权重，Step4 在前三步基础上执行最终否决
- 每步独立产生 `ctx1_score` / `ctx2_score` / `ctx3_score`（0-1），Step4 产生二元 veto 标志
- 框架通过 `i_useBrooks4` 总开关控制——关闭时所有 ctx 分数归零但不影响 FSM/引力/原信号逻辑独立运行
- Pine Script 中的变量命名约定：`ctx` 前缀 = 上下文分，与信号评分 `lFin/sFin` 互不干扰
- V1.5 起入场标签显示 `Brooks: {阶段} ·①{ctx1} ③{ctx3}`，便于实时对照面板分数

## 四步详解

### Step1 — 支撑阻力（"市场在什么价位？"）
检测当前价格相对于关键 S/R 的位置：
- **显著高低点**：`ph0/pl0`（最近）、`ph1/pl1`（次近）
- **唐奇安通道**：`donchH/donchL` 为动态区间边界
- **EMA20**：`ema20v` 作为动态支撑/阻力磁力位
- **区间 50%**：`fib50`（`majorSH` 与 `majorSL` 的中点）
- **测量移动 MM**：`mmTargetBrooks`——腿幅投影到 50% 另一侧
- **整数关口**：`nearestRound`：`roundStep`（品种最小变动×10 或自定义），接近判定 = `i_roundNearMul × ATR14`
- **输出**：`ctx1_score`（0-1）+ `ctx1_note` 说明字符串

### Step2 — 市场阶段（"趋势 / 震荡 / 过渡？"）
- **震荡区间(TR)**：`fsm == 2` 且非过渡标记
- **突破(Breakout)**：`fsm == 3 或 0` 且非过渡
- **多头/空头趋势·通道**：`fsm == 1` 且 `fsmDir`
- **过渡(Transition)**（`brooksTransition`）：前根 `emaSteep` 且本根 `emaFlat`（通道/突破段），或通道内唐奇安宽度扩张 `donchWiden`（`donchW > donchWAvg × i_donchWidenMul`）
- **输出**：`brooksPhaseStr`（阶段标签）+ `ctx2_score`（过渡偏低 → TR 中等 → 趋势/突破偏高）

### Step3 — 动能与健康度
- **重叠度**：`avgOlp` 越低（棒与棒之间重叠少）→ 动能越强 → `ctx3_score` 越高
- **均线斜率**：`emaSteep`（陡峭=趋势强）/ `emaFlat`（走平=动能衰减）
- **紧急/衰竭**：`emergExit` 为真时压低分数，文案标注「紧急/衰竭触发」
- **实体强度**：当前棒实体与 `ta.sma(barBody, 5)` 比较
- **楔形标记**：在 `ctx3_note` 末尾追加「·楔形」
- **输出**：`ctx3_score`（0-1）+ `ctx3_note` 说明字符串

### Step4 — 一票否决
参见 [[ctx-scoring]] → Step4 否决规则，此处不重复。

## 与相关概念的关系
- [[ctx-scoring]]：子概念，详细描述 ctx1/ctx2/ctx3 的评分规则和否决逻辑
- [[support-resistance|Support/Resistance]]：Step1 的理论基础——16+ 种 S/R 类型、80% 法则
- [[fsm-market-cycle]]：Step2 的核心引擎——FSM 四状态机
- [[emergency-exit]]：Step3 的衰竭检测 + Step4 否决的动能来源
- [[signal-scoring-synthesis]]：互补关系——四步评分判断「能否交易」（上下文），信号评分判断「信号多好」（K线质量）
- [[wedge-gravity-dual-core]]：四步框架所在的双核架构整体设计

## 实战应用
在 TradingView 图表上：开启 `i_useBrooks4`，观察面板上的 ①/②/③ 分数和否决文案（`brooksVetoTxt`）——当 ①+②+③ 均偏高且无否决时，上下文最有利；任一分数偏低或有否决触发时应谨慎或放弃。

## 来源支撑
- [[article-20250519-brooks-context-4-pine]]
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码第474-508行——四步法的首次完整 Pine Script 集成：ctx1_score/ctx2_score/ctx3_score 精确加权公式 + brooksPhaseStr 枚举 + brooksTransition 过渡检测）
- [[article-huangzongprice-context-engine-v1]]（standalone v1 实现，独立于 WG_V15 双核架构，拥有完整的自包含评分流水线）
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — **WG_V15 的 Pine Script 源码**，揭示了 ctx1/ctx2/ctx3 在双核架构中的精确加权公式（此前仅描述因子未给公式）（standalone v1 实现，独立于 WG_V15 双核架构，拥有完整的自包含评分流水线）
- [[book-huangzongprice-context-analysis-steps]] — **实操检查清单版**：同一四步框架的人工交易者版本，含 Brooks 课程视频编号映射（02D/19B/12A/16C/14D/08C/08D）和 Mermaid 流程图，强调「一票否决权」纪律原则

## v1 独立实现与 WG_V15 的区别
- **架构定位**：v1 是独立 overlay 指标，不依赖 `input.source` API 绑定；WG_V15 的 Context Engine 是双核架构的子模块
- **位置层**：v1 使用 6 关键价位 + ATR 归一化距离 + 加减分制（详见 [[position-layer-scoring]]）；WG_V15 使用 7 因子（含测量移动 MM 和整数关口）
- **阶段层**：v1 FSM 使用 `var` 持久化变量，`fsm=0` 可通过 `bo2ch` 路径到达；WG_V15 FSM 中 `fsm=0` 为死分支
- **动能层**：v1 使用五因子加权公式（动量+趋势健康+成熟度+衰竭风险+腿弱化）；WG_V15 使用重叠度/均线斜率/emergExit/实体强度/楔形标记
- **否决层**：v1 有 4 类否决（区间中部/逆势/追价/成熟衰竭）；WG_V15 有 2 类（TR 位置/emergExit 顺势）
- [[article-huangzongprice-context-engine-v2]]（v2 将此四步法正式升级为四层显式加权流水线）

## v6 刷新

v6 PA背景分析引擎（`@version=6`，独立 Pine Script v6 overlay 指标）为四步框架带来三项关键升级：

1. **Step 0 — 无重绘基础**：所有 o/h/l/c 在 K 线未收盘时回退到上一根已确认 K 线数据，从源头消除信号重绘（详见 [[anti-repainting]]）
2. **Step 3 — 动能与健康度分离**：将笼统的 `ctx3_score` 拆分为独立的 `momentumScore`（五因子加权）和 `healthScore`（四正一罚+高潮惩罚），首次公开精确加权公式（详见 [[momentum-health]]）
3. **可视化三修复**：盒体留存+垃圾回收、yloc 相对定位标签、极简十字 SR 信号（详见 [[indicator-visual-optimization]]）

来源：[[article-huangzongprice-context-engine-v6]]

## v2 演进
v2 Context Engine（`brooks_pa_context_engine_v2_linkable`）将本框架从「定性描述 + 隐式评分」升级为「四层显式加权」：
- Step1 价位 → **位置层** [[atr-position-scoring]]（ATR 距离 + 硬编码加分/扣分规则）
- Step2 阶段 → **阶段层**（FSM 不变，但过渡检测从 2 信号扩展为 5 信号）
- Step3 动能 → **动能层** [[momentum-health]]（四维分解，不再是笼统的 ctx3_score）
- Step4 否决 → **综合与否决层** [[context-engine-v2]]（冲突检测 + 4 条否决规则 + 7 状态输出）
- V1.5 的 `ctx1`/`ctx2`/`ctx3` 在 v2 中改名为 `locScore`/`phaseScore`/`momScore`，分别由独立的代码段计算，不再依赖隐式级联

## 矛盾与待验证
- Step2 的过渡检测依赖 `i_donchWidenMul` 参数，此参数的品种校准规则未在本文档中给出
- ctx2_score（Step2）在入场标签 V1.5 中被省略（标签只显示 ① 和 ③），原因未说明——可能是 Step2 的阶段信息已通过 `brooksPhaseStr` 充分表达

## 源码验证（来自 Pine Script，2026-05-19 更新）

以下精确公式来自 `wedge_gravity_tradingview_brooks_v1.txt` 源码：

**ctx1_score 公式**（第 477 行）：
```
ctx1_score = clamp01(ctx1_keyScore × 0.52 + (gravOK ? 0.33 : 0.12) + (mmDistAtr < 0.55 ? 0.13 : 0.0) + (nearRoundBr ? 0.08 : 0.0))
```
其中 `ctx1_keyScore = clamp01(1.0 - min(minKeyAtr, 2.5) / 2.5)`，`minKeyAtr` 取 ph0/pl0/ema20/donchH/donchL/fib50 的最小 ATR 距离。

**ctx2_score 公式**（第 496–497 行）：
```
ctx2_score = brooksTransition ? 0.46 : fsm==2 ? 0.52 : fsm==1 ? 0.76 : (fsm==3 or fsm==0) ? 0.84 : 0.55
```
过渡 0.46 / 震荡 0.52 / 通道 0.76 / 突破 0.84 / 默认 0.55。

**ctx3_score 公式**（第 702–710 行）：
```
ctx3_score = clamp01(olpHealth × 0.38 + slopePart + emergPart + bodPart)
```
其中 `olpHealth = clamp01(1.0 - min(avgOlp,0.75)/0.75)`, `slopePart = emaSteep?0.32 : emaFlat?0.18 : 0.24`, `emergPart = emergExit?0.0:0.26`, `bodPart = barBody > bodAvg5×1.15 ? 0.12 : 0.04`。
