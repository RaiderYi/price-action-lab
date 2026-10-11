---
title: "供需区（Supply & Demand Zone）"
phase: [trend, range, breakout, transition]
signal_types: [wedge]
tags: [base, avgbody, brooks, zone, 供应区]
difficulty: intermediate
related: [support-resistance, buy-vacuum-sell-vacuum, fair-price-discovery, price-action, article-20240315-price-action-intro, order-block-recognition, v5-integrated-architecture, wedge-gravity-dual-core, brooks-signal-catalog, article-huangzongprice-wedge-gravity-v5, order-blocks, breakout-mechanics, article-wedge-gravity-B-signal-execute-v5]
char_count: 5671
---
# 供需区（Supply & Demand Zone）

## 一句话定义
价格快速离开的横盘区域，代表机构资金的集中介入（吸筹/派发）痕迹。

## 核心要点
- **需求区（Demand Zone）**：价格快速上涨前的小幅横盘区 → 机构在此吸筹建仓
- **供给区（Supply Zone）**：价格快速下跌前的小幅横盘区 → 机构在此派发减仓
- **与 S/R 的关键区别**：支撑阻力是价格多次测试的水平线，供需区是价格"快速离开"的区域（通常只被触及一次）——供需区关注的是机构的足迹，S/R 关注的是市场的记忆
- **Sam Seiden 流派**：将供需区理论系统化，认为机构订单流是价格运动的根本动力
- **入场逻辑**：价格回测需求区做多 / 价格回测供给区做空，止损设在区域外侧

## 与相关概念的关系
- [[support-resistance|Support/Resistance]]：互补关系——S/R 是"价格曾在这里反转"，供需区是"机构曾在这里行动"。供需区可以被视为一种特殊类型的 S/R，但识别逻辑不同
- [[buy-vacuum-sell-vacuum]]：真空效应与供需区的磁吸机制高度相关——一方缺席后价格被吸向供需区
- [[fair-price-discovery]]：供需区是公平价格发现过程中的关键节点——机构在此处发现了他们认为的不公平定价
- [[price-action]]：供需区是价格行为学中区别于传统 S/R 分析的一个独立维度

## 实战应用
在图表上寻找"价格快速离开前的小横盘"——横盘越小、离开越快、离开幅度越大，供需区越有效。价格首次回测该区域时是最佳入场时机。

## 来源支撑
- [[article-20240315-price-action-intro]]

## 矛盾与待验证
- Sam Seiden 的供需区理论在 Brooks 体系中并非核心——Brooks 更关注价格在 S/R 附近的棒线行为而非"区域"本身。两种视角的优劣和适用场景需要更多对比资料。
- A 股市场有涨跌停限制，可能导致供需区形态失真（快速离开 = 封板），需要验证供需区理论在 A 股的适应性。


---

## Merged Content (from supply-demand-zone-recognition)

# 供需区识别（Supply/Demand Zone Recognition）

## 一句话定义
基于 SMC（Smart Money Concepts）理论的供需区自动识别——通过强趋势后的 Base 区域（小实体整理）定位机构订单聚集区，与 Brooks 经典支撑/阻力属于互补但独立的体系。

## 核心要点
- **起源**：V5.0 新增的 G6 参数组模块，是 huangzongprice 系统中首次引入 SMC 风格的供需区检测
- **核心思想**：强趋势后的短暂整理（Base/Congestion）是机构订单执行区——供应区=卖单聚集，需求区=买单聚集
- **与 Brooks S/R 的区别**：Brooks S/R 基于市场结构（前高/前低/均线/整数位），供需区基于**价格行为模式**（强K线+Base区）
- **识别规则**：需求区信号+D→Base+U 组合；供应区 D→Base+D 组合；Pine Script 中统一使用 3 根 K 线窗口

## 识别规则详解

### 供应区（Supply Zone）— 上方卖压区
```
条件链：强下跌K线 + 前一根是Base区 + 价格结构确认
```

伪代码：
```
strongDown = 实体 > avgBody5 × 1.2 + 收盘 < 开盘 + 收盘 < 前低
baseRBR    = strongDown + 前根实体 < avgBody5 × 0.3 + 前根阳线  // Rally-Base-Rally
baseRBD    = strongDown + 前根实体 < avgBody5 × 0.3 + 前根阴线  // Rally-Base-Drop
→ 满足 strongDown + (baseRBR or baseRBD) → 标记供应区
→ 区域范围 = max(high, high[1], high[2]) ~ min(low, low[1], low[2])
```

### 需求区（Demand Zone）— 下方支撑区
```
条件链：强上涨K线 + 前一根是Base区 + 价格结构确认
```

伪代码：
```
strongUp = 实体 > avgBody5 × 1.2 + 收盘 > 开盘 + 收盘 > 前高
demandBaseRBD = strongUp + 前根实体 < avgBody5 × 0.3 + 前根阴线  // Drop-Base-Drop
demandBaseRBR = strongUp + 前根实体 < avgBody5 × 0.3 + 前根阳线  // Drop-Base-Rally
→ 满足 strongUp + (demandBaseRBD or demandBaseRBR) → 标记需求区
```

## 区域管理机制

### 强度评分
`zone.strength = barBody / avgBody5`（强K线实体相对平均实体的倍数）

### 生命周期
- 最大寿命：`i_zoneMaxBars`（默认 100 bar），超时自动移除
- 每根 K 线末尾倒序遍历 Array，删除过期区域

### 重叠检测
新区域创建时，遍历已有同类型区域数组——如果新区域的价格范围与任一已有区域重叠，跳过创建（避免同区域重复标记）

### 测试检测（未在 V5 完整实现）
设定了 `isTested` 和 `testCount` 字段，但 V5 仅初始化未动态更新——可能是 V5.1 的预留功能

## V5 可视化
- 供应区：红色半透明框（`color.new(color.red, 90)`，边框 `color.new(color.red, 60)`）
- 需求区：绿色半透明框（`color.new(color.lime, 90)`，边框 `color.new(color.lime, 60)`）
- 从 zone.barStart 延伸到当前 bar_index
- 最多显示最近 3 个区域

## 与相关概念的关系
- [[support-resistance|Support/Resistance]]：Brooks 经典 S/R——前高/前低/均线/整数位，与供需区是互补体系
- [[order-block-recognition]]：V5 同期新增，OB 是单一 K 线的"微缩版供需区"
- [[v5-integrated-architecture]]：供需区是 V5 单体架构的 G6 模块
- [[wedge-gravity-dual-core]]：V1.5/V4.1 无此模块，是 V5 的全新功能
- [[brooks-signal-catalog]]：Brooks 体系不包含 SMC 供需区概念

## 实战应用
在信息面板第 29 行显示「供需区/OB数量」。图表上有红/绿色半透明区域时：
- 价格接近需求区（绿色）→ 潜在做多机会 + 止损位参考
- 价格接近供应区（红色）→ 潜在做空机会 + 目标位参考
- 供需区与 Brooks S/R 共振时信号最强

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v5]]（G6 参数组，行 532-619）

## 矛盾与待验证
- SMC 供需区理论与 Brooks 价格行为学属于不同流派——V5 是首次在同一指标中融合两者，两者对"S/R"的解读可能存在分歧
- 在低流动性市场（如小币种/个股）中 Base 区域识别准确度未验证
- `isTested`/`testCount` 字段已定义但未在 V5 中动态更新——未来版本可能添加"区域有效性"评估
- Base 区识别仅用前一根 K 线（body < avgBody5 × 0.3），SMC 原理论允许 1-5 根——3 根窗口可能更合理


---

## Merged Content (from supply-demand-zones)

# 供需区识别（Supply/Demand Zones）

## 一句话定义
基于 Brooks "供需失衡"理论，识别强突破K线前的 Base 蜡烛——供应区（强阴线前的横盘）和需求区（强阳线前的横盘），标定为未来价格回测时的潜在支撑/阻力区域。

## 核心要点

### ZoneData 类型
Pine Script v6 自定义类型，包含9个字段：
- `barStart/barEnd`：区域起止K线索引
- `highPrice/lowPrice`：区域高低价格边界（取3根范围）
- `originPrice`：Base 蜡烛收盘价
- `isSupply`：true=供应区（上方阻力），false=需求区（下方支撑）
- `strength`：突破实体 / avgBody5（强度倍数）
- `isValid/isTested/testCount`：有效性/是否被测试/测试次数

### 供应区检测条件
需同时满足两个条件：
1. **strongDown 突破**：barBody > avgBody5 × i_zoneStrength（默认1.2）AND close < open（阴线）AND close < low[1]（跌破前低）
2. **Base 确认**（二选一）：
   - **baseRBR**：前一根 barBody < avgBody5 × 0.3（小实体）AND close[1] > open[1]（阳线）
   - **baseRBD**：前一根 barBody < avgBody5 × 0.3（小实体）AND close[1] < open[1]（阴线）

取范围 = [bar_index-2, bar_index] 三根的高低极值。去重：与已有供应区不重叠（zoneLow > existing.highPrice or zoneHigh < existing.lowPrice）才加入。

### 需求区检测条件
与供应区对偶：
1. **strongUp 突破**：barBody > avgBody5 × i_zoneStrength AND close > open（阳线）AND close > high[1]（突破前高）
2. **Base 确认**（二选一）：
   - **demandBaseRBD**：前一根 barBody < avgBody5 × 0.3 AND close[1] < open[1]（阴线）
   - **demandBaseRBR**：前一根 barBody < avgBody5 × 0.3 AND close[1] > open[1]（阳线）

### 生命周期
- **最大寿命**：`i_zoneMaxBars`（默认100根，可调20-300）
- 每根确认K线后遍历清理过期区域
- 显示时仅渲染最近3个（减少视觉噪音）

### 参数体系
| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| i_zoneEnable | true | — | 启用供需区识别 |
| i_zoneStrength | 1.2 | 0.5-3.0 | Base强度倍数（实体≥5均×此值） |
| i_zoneMaxBars | 100 | 20-300 | 供需区最大寿命（根） |
| i_shZones | true | — | 显示供需区 |

## 与相关概念的关系
- [[order-blocks]]：供需区与订单块是两种不同的支撑/阻力识别方法——供需区检测 Base + 突破，订单块检测突破 + 反向确认
- [[support-resistance|Support/Resistance]]：Brooks 理论中的支撑阻力概念，供需区是其量化实现之一
- [[wedge-gravity-dual-core]]：供需区是 V5 执行引擎新增的独立模块，不参与背景评分但为交易者提供视觉参考
- [[breakout-mechanics]]：供需区检测的核心逻辑——强突破前的小实体 Base 蜡烛

## 实战应用
图表上供需区以半透明 box 显示：红色=供应区（上方阻力），绿色=需求区（下方支撑）。价格回测到需求区时可能形成做多入场，回测到供应区时可能形成做空入场。但供需区不参与自动信号生成——需要人工判断价格到达供需区后的反应。

## 来源支撑
- [[article-wedge-gravity-B-signal-execute-v5]]（V5.0 信号执行引擎——供需区识别首次作为独立模块引入）

## 矛盾与待验证
- 供需区仅用于视觉参考，未纳入评分体系——与 Brooks 原著将供需失衡作为核心分析维度存在落差
- Base 确认仅看前一根K线（barBody[1] < avgBody5 × 0.3），Brooks 原著中 Base 可能持续多根小K线
- 强度倍数 1.2 为经验值，不同品种/周期最优值需回测确定
- 仅保留最近3个供需区显示，可能遗漏更早期的关键区域
