---
title: "Context Engine v2（四层加权背景引擎）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge]
tags: [layer, 健康, bgscore, 否决, 衰竭风险]
difficulty: intermediate
related: [atr-position-scoring, fsm-market-cycle, momentum-health, brooks-four-step-context, ctx-scoring, wedge-gravity-dual-core, pine-source-binding, three-push-wedge, emergency-exit, article-huangzongprice-context-engine-v2]
char_count: 2890
---
# Context Engine v2（四层加权背景引擎）

## 一句话定义
Brooks PA 背景引擎的 v2 重新实现——将 V1.5 的定性四步法升级为四层显式加权评分流水线（位置40%+阶段35%+动能25%），输出 7 状态背景结论。

## 核心要点
- **完全重写**：从 V1.5/v3 的双核/三层架构演进为四层显式加权流水线，所有加分/扣分规则以 `+=`/`-=` 硬编码在 Pine Script v6 源码中
- **默认权重**：位置层 40% + 阶段层 35% + 动能层 25%（可通过输入参数调节）
- **输出 7 状态**：多强(2)/多可(1)/中性(0)/空可(-1)/空强(-2)/否决(9)，比 V1.5 的连续 0-1 分数更直接
- **API 导出**：30+ 变量通过 `display.data_window` 暴露，供下游执行层联动
- **报警系统**：8 条 alertcondition（背景转多/转空/否决、支持多/空、区间中部、衰竭风险）

## 四层流水线

```
raw/OHLC → [Layer1: 位置层 40%] → locScore L/S
         → [Layer2: 阶段层 35%] → phaseScore L/S
         → [Layer3: 动能层 25%] → momScore L/S
         → [Layer4: 综合与否决]  → bgScore → conflict? → veto? → 7 状态
```

### Layer 1 — 位置层（权重 0.40）
参见 [[atr-position-scoring]]：基于 ATR 距离，检测价格相对于分型极点/Donchian/EMA20/Fib50 的位置，按预设加分/扣分规则计算 `locScore`

### Layer 2 — 阶段层（权重 0.35）
引擎：[[fsm-market-cycle]] 四状态 FSM + 5 信号过渡检测 + 阶段健康分类

| 多头得分条件 | 加分 | 空头得分条件 | 加分 |
|-------------|------|-------------|------|
| 趋势健康 (phaseTrendHealthy) | +0.52 | 趋势健康 (空头) | +0.52 |
| 趋势弱化 (phaseTrendWeakening) | +0.30 | 趋势弱化 (空头) | +0.30 |
| 仅趋势状态 | +0.20 | 仅趋势状态 | +0.20 |
| 震荡+近支撑 | +0.12 | 震荡+近阻力 | +0.12 |
| 对方趋势健康 | −0.26 | 对方趋势健康 | −0.26 |
| 双向环境+不近关键位 | −0.14 | 双向环境+不近关键位 | −0.14 |

### Layer 3 — 动能层（权重 0.25）
参见 [[momentum-health]]：四维分解（趋势健康度/成熟度/衰竭风险/当前腿弱化），综合公式：
```
momScore = 0.10 + impulseScore×0.30 + trendHealth×0.28
           − trendMaturity×0.20 − exhaustRisk×0.18 − legWeakening×0.12
```

### Layer 4 — 综合与否决
```
bgScore = locScore×0.40 + phaseScore×0.35 + momScore×0.25
```

**冲突检测**（任一触发 → 背景不支持）：
- bgScore < 0.58 且 > 0.42（灰色地带）
- 多空差 > 0.18（方向不明确）
- 双向环境 + 不近关键位

**否决条件**（任一触发 → bgStateCode=9）：
1. 区间中部 + 震荡阶段
2. 对方趋势健康 + 对方衰竭风险 < 0.55
3. 追价突破 + 对方阻力/支撑
4. 成熟度 ≥ 0.65 或 衰竭风险 ≥ 0.60 + 目标接近

输出 `bgStateCode` → `bgState`：
- 2: 多强（bgScore ≥ 0.72）
- 1: 多可
- 0: 中性
- −1: 空可
- −2: 空强（bgScore ≥ 0.72）
- 9: 否决

## 与相关概念的关系
- [[brooks-four-step-context]]：v2 是 V1.5 四步法的正式工程化升级——从「定性描述+隐式评分」变为「四层显式加权」
- [[ctx-scoring]]：V1.5 的 ctx1/ctx2/ctx3 → v2 的 locScore/phaseScore/momScore，评分公式彻底透明化
- [[atr-position-scoring]]：Layer 1 的位置评分子系统
- [[momentum-health]]：Layer 3 的动能四维分解子系统
- [[fsm-market-cycle]]：Layer 2 的 FSM 核心引擎（v2 保留原逻辑 + 5 信号过渡检测增强）
- [[wedge-gravity-dual-core]]：v2 是双核→三层→四层的架构演进终点
- [[pine-source-binding]]：v2 引入 `display.data_window` 作为新的 API 导出通道
- [[three-push-wedge|Three Push Wedge]]：v2 中楔形标记参与动能层全部 4 子维度
- [[emergency-exit]]：v2 将衰竭风险系统化为 4 维度分解 + 4 条否决规则

## 实战应用
在 TradingView 图表上加载此指标后：
1. 看背景色：绿=多头趋势健康、红=空头趋势健康、橙=震荡、紫=过渡
2. 看信息面板：位置分/阶段分/动量分/背景分 → 背景结论（多强/多可/中性/空可/空强/否决）
3. 看背景标签：「背景转多」「背景转空」「背景否决」
4. 下游执行层通过 API plot 的 data_window 读取 30+ 变量做入场过滤

## 来源支撑
- [[article-huangzongprice-context-engine-v2]]

## 矛盾与待验证
- **权重可配置性**：默认权重 40/35/25 是经验设定，最优值需跨品种/周期回测验证
- **否决阈值敏感性**：成熟度阈值 0.65、衰竭风险阈值 0.60、冲突差阈值 0.18 均为硬编码默认值
- **过渡检测 5 信号**：累计计数法（≥2=过渡）的假阳性率/假阴性率未知
- v2 砍掉了 V1.5/v3 中的一些模块（引力场、H2/L2 状态机、Playbook），是精简还是退化需实战检验
