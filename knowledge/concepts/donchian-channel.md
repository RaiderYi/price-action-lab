---
title: "唐奇安通道"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, wedge, failed-breakout]
tags: [atr, fsm, donchl, donchh, brooks]
difficulty: intermediate
related: [fsm-market-cycle, trading-range-quality, support-resistance, fsm-strategy-constraints, brooks-four-step-context, article-20260519-wedge-gravity-brooks-v1-pine, background-scoring-engine, gravity-field, atr-scaling, late-breakout, article-huangzongprice-wedge-gravity-v41-fixed, article-wg-v15-analysis, article-20250519-brooks-context-4-pine]
char_count: 4242
---
# 唐奇安通道

## 一句话定义
基于 N 周期最高/最低价的动态通道——在 WG 系统中扮演 FSM 边界、TR 区域定位和过渡检测三重角色。

## 核心要点
- **标准定义**：`donchH = highest(high, N)`，`donchL = lowest(low, N)`，WG 默认 N=20
- **角色一：FSM 状态边界**。唐奇安上/下轨是 BREAKOUT → CHANNEL → TRADING_RANGE → NEW_BREAKOUT 循环的核心边界——突破必须创通道新高/低
- **角色二：TR 区域定位**。`trPosBrooks = (close - donchL) / (donchH - donchL)` 计算收盘在区间中的比例位置，用于 Brooks Step4 TR 区位否决（上 65% 禁多、下 35% 禁空）和 FSM 策略约束（仅在边界附近交易）
- **角色三：过渡检测**。`donchWiden = donchW > donchWAvg × 1.15`——当通道宽度扩张超过均值的 1.15 倍时，视为市场可能进入过渡/突破阶段，影响 Brooks Step2 的阶段判定
- **Path-B 保守突破**：TR 中需连续 3 根收盘维持在唐奇安外侧才确认新突破——防止假突破
- **不含当前 Bar 的历史边界**：`donchHPrev = highest(high[1], N)` 用于突破判断，避免当前 K 线自身触发边界突破的循环依赖
- **面板展示**：右上角面板第 6/7 行显示当前上/下轨价格 + 靠近标记

## 与相关概念的关系
- [[fsm-market-cycle]]：唐奇安是 FSM 状态机的「标尺」——所有状态转换条件都依赖唐奇安边界
- [[trading-range-quality]]：唐奇安宽度 + 位置比例是量化 TR 质量的连续版本——WR 的「≥8根 K + ≥2 次边界测试」在代码中用唐奇安通道近似
- [[support-resistance|Support/Resistance]]：唐奇安上下轨本身就是动态 S/R——在 Brooks Step1 的 7 种 S/R 中，donchH/donchL 被作为关键位之一参与 ctx1_score 计算
- [[fsm-strategy-constraints]]：唐奇安边界的 `nearDonchH`/`nearDonchL` 直接决定 TR 中的方向许可
- [[brooks-four-step-context]]：唐奇安宽度扩张 (`donchWiden`) 是 Brooks Step2 过渡检测的辅助信号

## 实战应用
在图表上观察唐奇安通道（橙色阶梯线）：价格在通道内 = 震荡/通道阶段，价格突破上轨 = 警惕新突破（Path-A 即时 / Path-B 等 3 根确认），通道突然变宽 = 过渡信号。

## 来源支撑
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — Pine Script 源码，第 133–140 行定义唐奇安计算，第 224–249 行定义 Path-A/B 突破，第 731–759 行定义 TR 边界入场逻辑

## 矛盾与待验证
- **N=20 的普适性**：20 周期唐奇安是经验参数，在不同时间框架（日线/4H/30min）上可能需要调整
- **Path-B 的 3 根确认**：3 根 K 线在 30min 图上 = 1.5 小时，可能错过最佳入场时机——保守与及时性的经典权衡
- **宽度扩张的 1.15 倍阈值**：在低波动环境下可能频繁误触发过渡信号，需要 ATR 确认


---

## Merged Content (from donchian-channel-scaffold)

# 唐奇安通道定位网格

## 一句话定义
WG Brooks V4.1 中，以 20 周期唐奇安通道为坐标系将所有价格位置划分为 5 个功能区域，驱动 Location 背景评分的加减分逻辑。

## 核心要点

### 为什么要用唐奇安通道做坐标？
- Brooks 原著强调「市场在什么价位」是分析背景的第一步
- 唐奇安通道（N=20）提供了一个**动态的、自适应的矩形框架**：上轨=近期最高价、下轨=近期最低价、中轨=(上+下)/2
- 相比固定 S/R 位（ph0/pl0），唐奇安通道更擅长捕捉「当前市场正在交易的区间」

### 五个位置区域

| 区域 | 判定条件 | 评分效应 | 策略含义 |
|------|---------|---------|---------|
| **多头支撑区** | `distToPl0Atr ≤ 0.60` 或 `distToDonchLAtr ≤ 0.60` | +0.30（at） / +0.18（near ≤1.20） | 买在支撑附近 |
| **空头阻力区** | `distToPh0Atr ≤ 0.60` 或 `distToDonchHAtr ≤ 0.60` | +0.30（at） / +0.18（near ≤1.20） | 卖在阻力附近 |
| **中部无人区** | `abs(close - donchMid) ≤ donchSpan × 0.20` 且 `bullSupportDist > 1.0` 且 `bearResistDist > 1.0` | **−0.28**（最大单项扣分） | 中部不交易 |
| **晚突破陷阱** | 做多：`close > donchHPrev + 0.60×ATR` + 不近空头阻力 | **−0.20** | 追价风险 |
|  | 做空：`close < donchLPrev - 0.60×ATR` + 不近多头支撑 | **−0.20** | 追价风险 |
| **目标位迫近** | 做多：距 donchH ≤ 0.80 ATR | **−0.16** | 盈亏比恶化 |
|  | 做空：距 donchL ≤ 0.80 ATR | **−0.16** | 盈亏比恶化 |

### 距离度量：ATR 归一化

所有距离统一用 `math.abs(close - level) / atr14` 归一化（函数 `f_distAtr`），消除不同品种/时间周期的尺度差异。`bullSupportDist` 取 `pl0/donchL/EMA20/fib50` 四个支撑位中最近的距离。

### 在 FSM 中的角色

唐奇安通道同时是 FSM 状态转移的核心基础设施：
- **Path-A 突破**：收盘超越 `donchHPrev + 0.5×ATR20` 且 high ≥ donchH → `fsm = 3`
- **Path-B 突破**：连续 3 根 K 线收盘在唐奇安同侧边界外 → `fsm = 3`
- **ch2rng**：突破最近分型（ph0/pl0）→ `fsm = 2`

即唐奇安通道既是**空间坐标系**（在哪里），也是**状态切换器**（是什么阶段）。

## 与相关概念的关系

- [[support-resistance|Support/Resistance]]：唐奇安通道是 Brooks S/R 体系中「由计算机计算的精确 S/R」概念的 Pine 实现——上轨/下轨即动态阻力/支撑
- [[fsm-market-cycle]]：唐奇安边界是 FSM 状态转移的触发条件，中轨用于 midRange 判定
- [[background-scoring-engine]]：Location 层（40%权重）的评分完全基于唐奇安定位网格
- [[gravity-field]]：引力场与唐奇安网格互补——引力场判断「值不值得交易」，唐奇安网格判断「位置好不好」
- [[atr-scaling]]：距离归一化依赖 ATR 标尺
- [[late-breakout]]：晚突破概念即「价格已超越唐奇安前边界但还未触发新突破」的状态

## 实战应用

快速判断位置优劣的口诀：
> 「边界附近好，中部不做；追价扣分，目标压分。」

- 中部位置（-0.28）是最重的单项扣分——它不仅压低 locScore，还可能与 phaseIsRange 组合触发表决（bgVeto）
- 即使信号棒满分（signalBarScore=1.0），在中部位置也很难达到 bgThr=0.58
- `lateBreakout` 追价扣分 -0.20 是设计用来防止突破后再追的 FOMO 交易

## 来源支撑

- [[article-huangzongprice-wedge-gravity-v41-fixed]]（V4.1 源码：f_distAtr/donchH/donchL/donchMid/midRangeLocation/lateBreakout 等变量的首次完整定义）
- [[article-wg-v15-analysis]]（WG V1.5 分析中提及唐奇安通道用于 FSM 状态切换和位置判定）
- [[article-20250519-brooks-context-4-pine]]（Step1 价位分析中唐奇安作为 7 种 S/R 源之一）

## 矛盾与待验证

- N=20 是默认值（`i_donchN`，范围 10-60），不同品种/周期的最优 N 值未知。A 股 30 分钟 K 线可能需不同参数。
- `donchMid` 中轨取 (donchH+donchL)/2，即算术中点——非成交量加权或时间加权中点。中轨附近的交易是否在所有市场条件下都应回避，需回测验证。
- `nearBullSupport/nearBearResistance` 的 1.20 ATR 阈值与 `atBullSupport/atBearResistance` 的 0.60 ATR 阈值之间的 0.60-1.20 ATR 灰色地带，加分仅为 +0.18（vs +0.30）。这个分级是否最优待验证。
