---
title: "Ctx 上下文评分系统"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry]
tags: [ctx, score, step, 价格接近, donchl]
difficulty: intermediate
related: [brooks-four-step-context, support-resistance, fsm-market-cycle, emergency-exit, signal-scoring-synthesis, measured-move, fifty-percent-pullback, trading-range-quality, article-20250519-brooks-context-4-pine, article-huangzongprice-wedge-gravity-v2-master, article-huangzongprice-context-engine-v1, article-huangzongprice-context-engine-v2, article-huangzongprice-context-engine-v6, position-layer-scoring, trend-maturity, late-breakout, article-huangzongprice-pa-context-engine-v6, momentum-health]
char_count: 5870
---
# Ctx 上下文评分系统

## 一句话定义
Brooks 四步上下文分析法中，将 Step1～Step3 的定性分析量化为 0-1 数值评分，Step4 产生二元否决标志的评分体系。

## 核心要点
- `ctx1_score`（价位分）、`ctx2_score`（阶段分）、`ctx3_score`（动能分）均为 0-1 连续值
- 评分不是独立的——Step1 结论影响 Step2 权重，Step2 结论影响 Step3 权重，形成**级联加权**
- `ctx2_score` 有明确的方向性规则：过渡偏低 → TR 中等 → 趋势/突破偏高
- Step4 否决是**硬闸门**：一旦触发，即使 ctx1-3 全部满分也拦截信号
- 可通过 `i_useBrooks4` 一键关闭全部 ctx 评分（分数归零）而不影响系统其他模块

## 各步骤评分细则

### ctx1_score（价位分）
| 因子 | 对分数的影响 |
|------|-------------|
| 价格接近显著高/低点（ph0/pl0、ph1/pl1） | ↑ 价位有意义 |
| 价格接近唐奇安边界（donchH/donchL） | ↑ 处于决策边界 |
| 价格接近 EMA20 | ↑ 动态磁力位 |
| 价格接近区间 50%（fib50） | ↑ 公平价格区域 |
| 价格接近测量移动目标（mmTargetBrooks） | ↑ 有明确目标参照 |
| 价格接近整数关口（nearestRound） | ↑ 机构心理价位 |
| 远离所有关键价位 | ↓ 无参照，随机游走概率高 |

### ctx2_score（阶段分）
| 阶段（brooksPhaseStr） | 分数倾向 | 逻辑 |
|----------------------|---------|------|
| 过渡（Transition*） | 偏低 | 阶段不稳定，方向不明确 |
| 震荡区间（TR） | 中等 | 有边界参照但方向性弱 |
| 趋势·通道（多头/空头） | 偏高 | 方向明确，顺势概率高 |
| 突破（Breakout） | 偏高 | 新阶段启动，动能可能持续 |

过渡判定条件（任一满足即触发）：
1. 前根 `emaSteep` 且本根 `emaFlat`（均线斜率急剧变平，趋势可能结束）
2. 通道内唐奇安宽度扩张：`donchW > donchWAvg × i_donchWidenMul`（波动率突然放大，区间可能突破）

### ctx3_score（动能分）
| 因子 | 方向 | 说明 |
|------|------|------|
| 重叠度 `avgOlp` | 越低 → 分越高 | 棒线重叠少 = 动能强、趋势健康 |
| 均线斜率 `emaSteep` | 陡峭 → 分越高 | 趋势有惯性支撑 |
| 均线走平 `emaFlat` | 走平 → 压低分 | 动能衰减信号 |
| 紧急/衰竭 `emergExit` | 触发 → 大幅压低 | 「紧急/衰竭触发」出现在 ctx3_note |
| 实体强度 | 强实体 → 分高 | 与 5 周期均实体比较 |
| 楔形标记 | 追记标签 | 不直接改分，在 ctx3_note 末尾追加「·楔形」 |

### Step4 — 一票否决
| 否决规则 | 变量 | 条件 |
|---------|------|------|
| TR 内收盘位于区间上半区仍想做多 | `vetoTRlong` | 需 `i_trFadeStrict=true`；`trPosBrooks = (close - donchL)/(donchH - donchL)` ≥ `i_trUpper` |
| TR 内收盘位于区间下半区仍想做空 | `vetoTRshort` | 需 `i_trFadeStrict=true`；`trPosBrooks` ≤ `i_trLower` |
| 紧急逃生 + 顺势结构（防追价） | `vetoEmergL` / `vetoEmergS` | `i_vetoEmergTrend=true`（默认开启）；emergExit + 顺势方向 |

否决文案聚合于 `brooksVetoTxt`。最终信号逻辑：
```
longSig  = longSigRaw and not (i_brooksVetoHard and brooksVeto*)
shortSig = shortSigRaw and not (i_brooksVetoHard and brooksVeto*)
```
即 `i_brooksVetoHard` 关闭时否决仅展示文案不拦截信号。

## 与相关概念的关系
- [[brooks-four-step-context]]：父概念，四步框架的整体描述
- [[support-resistance|Support/Resistance]]：ctx1_score 的 S/R 检测理论基础
- [[fsm-market-cycle]]：ctx2_score 的阶段判定引擎
- [[emergency-exit]]：ctx3_score 的衰竭因子 + Step4 否决的动能来源
- [[signal-scoring-synthesis]]：互补评分体系（lFin/sFin 评信号质量，ctx评交易环境）
- [[measured-move]]：Step1 的 MM 目标计算理论基础
- [[fifty-percent-pullback]]：Step1 的 fib50 理论基础
- [[trading-range-quality]]：Step4 TR 否决的区间判定基础

## 实战应用
开启 `i_useBrooks4` 后，按以下优先级评估：① 先看否决文案（有否决=无条件放弃）→ ② 看 ctx2_score（阶段方向）→ ③ 看 ctx1_score（价位有意义吗）→ ④ 看 ctx3_score（动能健康吗）。三个分数均 > 0.5 且无否决时，上下文处于"绿灯"状态。

## 来源支撑
- [[article-20250519-brooks-context-4-pine]]
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码的 ctx1/ctx2/ctx3 精确公式——WG 系列中最完整的嵌入式 Brooks 四步实现，ctx1=加权加法、ctx2=五档硬编码、ctx3=四因子加权）
- [[article-huangzongprice-context-engine-v1]]（完整 Pine Script 源码，给出了此前未公开的评分公式）
- [[article-huangzongprice-context-engine-v2]]（v2 保留 v1 的透明公式结构，新增 API data_window 导出）
- [[article-huangzongprice-context-engine-v6]]（v6：Step 3 拆为 momentumScore + healthScore，精确加权公式公开）

## v1 源码揭示的评分公式（2026-05-20 更新）

> 以下来自 `brooks_pa_context_engine_v1.txt` 的源码分析。该脚本是 huangzongprice 的 standalone Context Engine，拥有自己的评分流水线，不同于 WG_V15 的嵌入式 Context Engine 子模块。

### 位置评分（ctx1 对应 `locScore`）的聚合方式
**不是加权平均，而是阈值判定 + 加减分**。基础分 0.10，每个条件独立加减分：

| 条件 | 加分/减分 |
|------|----------|
| at 支撑/阻力（≤0.60 ATR） | +0.30 |
| near 支撑/阻力（≤1.20 ATR） | +0.18 |
| near Fib50（≤0.80 ATR） | +0.08 |
| close ≤ EMA20+0.3×ATR | +0.05 |
| midRange 区间中部 | -0.28 |
| lateBreakout 追价 | -0.20 |
| at 对向阻力/支撑 | -0.28 |
| near 对向阻力/支撑 | -0.14 |
| target 目标位临近 | -0.16 |

最终 `f_clamp01(总分)` 钳位到 [0,1]。

### 阶段评分（ctx2 对应 `phaseScore`）的聚合方式
基础分 0.08，按阶段状态和方向加减分：
- 趋势健康：+0.52 / 趋势弱化：+0.30 / 仅趋势：+0.20
- 逆势+弱化+near S/R：+0.22
- 震荡+near S/R：+0.24+0.12
- 双向且不近 S/R：-0.14
- 逆势趋势健康：-0.26

### 动能评分（ctx3 对应 `momScore`）的五因子公式
```
momScore = f_clamp01(
    0.10 + impulseScore × 0.30 + trendHealth × 0.28
    - trendMaturity × 0.20 - exhaustRisk × 0.18 - legWeakening × 0.12
)
```
详见 [[position-layer-scoring]]、[[trend-maturity]]、[[late-breakout]]。

### 综合背景分权重
`bgScore = locScore×0.40 + phaseScore×0.35 + momScore×0.25`

### 否决条件（4 类，此前 ctx-scoring 仅记录 2 类）
1. 区间中部 + 震荡阶段
2. 逆势趋势健康 + 对向衰竭风险低
3. 阻力位追价做多 / 支撑位追价做空
4. 成熟度或衰竭风险高 + 目标位临近

## v6 动量/健康度精确公式

> 以下来自 [[article-huangzongprice-pa-context-engine-v6]]（`@version=6.txt` 源码）。

v6 将 Step 3 拆分为两个独立评分：

### momentumScore（动能分）五因子加权
```
100 × clamp(
    trendBarPower × 0.30 + slopePower × 0.20 + distancePower × 0.15
  + efficiencyPower × 0.20 + overlapPower × 0.15
, 0, 1)
```

### healthScore（健康度）四正一罚
```
100 × clamp(
    efficiencyPower × 0.35 + overlapPower × 0.25 + bodyQuality × 0.20
  + (1 - extensionPenalty) × 0.20 - climaxPenalty
, 0, 1)
```
高潮惩罚触发条件：`|distFromEMA| > 2.2×ATR` 且反向影线 > 35% → 扣 0.15。

详细公式解析和因子含义见 [[momentum-health]]。

## WG_V15 源码验证（来自 Pine Script，2026-05-19 更新）

**WG_V15 嵌入式 Context Engine 的精确公式**：

**ctx1_score**：`clamp01(ctx1_keyScore×0.52 + (gravOK?0.33:0.12) + (mmDistAtr<0.55?0.13:0.0) + (nearRoundBr?0.08:0.0))`——引力场和 MM 距离是独立加成，不是 ctx1_keyScore 的子因子。基准分 0.12（无引力时），引力触发跳至 0.33。

**ctx2_score**：五档硬编码——过渡 0.46 / 震荡 0.52 / 通道 0.76 / 突破 0.84 / 默认 0.55。

**ctx3_score**：`olpHealth×0.38 + slopePart + emergPart + bodPart`——斜率是最大的单一贡献者（0.18~0.32，占比 18%~32%），紧急逃生否给 0.26 固定分。

**TR 否决阈值**：`i_trUpper=0.65, i_trLower=0.35`（`trPosBrooks = (close-donchL)/(donchH-donchL)`）。

## 矛盾与待验证
- ~~具体评分公式未公开~~ → **已解决**：v1 Context Engine 和 WG_V15 Pine Script 源码均已揭示完整公式
- ~~`i_donchWidenMul` 参数值~~ → 已确认：默认 1.15（`donchW > donchWAvg × 1.15`）
- ~~ctx1_score 聚合方式~~ → **已解决**：WG_V15 使用加权加法（非 v1 的加减分制），核心权重 0.52 + 引力/MM/整数独立加成
- ~~v1 vs WG_V15 评分方式差异~~ → **已解决**：v1 用加减分制（基础分 0.10 + 条件加减），WG_V15 用加权加法（minKeyAtr 衰减×0.52 + 独立加成）——两种不同的量化策略
- ~~`i_trUpper` / `i_trLower`~~ → **已确认**：默认 0.65 / 0.35
- `i_trUpper` / `i_trLower` 在 WG_V15 中仍未知，v1 不使用 TR 位置否决（改为区间中部否决）
- v6 权重分配的优化依据未验证（经验调参 vs 回测优化）
