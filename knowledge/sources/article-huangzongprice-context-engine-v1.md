# Brooks PA Context Engine v1 — Pine Script 源码

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6 指标）
- 原始位置：`raw/articles/huangzongprice/brooks_pa_context_engine_v1.txt`
- 脚本类型：独立 overlay 指标（不依赖其他脚本的 input.source）
- 代码行数：465 行

## 一句话摘要
huangzongprice 将 Brooks「分析背景」四步法工程化为独立 Pine Script v6 指标，三层评分（位置×0.40 + 阶段×0.35 + 动能×0.25）加权合成背景分，四条件否决闸门决定最终多空背景支持。

## 核心论点

### 架构总览
这是一个**独立的 standalone 指标**（非 WG_V15 双核架构中的子模块）。与 WG_V15 的 Context Engine 子模块不同，v1 拥有自己的完整评分流水线，不通过 `input.source` API 绑定外部数据。四层递进：

```
OHLC → 基础数据层(ATR/EMA/Donchian/Pivot) → 位置层 → 阶段层 → 动能层 → 综合背景分 → 否决闸 → 背景结论
```

### 第一步：位置层（Location Layer）
使用 `f_distAtr(level, atrBase)` 将所有关键价位距离归一化为 ATR 倍数：

| 关键价位 | 距离变量 | 含义 |
|---------|---------|------|
| 最近波段高点 ph0 | `distToPh0Atr` | 距阻力 |
| 最近波段低点 pl0 | `distToPl0Atr` | 距支撑 |
| Donchian High (20期) | `distToDonchHAtr` | 距近期上边界 |
| Donchian Low (20期) | `distToDonchLAtr` | 距近期下边界 |
| EMA20 | `distToEmaAtr` | 距动态均线 |
| Fib50 (ph0-pl0中点) | `distToFib50Atr` | 距波段中点 |

**位置分类判定**（阈值 = ATR 倍数）：
- `atBullSupport`：距多方支撑 ≤ 0.60 ATR → +0.30
- `atBearResistance`：距空方阻力 ≤ 0.60 ATR → +0.30
- `nearBullSupport`：距多方支撑 ≤ 1.20 ATR → +0.18
- `nearBearResistance`：距空方阻力 ≤ 1.20 ATR → +0.18
- `midRangeLocation`：距 Donchian 中线 ≤ 区间宽度×0.20 → -0.28
- `lateBreakoutLong/Short`：收盘突破旧 Donchian 边界+离场支撑/阻力 → -0.20
- `bullTargetNearby/bearTargetNearby`：目标位 ≤ 0.80 ATR → -0.16
- 基础分 = 0.10，最终 `locScoreL`/`locScoreS` 经 `f_clamp01()` 钳位到 [0,1]

### 第二步：阶段层（Phase Layer）
独立的 FSM（四状态，用 `var` 变量跨 Bar 持久化）：

| 状态 | 编码 | 含义 |
|------|------|------|
| BREAKOUT | 0 | 突破 |
| CHANNEL | 1 | 通道 |
| TRADING_RANGE | 2 | 震荡区间 |
| NEW_BREAKOUT | 3 | 新突破 |

**三条转移路径**（每根最多一条，优先级递减）：
1. `rng2nbk`（TR→新突破）：路径A（大实体+收盘过 Donchian+突破Donchian边界）或 路径B（连续≥3根收盘同方向过旧 Donchian 边界）
2. `bo2ch`（突破→通道）：振幅≥1×ATR20 + 逆势回调
3. `ch2rng`（通道→TR）：大实体+极强收盘+突破分型

**过渡检测（5 信号计数，≥2 即过渡）**：
1. `transitionByOverlap`：avgOlp > 0.32
2. `transitionBySlopeLoss`：EMA斜率不足或平坦
3. `transitionByBroadChannel`：通道+重叠>0.24+置信度<0.72
4. `transitionByWedge`：上升楔形或下降楔形
5. `transitionByFailedBreakout`：近3根突破分型但收盘失败

**阶段健康分类**：
- `phaseTrendHealthy`：趋势+置信度≥0.70+EMA陡峭+低重叠+非过渡
- `phaseTrendWeakening`：趋势+≥1过渡信号+(高重叠或非EMA陡峭)
- `phaseTwoSided`：震荡或过渡或重叠度>0.35

**阶段评分**（基础分 0.08）：
- 多头方向 + 趋势健康 → +0.52；趋势弱化 → +0.30；仅趋势 → +0.20
- 空头方向 + 多头趋势弱化且靠近支撑 → +0.22
- 震荡 + 靠近支撑 → +0.24+0.12
- 双向且不靠近支撑 → -0.14
- 空头方向 + 空头趋势健康 → -0.26

### 第三步：动能层（Momentum Layer）
五因子加权评分：

| 因子 | 公式核心 | 权重方向 |
|------|---------|---------|
| **Impulse Score** | `bodyRatio×0.55 + breakMag×0.45`（实体占比+突破幅度） | +0.30 |
| **Trend Health** | 动量×0.35 + EMA斜率×0.25 + 重叠度×0.20 + 无衰竭棒×0.20 | +0.28 |
| **Trend Maturity** | 楔形×0.35 + 追价×0.25 + 衰竭棒×0.20 + 目标位近×0.20 | -0.20 |
| **Exhaustion Risk** | 假突破×0.40 + 楔形×0.25 + 高重叠×0.15 + 目标近×0.20 | -0.18 |
| **Current Leg Weakening** | 动量衰减×0.30 + 高重叠×0.25 + EMA斜率丢失×0.20 + 楔形×0.25 | -0.12 |

基础分 0.10，最终 `momScoreL`/`momScoreS` 经钳位到 [0,1]。

**衰竭棒条件**：实体 ≥ avgBody20 × 1.50 且 波幅 > ATR14 × 1.20

### 第四步：综合与否决（Integration & Veto）
**综合背景分**：
- `bgScoreL = locScoreL×0.40 + phaseScoreL×0.35 + momScoreL×0.25`
- `bgScoreS = locScoreS×0.40 + phaseScoreS×0.35 + momScoreS×0.25`

**背景冲突判定**：
- 单项不足但非极低（0.42-0.58）
- 多空差距 > 0.18
- 双向+不靠近目标方向支撑/阻力

**四类否决条件**（任一满足即否决）：
1. **区间中部否决**：`midRangeLocation` + 震荡阶段
2. **逆势否决**：对向趋势健康 + 对向衰竭风险 < 0.55
3. **追价否决**：在阻力位做多追价 / 在支撑位做空追价
4. **成熟度/衰竭否决**：趋势成熟度或衰竭风险达阈值 + 目标位临近

**背景结论六态**：
- `多强`：bgSupportLong + bgScoreL ≥ 0.72
- `多可`：bgSupportLong + bgScoreL < 0.72
- `空强`：bgSupportShort + bgScoreS ≥ 0.72
- `空可`：bgSupportShort + bgScoreS < 0.72
- `中性`：无明确方向支持
- `否决`：任一否决条件触发

### 面板渲染
信息面板（15行 × 2列）显示：市场阶段、趋势方向、置信度/R²、位置分 L/S、阶段分 L/S、动量分 L/S、背景分 L/S、背景结论、背景支持、背景否决、位置特征、趋势健康 L/S、成熟度 L/S、衰竭风险 L/S。

### 警报条件（7 种）
- 背景转多 / 背景转空 / 背景否决 → 含 ticker+周期
- 背景支持做多 / 背景支持做空 → 含 ticker
- 区间中部 / 衰竭风险高 → 含 ticker

## 提取出的新概念
- [[position-layer-scoring]] — ATR归一化的位置层评分算法（填补 ctx-scoring 中"未公开"的公式）
- [[trend-maturity]] — 趋势成熟度多因子评估（楔形+追价+衰竭+目标）
- [[late-breakout]] — 追价判定：突破旧边界+远离支撑/阻力+临近对向阻力/支撑

## 与现有知识的衔接
- [[brooks-four-step-context]]：v1 是四步框架的独立实现，定位不同于 WG_V15 的双核架构子模块
- [[ctx-scoring]]：v1 源码给出了此前标注为「未公开」的完整评分公式——ctx1/ctx2/ctx3 的精确权重、阈值和因子组合
- [[fsm-market-cycle]]：v1 FSM 拥有独立的 var 持久化状态变量，与 WG_V15 的 FSM 在实现上有所不同（v1 中 fsm=0 通过 bo2ch 可达）
- [[emergency-exit]]：v1 的 exhaustion risk 因子（假突破×0.40 + 楔形×0.25 + 高重叠×0.15 + 目标近×0.20）是 emergExit 的量化替代方案

## 与现有知识的冲突
- **无直接冲突**。v1 Context Engine 是一个独立的 standalone 实现，其评分体系与 WG_V15 的 Context Engine 子模块（通过 input.source 绑定）是**平行关系**而非替代关系。区别在于：
  - WG_V15 的 ctx 评分嵌入在双核架构中，依赖 FSM/引力场/信号评分的联动
  - v1 是完全自包含的独立指标，拥有自己的 FSM、自己的评分、自己的否决逻辑
  - v1 的位置层使用了 Donchian Channel 和 ATR 归一化距离，比 WG_V15 的位置检测（显著高低点+唐奇安+EMA+50%+MM+整数关口）更精简
  - v1 的否决条件包含区间中部否决和逆势否决，WG_V15 的否决只有 TR 位置否决和 emergExit 顺势否决
