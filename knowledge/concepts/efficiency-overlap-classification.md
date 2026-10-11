---
title: "效率-重叠度阶段分类（Efficiency-Overlap Classification）"
phase: [trend, range, breakout, transition]
signal_types: []
tags: [ema, fsm, efficiency, 效率, price]
difficulty: intermediate
related: [fsm-market-cycle, brooks-four-step-context, ctx-scoring, trend-strength-filter, channel-to-trading-range, article-huangzongprice-context-engine-v6]
char_count: 2713
---
# 效率-重叠度阶段分类（Efficiency-Overlap Classification）

## 一句话定义
V6 引入的不依赖 FSM 状态机的市场阶段判定体系——用趋势效率(efficiency)和 K 线重叠度(overlap)两个量化指标 + EMA 位置直接将市场分为「上涨趋势/下跌趋势/震荡区间/过渡阶段」四种状态。

## 核心要点

### 两个核心指标

| 指标 | 计算方式 | 含义 |
|------|---------|------|
| **efficiency**（趋势效率） | `|close − close[N]| / (avgTR × N)` | 价格推进的顺畅程度——高=趋势推进快，低=来回拉锯 |
| **avgOverlap**（平均重叠度） | `SMA(相邻K线重叠/当前波幅, 20)` | K线之间的重叠比例——高=震荡，低=趋势 |

### 四阶段判定公式

```
bullContext = (HH>HL 且 LH>LL) 或 (price>EMA20 且 EMA斜率>0.12×ATR)
bearContext = (HH<HL 且 LH<LL) 或 (price<EMA20 且 EMA斜率<-0.12×ATR)

上涨趋势 = efficiency ≥ 0.38 且 avgOverlap ≤ 0.42 且 price远高于EMA(>0.20ATR) 且 bullContext
下跌趋势 = efficiency ≥ 0.38 且 avgOverlap ≤ 0.42 且 price远低于EMA(<-0.20ATR) 且 bearContext
震荡区间 = efficiency ≤ 0.22 且 avgOverlap ≥ 0.55 且 price贴近EMA(≤0.80ATR)
过渡阶段 = 不满足前三者任一
```

### 可配置阈值

| 参数 | 默认值 | 含义 |
|------|--------|------|
| `effTrendTh` | 0.38 | 趋势效率最低阈值 |
| `effRangeTh` | 0.22 | 震荡效率最高阈值 |
| `overlapTrendTh` | 0.42 | 趋势最大重叠度 |
| `overlapRangeTh` | 0.55 | 震荡最小重叠度 |
| `stageLookback` | 30 | 阶段判断回看K线数 |
| `momLookback` | 20 | 重叠度计算窗口 |

### 四阶段语义

| 阶段 | 背景色 | 典型特征 | 交易含义 |
|------|--------|---------|---------|
| 上涨趋势 | 绿色 | 效率高、重叠低、价格在EMA上方、HH/HL递升 | 顺势做多，背景绿灯 |
| 下跌趋势 | 红色 | 效率高、重叠低、价格在EMA下方、HH/HL递降 | 顺势做空，背景绿灯 |
| 震荡区间 | 橙色 | 效率低、重叠高、价格贴近EMA | 等待突破，缩小仓位 |
| 过渡阶段 | 灰色 | 不满足前三者——方向切换中 | 信号降级，谨慎入场 |

## 与 FSM 分类的对比

| 维度 | FSM 四状态机 | 效率-重叠度分类 |
|------|-------------|----------------|
| 状态数 | 4 (BREAKOUT/CHANNEL/TR/NEW_BREAKOUT) | 4 (涨/跌/震/过渡) |
| 判定方式 | 状态转移规则+方向许可 | 效率+重叠度直接阈值判定 |
| 方向性 | 无内置方向（依赖单独的方向判定） | 内置多空方向 |
| 复杂度 | 需要4×4转移矩阵+置信度调整 | 4个if条件，一行代码 |
| 代表性版本 | WG V1.5/V4.1/V5 | V6 |
| 代码量 | ~200行（含转移逻辑） | ~20行 |

**核心差异**：FSM 关注「市场处于周期的哪个位置」（突破→通道→震荡→新突破），效率-重叠分类关注「当前K线行为的统计特征」（推进效率+重叠程度），后者更接近 Brooks 的「看K线本身说话」哲学。

## 与相关概念的关系

- [[fsm-market-cycle]]：V6 废弃 FSM 改用效率/重叠分类——这是 huangzongprice 系列中阶段判定的最大一次范式转换
- [[brooks-four-step-context]]：V6 的 Step2（阶段判定）完全对应 Brooks Step2——判断市场处于趋势还是震荡
- [[ctx-scoring]]：`ctx2_score` 的判定方式（FSM + 过渡检测）与 V6 的效率/重叠法互为替代方案
- [[trend-strength-filter]]：效率指标本身就衡量趋势强度——效率>0.38 等价于「趋势足够强」
- [[channel-to-trading-range]]：重叠度从低到高的转变 = 通道向区间的演变——V6 用重叠度阈值 0.42→0.55 量化了这个过程

## 实战应用

在 V6 指标中，阶段判定控制三个可视化元素：
- **背景色**：整张图按阶段着色，肉眼即可判断当前处于什么环境
- **震荡盒体**：仅在「震荡区间」阶段绘制，离开震荡后保留历史盒体
- **阶段标签**：仅在阶段切换时打中文标签（不重复标注）

交易者使用 V6 时的工作流：
1. 看一眼背景色 → 知道当前阶段
2. 如果橙色（震荡）→ 等待或缩小仓位
3. 如果灰色（过渡）→ 不急于入场，等阶段明确
4. 如果绿色/红色（趋势）→ 再看动能/健康度评分确认趋势质量

## 来源支撑

- [[article-huangzongprice-context-engine-v6]]（V6 源码，第 105-130 行）

## 矛盾与待验证

- 四个阈值（0.38/0.22/0.42/0.55）均为经验参数，未经过回测交叉验证最优值
- 「过渡阶段」作为兜底分类，可能覆盖过多异质场景（从趋势转弱到区间突破前夕都在此列）——是否需要进一步细分？
- 效率指标使用 `stageLookback=30` 周期计算，可能在快速切换市场中滞后
- 与 FSM 体系相比，缺少「新突破」这一关键状态——V6 将突破直接归入趋势（如果效率够高）或过渡（如果不够），可能模糊掉突破这一独立阶段
