# PA背景分析引擎 v6 — 精简纯背景版

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6 指标）
- 原始位置：`raw/articles/huangzongprice/@version=6.txt`
- 代码行数：251 行（含注释）
- 脚本类型：独立 overlay 指标（纯背景分析，无执行层）
- 版本演进：V5 全栈引擎(1520行) → V6 聚焦精简背景版(251行)

## 一句话摘要
V6 是 huangzongprice Brooks PA 系列从「全栈单体」向「关注点分离」的转折——砍掉楔形/FSM/H2L2/供需区/订单块/执行评分/警报，仅保留核心背景分析四步：支撑阻力定位 → 市场阶段判定 → 动能健康双评 → 一票否决，仅 251 行。

## 核心论点

### V6 vs V5：根本性架构转向

| 维度 | V5 (1520行) | V6 (251行) |
|------|-----------|-----------|
| 定位 | 全栈单体引擎（背景+执行+警报） | 纯背景分析引擎 |
| S/R | 经典枢轴 + S-D Zone + Order Block | 仅经典枢轴（简洁） |
| 阶段判定 | FSM 四状态机 | 效率/重叠度直接判别 |
| 评分体系 | 三层背景(40/35/25) + 执行(55/25/20) | 动能(5因子) + 健康度(5因子) |
| 可视化 | 32行面板 + 楔形连线 + 周期标签 + H2L2 | 8行简洁面板（无楔形/H2L2/S-D/OB） |
| 警报 | 10种 | 0（无警报） |
| 类型系统 | 3个 type (WedgeData/ZoneData/OBData) | 0（无 type） |

核心哲学：**背景是背景，执行是执行**——V6 回归 Brooks 的原始理念「先看懂图，再找信号」。

### 架构总览（四步流水线）

```
OHLC → [防重绘: barstate.isconfirmed]
     → [Step1: 枢轴S/R定位]
     → [Step2: 效率/重叠度 → 四阶段判定]
     → [Step3: 动能评分(5因子) + 健康度评分(5因子-高潮惩罚)]
     → [Step4: 一票否决(6条件)]
     → [可视化: EMA20 + S/R线 + 阶段背景色 + 震荡盒体 + 标签 + 8行面板]
```

### Step 1: 支撑阻力

- 使用 `ta.pivothigh` / `ta.pivotlow` 识别已确认枢轴（长度可配，默认 5）
- 最多保留 6 条历史线（可配），超过自动清理最旧
- 最近 2 个高点和 2 个低点保留为 `lastHigh1/2`、`lastLow1/2`
- 贴近判定：`|price - SR| ≤ ATR × 0.35`（可配）

### Step 2: 市场阶段判定（全新方式）

不再使用 FSM 状态机，改用**效率 + 重叠度 + EMA位置**直接分类：

```
bullContext = (HH>HL 且 LH>LL) 或 (c > EMA20 且 EMA斜率 > 0.12×ATR)
bearContext = (HH<HL 且 LH<LL) 或 (c < EMA20 且 EMA斜率 < -0.12×ATR)

上涨趋势 = 效率 ≥ 0.38 且 重叠度 ≤ 0.42 且 远离EMA(>0.20ATR) 且 bullContext
下跌趋势 = 效率 ≥ 0.38 且 重叠度 ≤ 0.42 且 远离EMA(<-0.20ATR) 且 bearContext
震荡区间 = 效率 ≤ 0.22 且 重叠度 ≥ 0.55 且 贴近EMA(≤0.80ATR)
过渡阶段 = 不满足以上三者
```

**关键参数**（全部可配）：
- 趋势效率阈值：0.38
- 震荡效率阈值：0.22
- 趋势最大重叠度：0.42
- 震荡最小重叠度：0.55

→ 详见 [[efficiency-overlap-classification]]

### Step 3: 动能与健康度双评分

V6 的核心创新：将原来单维的「动能分」拆为两个独立评分。

#### 动能评分（momentumScore）

```
100 × clamp(
    trendBarPower×0.30 + slopePower×0.20 + distancePower×0.15
  + efficiencyPower×0.20 + overlapPower×0.15
, 0, 1)
```

| 因子 | 含义 | 来源 |
|------|------|------|
| trendBarPower (30%) | 趋势K线占比（收在极值端的高质量K线） | bullBarRatio/bearBarRatio |
| slopePower (20%) | EMA斜率强度（归一化到1.2×ATR） | emaSlopeATR |
| distancePower (15%) | 价格偏离EMA程度（归一化到2.5×ATR） | distFromEMAatr |
| efficiencyPower (20%) | 趋势效率（价格推进顺畅度） | efficiency |
| overlapPower (15%) | 非重叠度（1−重叠度，越高动能越强） | 1−avgOverlap |

分级：≥75 强 / ≥55 中等 / ≥35 偏弱 / <35 很弱

#### 健康度评分（healthScore）

```
100 × clamp(
    efficiencyPower×0.35 + overlapPower×0.25
  + bodyQuality×0.20 + (1−extensionPenalty)×0.20
  − climaxPenalty
, 0, 1)
```

| 因子 | 含义 | 权重 |
|------|------|------|
| efficiencyPower | 趋势效率 | 35% |
| overlapPower | 非重叠度 | 25% |
| bodyQuality | K线实体质量（实体/波幅比） | 20% |
| 1−extensionPenalty | 非过度延伸（价格不离EMA太远） | 20% |
| climaxPenalty | 高潮惩罚（远离EMA+反向影线>35%→扣0.15） | 惩罚项 |

分级：≥75 健康 / ≥55 稳健 / ≥35 衰减 / <35 衰竭

→ 详见 [[momentum-health]]

### Step 4: 一票否决（6 条件）

```
震荡区间 → "震荡内优先等待突破"
上涨趋势 + 贴近阻力 → "多头受阻力压制"
下跌趋势 + 贴近支撑 → "空头受支撑压制"
过渡阶段 → "过渡期信号降级"
上涨趋势 → "顺势偏多有效"（非否决）
下跌趋势 → "顺势偏空有效"（非否决）
其他 → "等待更清晰背景"
```

前 4 种为否决状态，后 2 种为绿灯。这与 V5/V4 的 4 类背景否决相似但更简洁。

→ 详见 [[veto-decision-gate]]

### 可视化

- **EMA20**：青色线（可关闭）
- **S/R 线**：红/绿半透明延长线
- **阶段背景色**：绿(涨)/红(跌)/橙(震)/灰(过渡)，透明度 88-90%
- **震荡盒体**：橙色半透明矩形框，离开震荡后保留历史盒体
- **阶段切换标签**：仅在阶段变化时在 K 线位置打中文标签
- **贴近信号**：贴近阻力→红叉"阻"，贴近支撑→绿叉"支"
- **状态面板**：8 行 × 2 列 Table（市场阶段/主导方/位置/动能分/健康度/重叠效率/一票否决）

### 防重绘设计

整份代码统一使用 `barstate.isconfirmed` 保护：未收盘 K 线使用前一根确认 K 线的 OHLC——杜绝 Pine Script 中最常见的重绘陷阱。

## 提取出的新概念

- [[efficiency-overlap-classification]] — V6 的独创阶段判定体系（效率/重叠度四分类，取代 FSM）
- [[momentum-health]] — V6 的动能(5因子) + 健康度(5因子-高潮惩罚)双评系统
- [[veto-decision-gate]] — V6 的 6 条件一票否决闸门（4否决+2绿灯）

## 与现有知识的衔接

### V6 对已有概念的补充
- [[support-resistance|Support/Resistance]]：V6 使用最纯净的枢轴法 S/R，无供需区/OB 掺杂
- [[brooks-four-step-context]]：V6 的四步流水线是 Brooks 四步法的 Pine Script 最简实现
- [[ctx-scoring]]：V6 的四步结构与 ctx1-4 一一对应，但评分方式不同
- [[background-scoring-engine]]：V5/V4 用三层加权(40/35/25)，V6 用效率/重叠直接分类+独立双评
- [[wedge-gravity-dual-core]]：V6 是双核架构演进的「减法分支」——只保留背景核的精华
- [[emergency-exit]]：V6 的一票否决是紧急逃生的概念升级——从 3 条件扩展到 6 条件（含背景/位置/阶段维度）

### V6 的独特性
- **第一个纯背景指标**：在 huangzongprice 系列中，V6 是第一个（也是目前唯一）不包含任何执行层/信号层的纯背景指标
- **效率/重叠度分类体系**：这是全新的市场阶段判定方法，不同于之前所有版本的 FSM 或 EMA/结构混合法
- **251 行的极简主义**：相比 V5 的 1520 行，V6 砍掉了 83% 的代码——证明背景分析的核心逻辑可以被高度浓缩

## 潜在风险
- 效率/重叠度的阈值（0.38/0.22/0.42/0.55）均为经验参数，未验证最优性
- 无警报系统——纯可视化指标，需要交易者自主观察面板和颜色
- 震荡盒体可能在快速切换中产生视觉残留
