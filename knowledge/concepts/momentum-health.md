---
title: "动量健康度（Momentum Health）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, swing, failed-breakout]
tags: [权重, ema, clamp, 衰竭风险, exhaustrisk]
difficulty: intermediate
related: [trend-maturity, emergency-exit, three-push-wedge, background-scoring-engine, position-layer-scoring, fsm-market-cycle, article-20260520-wedge-gravity-brooks-context-v3, climax, brooks-four-step-context, ctx-scoring, trend-strength-filter, anti-repainting, article-huangzongprice-pa-context-engine-v6, momentum-health, article-huangzongprice-context-engine-v6, article-huangzongprice-context-engine-v1, wedge-gravity-dual-core, article-huangzongprice-context-engine-v3-rebuild]
char_count: 13842
---
# 动量健康度（Momentum Health）

## 一句话定义
WG Brooks V3 中评估当前动能质量的五因子综合评分系统——impulse（冲击力）+ trendHealth（趋势健康）+ trendMaturity（成熟度）+ exhaustRisk（衰竭风险）+ currentLegWeakening（当前腿转弱），钳位为 0-1 的 momScore，权重 25% 进入背景评分。

## 核心要点

### 动量分公式（源码精确版）

```
momScoreL = clamp(
  0.10                                    // 基础分
  + impulseScoreL × 0.30                  // 当前棒冲击力
  + trendHealthL × 0.28                   // 趋势跟随健康度
  + swingCompareL × 0.12                  // 最近两段波动力度对比
  + (空头趋势中出现 H2/fallingWedge) ? 0.12 : 0.00   // 反转结构加分
  - trendMaturityL × 0.20                 // 趋势成熟度扣分
  - exhaustRiskL × 0.18                   // 衰竭风险扣分
  - currentLegWeakeningL × 0.12           // 当前腿转弱扣分
  , 0, 1)
```

### 五因子详解

#### 1. impulseScore（冲击力分，权重 0.30）
```
impulseScoreL = clamp(bodyRatio × 0.55 + breakMagL × 0.45, 0, 1)
  bodyRatio = barBody / barRange                   // 实体占比：大实体=强动能
  breakMagL = (close - low) / barRange             // 多头突破幅度：收盘越高越强
```
- 当前单根 K 线的纯动能评估——实体大且收在高位 = 高冲击力
- 空方镜像：`breakMagS = (high - close) / barRange`

#### 2. trendHealth（趋势跟随健康度，权重 0.28）
```
trendHealthL = clamp(
  impulseScoreL × 0.35
  + (emaSteep && emaS3>0 ? 0.25 : emaS3>0 ? 0.12 : 0.00)   // EMA 陡峭性
  + (avgOlp < 0.22 ? 0.20 : avgOlp < 0.32 ? 0.10 : 0.00)   // 低重叠度
  + (emergExit ? 0.00 : 0.20)                                // 无紧急逃生
  , 0, 1)
```
- 评估"趋势是否还在正常运行"——EMA 斜率陡峭 + 低重叠度 + 无逃生信号
- `emaSteep`：3 根内 EMA 位移 > 0.5 ATR，即 EMA 在加速移动
- 紧急逃生触发时，趋势健康直接损失 0.20

#### 3. trendMaturity（趋势成熟度，权重 -0.20）
```
trendMaturityL = clamp(
  (risingWedge ? 0.35 : 0.00)           // 楔形出现
  + (lateBreakoutLong ? 0.25 : 0.00)    // 追价突破
  + (exhCdl ? 0.20 : 0.00)              // 衰竭棒（实体≥avgBody20×1.5 且波幅>ATR14×1.2）
  + (bullTargetNearby ? 0.20 : 0.00)    // 目标位过近（≤0.80 ATR）
  , 0, 1)
```
- **趋势走到哪了？**——楔形 + 追价 + 衰竭棒 + 目标近 = 趋势已老
- 详见 [[trend-maturity]]

#### 4. exhaustRisk（衰竭风险，权重 -0.18）
```
exhaustRiskL = clamp(
  (emergExit ? 0.40 : 0.00)             // 紧急逃生触发
  + (risingWedge ? 0.25 : 0.00)         // 楔形
  + (avgOlp > 0.35 ? 0.15 : 0.00)      // 高重叠度（多空争夺加剧）
  + (bullTargetNearby ? 0.20 : 0.00)   // 目标位过近
  , 0, 1)
```
- **趋势还能走吗？**——与成熟度部分重叠但侧重"危险信号"
- 紧急逃生权重最高（0.40），远大于其他因子

#### 5. currentLegWeakening（当前腿转弱，权重 -0.12）
```
currentLegWeakeningL = clamp(
  (impulseScoreL < impulseScoreL[1] ? 0.30 : 0.00)   // 冲击力递减
  + (avgOlp > 0.30 ? 0.25 : 0.00)                     // 高重叠度
  + (not emaSteep && phaseDir==1 ? 0.20 : 0.00)      // EMA 走平 + 多头趋势
  + (risingWedge ? 0.25 : 0.00)                        // 楔形
  , 0, 1)
```
- **当前推进行是否在减速？**——与前一根 K 线比冲击力、看重叠度变化
- 这是动量五因子中唯一的"环比"指标——直接比较当前与上一根

### 因子关系图

```
                ┌─────────────────┐
                │   momScore      │
                │   = 0.10 +      │
                │   Σ(加分) -     │
                │   Σ(扣分)       │
                └───────┬─────────┘
                        │
        ┌───────┬───────┼───────┬───────┐
        ▼       ▼       ▼       ▼       ▼
   impulse  trendH  trendM  exhaust  legWeak
   +0.30    +0.28   -0.20   -0.18    -0.12
   (当前棒) (趋势)  (阶段)  (危险)   (环比)
```

## 与相关概念的关系
- [[trend-maturity]]：动量健康度的扣分因子之一（-0.20），详见成熟度四因子
- [[emergency-exit]]：当逃生触发时，同时影响 trendHealth（-0.20）和 exhaustRisk（+0.40）
- [[three-push-wedge|Three Push Wedge]]：楔形出现同时影响 trendMaturity（+0.35）、exhaustRisk（+0.25）、currentLegWeakening（+0.25）
- [[background-scoring-engine]]：momScore 以 25% 权重汇入 bgScore，是该引擎的第三层输入
- [[position-layer-scoring]] / [[fsm-market-cycle]]：分别提供 bgScore 的另两层输入（40%/35%）

## 实战应用
- `momScoreL` < 0.40：动能不支持做多，即使位置层和阶段层有利，bgScore 也很难达到 0.58
- `exhaustRiskL` > 0.60：衰竭风险极高——在信息面板中会以紫色高亮显示
- `currentLegWeakeningL` > 0.50 + `trendMaturityL` > 0.60 → 大概率触发背景否决

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 完整 Pine Script 源码，第 670-726 行）

## 矛盾与待验证
- 五因子的权重（0.30/0.28/-0.20/-0.18/-0.12）和内部子权重均为经验参数，未经回测优化
- exhaustRisk 和 trendMaturity 共享多个因子（楔形、目标临近），存在重叠——两者同时扣分可能对同一场景双重惩罚
- currentLegWeakening 使用 `impulseScoreL < impulseScoreL[1]` 做环比——一根 K 线的冲击力波动可能引入噪音


---

## Merged Content (from momentum-health-dual-score)

# 动能-健康度双评分（Momentum-Health Dual Score）

## 一句话定义
v6 背景引擎将 Step 3「动能评估」拆分为两个独立评分体系——动能分评估趋势推力强度，健康度评估趋势可持续性——并首次公开精确加权公式。

## 核心要点
- **拆分动机**：动能强 ≠ 趋势健康。一段价格可以动能很强（快速推进）但已处于高潮衰竭区（不健康）
- **动量分（momentumScore）**：回答「趋势推力有多强？」
- **健康度分（healthScore）**：回答「这个趋势还能持续多久？」
- 两个分数均映射到 0-100 连续值，在状态面板分两行展示
- 此前版本（v1/v2/WG_V15）的 `ctx3_score` 是笼统的单一动能分，v6 是首次将二者拆分的公开实现

## 动能分公式（五因子加权）

```
momentumScore = 100 × clamp(
    trendBarPower × 0.30   // 趋势棒比例（收盘靠近极值）
  + slopePower   × 0.20   // 均线斜率强度
  + distancePower × 0.15  // 价格距 EMA 距离
  + efficiencyPower × 0.20 // 推进效率
  + overlapPower × 0.15   // (1 - 平均重叠度)
  , 0.0, 1.0)
```

| 因子 | 含义 | 标准化方式 | 权重 |
|------|------|-----------|------|
| `trendBarPower` | 趋势棒比例（收盘靠极值 + 实体>均值） | / 0.60 归一化 | 30% |
| `slopePower` | EMA20 斜率（绝对值） | / 1.2 归一化 | 20% |
| `distancePower` | 价格距 EMA20 距离（绝对值） | / 2.5 归一化 | 15% |
| `efficiencyPower` | 推进效率 = |C[n]-C[0]| / 总路径 | / 0.70 归一化 | 20% |
| `overlapPower` | 1 - 平均K线重叠度 | / 0.70 归一化 | 15% |

评分等级：≥75 强 → ≥55 中等 → ≥35 偏弱 → <35 很弱

## 健康度分公式（四正一罚）

```
healthScore = 100 × clamp(
    efficiencyPower × 0.35     // 效率（最大权重）
  + overlapPower   × 0.25     // 少重叠 = 健康
  + bodyQuality    × 0.20     // 实体质量（实体/振幅比）
  + (1 - extensionPenalty) × 0.20  // 越不超买超卖越健康
  - climaxPenalty              // 高潮惩罚（条件触发）
  , 0.0, 1.0)
```

| 因子 | 含义 | 权重 | 备注 |
|------|------|------|------|
| `efficiencyPower` | 推进效率 | 35% | 健康度最大权重——效率是趋势生命力的核心指标 |
| `overlapPower` | 1 - 平均重叠度 | 25% | 重叠少 = K线干净推进，趋势健康 |
| `bodyQuality` | 实体/振幅比 的 20 周期均值 | 20% | 实体占比高 = 方向明确 |
| `1 - extensionPenalty` | 价格不过度偏离 EMA | 20% | 偏离 > 1.8×ATR 时开始惩罚，越远惩罚越大 |
| `climaxPenalty` | 高潮惩罚 | 减分 | 条件：`|distFromEMA| > 2.2×ATR` 且反向影线 > 35% → 减 0.15 |

评分等级：≥75 健康 → ≥55 稳健 → ≥35 衰减 → <35 衰竭

## 高潮惩罚详解

```pinescript
climaxPenalty = abs(distFromEMAatr) > 2.2*ATR  // 价格极端偏离
                and climaxWick > 0.35           // 反向影线占比 > 35%
                ? 0.15                          // 触发惩罚
                : 0.0
```

`climaxWick` 根据主导方向选择：上涨趋势看上影线占比，下跌趋势看下影线占比。这实现了 Brooks 的高潮/竭尽概念（参见 [[climax]]）的量化检测。

## 与相关概念的关系
- [[brooks-four-step-context]]：v6 的 Step 3 由动能+健康度双评分组成
- [[ctx-scoring]]：此前 ctx3_score 的单一评分被 v6 拆分为双评分
- [[trend-strength-filter]]：v3 趋势强度四维评估与 v6 动能/健康度互补——trend-strength-filter 决定是否屏蔽逆势信号，momentum-health 评估当前背景质量
- [[climax]]：健康度分的高潮惩罚直接映射 Brooks 高潮概念
- [[anti-repainting]]：所有评分输入基于无重绘数据

## 实战应用
在 v6 状态面板上观察两行评分：
- 动能高 + 健康度高 → 最强背景，顺势信号最可靠
- 动能高 + 健康度低 → 趋势可能接近尾声，警惕反转
- 动能低 + 健康度高 → 趋势稳固但推进慢（慢牛/慢熊），适合波段
- 动能低 + 健康度低 → 最弱背景，避免入场

## 来源支撑
- [[article-huangzongprice-pa-context-engine-v6]]（Pine Script v6 源码 Step 3，第 133-162 行）

## 矛盾与待验证
- 权重分配（30%/20%/15%/20%/15% 和 35%/25%/20%/20%）的优化依据未说明——可能是经验调参，需要回测验证
- `climaxDistATR=2.2` 在不同品种/周期上可能需要重新校准


---

## Merged Content (from momentum-health-dual-scoring)

# 动能-健康度双评分（Momentum-Health Dual Scoring）

## 一句话定义
V6 将 Brooks Step3（动能评估）拆为两个独立 0-100 评分——动量分衡量「趋势推动力有多强」，健康分衡量「当前趋势是否健康可持续」——两者互补但可背离（强势不健康 = 高潮衰竭）。

## 核心要点

### 双评分设计理由

传统单维动能分（如 `ctx3_score`）混合了「推力」和「可持续性」两个不同维度。V6 的决定性创新是拆分：
- **动能分高 + 健康分低** → 高潮/衰竭状态（推力强但不可持续）
- **动能分低 + 健康分高** → 稳健推进（推力不强但结构良好）
- **动能分高 + 健康分高** → 最佳状态（强势且健康）
- **动能分低 + 健康分低** → 混沌/衰退（无推力且结构恶化）

### momentumScore（动能评分）

```
100 × clamp(
    trendBarPower × 0.30    ← 高质量趋势K线占比
  + slopePower   × 0.20    ← EMA斜率强度
  + distancePower × 0.15   ← 价格偏离EMA幅度
  + efficiencyPower × 0.20 ← 趋势推进效率
  + overlapPower  × 0.15   ← 非重叠度
, 0, 1)
```

#### 五因子逐一解释

| # | 因子 | 权重 | 计算方式 | 高分代表 |
|---|------|------|---------|---------|
| 1 | **trendBarPower** | 30% | `f_norm01(directionalRatio, 0.60)` — 主导方向的高质量趋势K线占比 | 70%+的K线收在极值端 |
| 2 | **slopePower** | 20% | `f_norm01(|emaSlopeATR|, 1.2)` — EMA斜率归一化 | EMA陡峭推进 |
| 3 | **distancePower** | 15% | `f_norm01(|distFromEMAatr|, 2.5)` — 价格偏离EMA程度 | 价格远离均线（趋势强） |
| 4 | **efficiencyPower** | 20% | `f_norm01(efficiency, 0.70)` — 趋势效率 | 价格推进顺畅 |
| 5 | **overlapPower** | 15% | `f_norm01(1.0−avgOverlap, 0.70)` — 非重叠度 | K线之间重叠少 |

四档分级：≥75 强 / ≥55 中等 / ≥35 偏弱 / <35 很弱

### healthScore（健康度评分）

```
100 × clamp(
    efficiencyPower     × 0.35   ← 趋势效率（最大权重）
  + overlapPower        × 0.25   ← 非重叠度
  + bodyQuality         × 0.20   ← K线实体质量
  + (1−extensionPenalty) × 0.20  ← 非过度延伸
  − climaxPenalty                 ← 高潮惩罚（减法项）
, 0, 1)
```

#### 四正因子 + 一惩罚项

| # | 因子 | 权重 | 计算方式 | 高分代表 |
|---|------|------|---------|---------|
| 1 | **efficiencyPower** | 35% | 同动量分 | 趋势推进顺畅 |
| 2 | **overlapPower** | 25% | 同动量分 | K线不重叠 |
| 3 | **bodyQuality** | 20% | `f_norm01(body/barRange的SMA, 0.70)` | 实体占比高（非十字星） |
| 4 | **1−extensionPenalty** | 20% | 过度延伸惩罚 = `(|distFromEMA|−1.8)/1.8` 钳位 | 价格不过度远离EMA |
| − | **climaxPenalty** | −0.15 | 触发条件：`|distFromEMA| > 2.2×ATR` 且反向影线 > 35% | 高潮减分 |

四档分级：≥75 健康 / ≥55 稳健 / ≥35 衰减 / <35 衰竭

### 高潮惩罚触发条件

```
climaxDistATR = 2.2   ← 默认：价格偏离EMA超过2.2倍ATR
climaxWick > 0.35     ← 反向影线超过波幅的35%
→ climaxPenalty = 0.15（从healthScore直接扣除）
```

这是 V6 中最精妙的机制之一：当价格远离 EMA 且出现长反向影线时，即使动能分很高，健康分也会被显著压低——形成「强动能+低健康」的高潮警告。

## 与 ctx3_score 的对比

| 维度 | ctx3_score（v1/WG_V15） | momentumScore + healthScore（V6） |
|------|------------------------|----------------------------------|
| 结构 | 单维 0-1 分 | 双维 0-100 分 |
| 因子数 | 5（含正负混合） | momentum 5正 / health 4正1罚 |
| 高潮处理 | 隐式（通过衰竭风险压低总分） | 显式（独立高潮惩罚项，−0.15） |
| 过度延伸 | 不单独建模 | 独立 extensionPenalty（20%权重） |
| 可解释性 | 「动能偏弱」→ 无法区分原因 | 「动能强/健康衰减」→ 精确诊断 |
| 权重透明度 | 部分未公开 | 全部精确公开 |

## 与相关概念的关系

- [[ctx-scoring]]：V6 的动量/健康双评是对 ctx3_score 的拆分重构——ctx-scoring 页面已收录 v6 公式
- [[background-scoring-engine]]：V5/V4 的 momScore（动量×25%）是 V6 双评的前身——V6 将 25% 的二级子项升级为独立的并行维度
- [[trend-strength-filter]]：动量分的 trendBarPower + efficiencyPower 共同衡量趋势强度
- [[climax]]：高潮惩罚是 Brooks 高潮理论的量化实现——`|distFromEMA| > 2.2×ATR + 反向影线 > 35%`
- [[momentum-health]]：如果该页面存在，V6 提供了一个工程化的精确实现

## 实战应用

在 V6 状态面板中，两行并列显示：
```
动能评分  65 / 100  中等     ← 绿色(≥75)/黄色(≥55)/橙色(≥35)/红色(<35)
健康度    42 / 100  衰减     ← 同上
```

交易者解读：
- 动能中等 + 健康衰减 → 趋势在减弱，可能即将进入震荡或反转
- 动能强 + 健康健康 → 最佳入场环境
- 动能很强 + 健康衰竭 → 高潮状态，追价风险极高
- 动能很弱 + 健康健康 → 稳健但缺乏推力——可能只是盘整而非趋势

## 来源支撑

- [[article-huangzongprice-context-engine-v6]]（V6 源码，第 135-162 行——五因子公式精确权重）
- [[article-huangzongprice-context-engine-v1]]（v1 的 ctx3_score 五因子公式是 V6 双评的祖代码）

## 矛盾与待验证

- 五因子权重（30/20/15/20/15）和四正一罚权重（35/25/20/20/−15）全部基于经验调参，未经验证数据集优化
- trendBarPower 使用 30% 最高权重，但「趋势K线」的定义（收在极值端的质量K线）依赖 `closeExtremePct=0.25` 阈值——这个阈值是否跨品种/周期稳定？
- 健康度的四正因子中有两个（efficiencyPower、overlapPower）与动量分完全重叠——去重后健康度的独立信息量可能被高估
- 高潮惩罚的 0.15 是固定值而非比例值——在极端高潮中这个惩罚可能严重不足


---

## Merged Content (from momentum-health-framework)

# 动能健康框架（Momentum Health Framework）

## 一句话定义
背景评分引擎动量层（25%权重）的四子评分互锁系统——trendHealth（动能健康）和 impulse（冲动质量）为加分项，trendMaturity（成熟度）、exhaustRisk（衰竭风险）、currentLegWeakening（当前腿弱化）为扣分项，综合产出 momScore。

## 核心要点

### 总公式

```
momScore = clamp(0.10 + impulse×0.30 + trendHealth×0.28 + swingCompare×0.12
                 + bonus − trendMaturity×0.20 − exhaustRisk×0.18 − legWeakening×0.12)
```

### 四子评分详解

#### 1. trendHealth（趋势健康度，权重 +0.28）——「动能还强吗？」

```
trendHealth = clamp(impulseScore×0.35 + slopeScore×0.25 + overlapScore×0.20 + escapeScore×0.20)
```

| 子因子 | 多头条件 | 空头条件 | 说明 |
|-------|---------|---------|------|
| impulseScore | bodyRatio×0.55 + breakMag×0.45 | 镜像 | 实体占比 + 收盘突破幅度 |
| slopeScore | EMA陡峭且向上→0.25 else 向上→0.12 | EMA陡峭且向下 | EMA20的3-period斜率 |
| overlapScore | avgOlp<0.22→0.20 else <0.32→0.10 | 相同 | 低重叠度=强趋势 |
| escapeScore | emergExit→0.0 else→0.20 | 相同 | 无紧急逃生标记=满分 |

#### 2. trendMaturity（趋势成熟度，权重 −0.20）——「走了多远了？」

```
trendMaturity = clamp(wedge×0.35 + lateBreakout×0.25 + climax×0.20 + target×0.20)
```

详见 [[trend-maturity]]。高成熟度扣减动量分——市场已走很远，继续顺势的风险回报比恶化。

#### 3. exhaustRisk（衰竭风险，权重 −0.18）——「还能走吗？」

```
exhaustRisk = clamp(emergency×0.40 + wedge×0.25 + overlapHigh×0.15 + target×0.20)
```

| 子因子 | 条件 | 权重 |
|-------|------|:---:|
| emergExit | 假突破/衰竭/竭尽任一触发 | 0.40 |
| wedge | risingWedge(空头衰竭) / fallingWedge(多头衰竭) | 0.25 |
| overlapHigh | avgOlp > 0.35 | 0.15 |
| target | bullTargetNearby(多) / bearTargetNearby(空) | 0.20 |

**与 trendMaturity 的区别**：成熟度问「走了多远」，衰竭风险问「还能走吗」。两者有因子交叉（楔形、目标位都出现在两边），但权重和解释不同——成熟度偏时间/阶段维度，衰竭偏动能/质量维度。

#### 4. currentLegWeakening（当前腿弱化，权重 −0.12）——「当前这腿还行吗？」

```
currentLegWeakening = clamp(impulseDecline×0.30 + overlapHigh×0.25 + slopeLoss×0.20 + wedge×0.25)
```

| 子因子 | 条件 |
|-------|------|
| impulseDecline | 当前 impulseScore < 前一根的 impulseScore |
| overlapHigh | avgOlp > 0.30 |
| slopeLoss | not emaSteep（多头+向上 or 空头+向下） |
| wedge | 对应方向的楔形 |

**独特价值**：前三个子评分（health/maturity/exhaust）看的是「趋势」层面的状态，legWeakening 看的是「当前腿」的即时变化——即使整体趋势健康，如果当前腿已显弱化（冲击减弱+重叠上升+斜率丧失），顺势入场的即时风险升高。

### 特殊加分：反转情境

```
bonusL = (phaseDir==-1 and (fallingWedge or h2)) ? 0.12 : 0.0
bonusS = (phaseDir==1  and (risingWedge  or l2)) ? 0.12 : 0.0
```

逆势方向出现楔形或H2/L2结构时，动量层额外加分——因为这些结构标志着原趋势动能可能正在衰竭。

### swingCompare（波动比，权重 +0.12）

```
swingCompare = clamp(1.0 − |swingRatio − 1.0| / 1.5)
swingRatio = |ph0−pl0| / |ph1−pl1|
```

当前波段与前一波段的幅度比越接近1.0，表明趋势节奏稳定，给满分。大幅加速或减速都会扣分——加速可能意味着高潮，减速意味着动能流失。

## 与相关概念的关系
- [[trend-maturity]]：动量健康框架的扣分项之一（−0.20），评估趋势已运行多久
- [[background-scoring-engine]]：momScore 是背景评分引擎的第三层（25%权重）
- [[emergency-exit]]：应急逃生同时影响 trendHealth（escapeScore）和 exhaustRisk（emergency×0.40）
- [[three-push-wedge|Three Push Wedge]]：楔形同时出现在 maturity、exhaustRisk、legWeakening 三个子评分中——是动量层最重要的多信号指标
- [[fsm-market-cycle]]：FSM方向决定 slopeScore 和 bonus 的方向判断
- [[wedge-gravity-dual-core]]：动量健康框架是双核架构→三层引擎中动量层的完整展开

## 实战应用
在信息面板中查看「动能健康 L/S」「成熟度 L/S」「衰竭风险 L/S」三行：
- 动能健康 > 0.70 + 成熟度 < 0.40 + 衰竭风险 < 0.30 → 趋势动能充沛，顺势交易环境最佳
- 成熟度 > 0.60 + 衰竭风险 > 0.55 → 即使背景支持，应警惕反转
- 成熟度 ≥ 0.65 or 衰竭风险 ≥ 0.60 + 腿弱化 ≥ 0.50 → 触发背景否决

## 来源支撑
- [[article-huangzongprice-context-engine-v3-rebuild]]（第544-568行，完整四子评分源码）

## 矛盾与待验证
- 四个子评分的权重（0.28/0.20/0.18/0.12）是经验设定，未经回测优化
- 楔形在 maturity(+0.35)、exhaust(+0.25)、legWeakening(+0.25) 三处出现——楔形出现时动量层可能被多重扣分，是否需要去重？
- swingCompare 使用 |ph0−pl0|/|ph1−pl1| 比较相邻波段，但在TR中摆动幅度波动天然大，此项可能在区间行情中产生误导
