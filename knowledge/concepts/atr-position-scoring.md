---
title: "ATR 位置评分系统"
phase: [trend, range, breakout, transition]
signal_types: []
tags: [atr, locl, locs, 阻力, ema]
difficulty: intermediate
related: [context-engine-v2, support-resistance, atr-scaling, ctx-scoring, brooks-four-step-context, article-huangzongprice-context-engine-v2]
char_count: 3580
---
# ATR 位置评分系统

## 一句话定义
v2 Context Engine 的第一层：将价格距离关键支撑/阻力的远近量化为 ATR 倍数，按预设加分/扣分公式计算多头/空头位置评分。

## 核心要点
- **距离计算**：`distToLevel / ATR14`，低于 `syminfo.mintick` 时用 mintick 兜底防止除零
- **基准分**：多头、空头均从 0.10 起步
- **所有加分/扣分规则以 `+=`/`-=` 硬编码**，最终 `f_clamp01` 限制在 0~1 区间
- 关键价位来源：分型极点 (ph0/pl0)、Donchian 20 (donchH/donchL)、EMA20、Fib50
- 与 V1.5 ctx1_score 本质不同：V1.5 是定性描述（「接近 → 加分」），v2 是精确量化（「≤0.60ATR → +0.30」）

## 位置判定矩阵

### 支撑/阻力距离判定
| 条件 | 参数 | 含义 |
|------|------|------|
| 距离 ≤ `i_srNearAtr` (默认 0.60 ATR) | 强支撑/阻力 | 价格紧贴关键位 |
| 距离 ≤ `i_srSoftAtr` (默认 1.20 ATR) | 弱支撑/阻力 | 价格在关键位附近 |
| 区间中点：`abs(close-donchMid) ≤ donchSpan × 0.20` | 区间中部 | 距离两侧都 > 1.0 ATR |
| 距离 ≤ `i_fibNearAtr` (默认 0.80 ATR) | 近 Fib50 | 公允价值区域 |
| 目标距离 ≤ `i_targetNearAtr` (默认 0.80 ATR) | 目标接近 | 多头目标/空头目标在射程内 |

### 追价判定
| 条件 | 含义 |
|------|------|
| `close > donchHPrev + 0.60×ATR14` 且距支撑 > 1.20 ATR 且距阻力 < 1.20 ATR | 多头追价（lateBreakoutLong） |
| `close < donchLPrev − 0.60×ATR14` 且距阻力 > 1.20 ATR 且距支撑 < 1.20 ATR | 空头追价（lateBreakoutShort） |

## 完整评分公式

### 多头位置分 (locScoreL)
```
locL = 0.10                                           // 基础分
locL += atBullSupport      ? +0.30 : 0.0             // 在强支撑
locL += nearBullSupport    ? +0.18 : 0.0             // 在弱支撑
locL += nearFib50          ? +0.08 : 0.0             // 近 Fib50
locL += close ≤ EMA20+0.3×ATR ? +0.05 : 0.0         // 在 EMA20 下方
locL -= midRangeLocation   ? −0.28 : 0.0             // 区间中部
locL -= lateBreakoutLong   ? −0.20 : 0.0             // 追价
locL -= atBearResistance   ? −0.28 : 0.0             // 在对方强阻力
locL -= nearBearResistance ? −0.14 : 0.0             // 在对方弱阻力
locL -= bullTargetNearby   ? −0.16 : 0.0             // 多头目标接近
locScoreL = clamp01(locL)
```

### 空头位置分 (locScoreS)
```
locS = 0.10                                           // 基础分
locS += atBearResistance   ? +0.30 : 0.0             // 在强阻力
locS += nearBearResistance ? +0.18 : 0.0             // 在弱阻力
locS += nearFib50          ? +0.08 : 0.0             // 近 Fib50
locS += close ≥ EMA20−0.3×ATR ? +0.05 : 0.0         // 在 EMA20 上方
locS -= midRangeLocation   ? −0.28 : 0.0             // 区间中部
locS -= lateBreakoutShort  ? −0.20 : 0.0             // 追价
locS -= atBullSupport      ? −0.28 : 0.0             // 在对方强支撑
locS -= nearBullSupport    ? −0.14 : 0.0             // 在对方弱支撑
locS -= bearTargetNearby   ? −0.16 : 0.0             // 空头目标接近
locScoreS = clamp01(locS)
```

## 关键参数配置

| 参数 | 默认值 | 含义 |
|------|--------|------|
| `i_srNearAtr` | 0.60 | 距关键 SR ≤ 此倍 ATR → 强支撑/阻力 |
| `i_srSoftAtr` | 1.20 | 距关键 SR ≤ 此倍 ATR → 弱支撑/阻力 |
| `i_midRangePct` | 0.20 | 区间中点带宽百分比 |
| `i_fibNearAtr` | 0.80 | 距 Fib50 ≤ 此倍 ATR → 标记 |
| `i_targetNearAtr` | 0.80 | 距目标位 ≤ 此倍 ATR → 标记 |
| `i_lateBreakAtr` | 0.60 | 追价判定 ATR 倍数 |
| `i_swN` | 5 | N-Bar 分型左右距 |
| `i_donchN` | 20 | Donchian 周期 |

## 与相关概念的关系
- [[context-engine-v2]]：Layer 1，权重 0.40，是整个四层架构的第一层
- [[support-resistance|Support/Resistance]]：位置评分的 S/R 理论来源——16+ 种 S/R 类型，v2 选取了其中 4 类（分型极点/Donchian/EMA/斐波那契）
- [[atr-scaling]]：ATR 归一化的方法论基础——距离除 ATR 使不同品种/周期的评分可比
- [[ctx-scoring]]：V1.5 的 ctx1_score 的前身，v2 将评分公式从「定性描述」升级为「显式量化」
- [[brooks-four-step-context]]：V1.5 四步法的 Step1（「市场在什么价位？」）的工程化落地

## 实战应用
- **locScoreL ≥ 0.70**：价格处于理想多头位置（在强支撑 + 远离阻力 + 非中部）
- **locScoreL < 0.30**：价格处于糟糕多头位置（在阻力/中部/追价）
- 位置分高但不等于背景支持——如果阶段层和动能层都差（对方趋势健康 + 衰竭风险高），最终 bgScore 仍可能很低

## 来源支撑
- [[article-huangzongprice-context-engine-v2]]

## 矛盾与待验证
- 扣分项中，对方弱阻力 −0.14 而对方强阻力 −0.28，是 2:1 的比例关系——是否应该梯度更细（比如 0.28/0.21/0.14）？
- ATR 周期使用 ATR14（短）用于距离判定，ATR20（长）用于波动率基线——两套 ATR 的互动关系未经回测验证
- 仅选取 4 类 S/R（分型/Donchian/EMA/Fib50）而忽略了整数关口/测量移动/前期密集区等——是精简取舍还是覆盖不足？
