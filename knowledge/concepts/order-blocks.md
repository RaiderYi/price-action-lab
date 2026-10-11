---
title: "订单块识别（Order Blocks）"
phase: [range, breakout, transition]
signal_types: [wedge]
tags: [and, close, 强度倍数, 突破, avgbody]
difficulty: intermediate
related: [supply-demand-zone, support-resistance, wedge-gravity-dual-core, breakout-mechanics, article-wedge-gravity-B-signal-execute-v5]
char_count: 2234
---
# 订单块识别（Order Blocks）

## 一句话定义
基于 ICT/SMC 的订单块概念，识别多空双方"未成交的剩余订单"堆积区——强方向性K线被反向确认后，该K线范围成为未来价格回测时的潜在反转区。

## 核心要点

### OBData 类型
Pine Script v6 自定义类型，包含7个字段：
- `barIndex`：订单块K线索引
- `highPrice/lowPrice`：OB 的高低价格边界（即该根K线的 high/low）
- `isBullish`：true=多头OB（下方支撑），false=空头OB（上方阻力）
- `strength`：实体 / avgBody5（强度倍数）
- `isValid/isRetested`：有效性/是否被回测

### 多头订单块（Bullish OB）
需同时满足两个条件：
1. **bullishOB 突破**：barBody > avgBody5 × i_obStrength（默认1.5）AND close < open（当前是阴线）AND close < low[1]（跌穿前低）——这根是"被拒绝的方向性K线"
2. **confirmUp 确认**：前一根 barBody > avgBody5 × 0.8 AND close[1] > open[1]（强阳线）AND close[1] > high（前收 > 当前最高点）

逻辑：前一根强阳线突破了某个价位 → 当前根被拒绝（强阴线打回）→ 前一根阳线区域仍有未成交的多头订单 → 该区域成为支撑

### 空头订单块（Bearish OB）
与多头对偶：
1. **bearishOB 突破**：barBody > avgBody5 × i_obStrength AND close > open（当前是阳线）AND close > high[1]（突破前高）
2. **confirmDown 确认**：前一根 barBody > avgBody5 × 0.8 AND close[1] < open[1]（强阴线）AND close[1] < low（前收 < 当前最低点）

逻辑：前一根强阴线跌穿 → 当前根被拒绝（强阳线拉回）→ 前一根阴线区域仍有未成交的空头订单 → 该区域成为阻力

### OB vs 供需区 对比
| 维度 | 供需区 | 订单块 |
|------|--------|--------|
| 理论基础 | Brooks 供需失衡 | ICT/SMC 订单流 |
| 检测逻辑 | Base（小实体）+ 突破 | 突破 + 反向确认 |
| 时间顺序 | 先有 Base → 后有突破 | 先有突破 → 后有确认 |
| 强度倍数 | 1.2（较低，覆盖面广） | 1.5（更高，更精选） |
| 最大寿命 | 100 根 | 80 根（更短） |
| 确认要求 | 前一根小实体即可 | 前一根强实体 + 收盘超越 |

### 生命周期
- **最大寿命**：`i_obMaxBars`（默认80根，可调20-200）
- 每根确认K线后清理过期OB
- 显示时最多渲染3个

### 参数体系
| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| i_obEnable | true | — | 启用订单块识别 |
| i_obStrength | 1.5 | 0.5-3.0 | OB强度倍数（实体≥5均×此值） |
| i_obMaxBars | 80 | 20-200 | OB最大寿命（根） |
| i_shOBs | true | — | 显示订单块 |

## 与相关概念的关系
- [[supply-demand-zone]]：供需区与订单块是 V5 执行引擎中并行的两种 S/R 识别模块——前者基于 Brooks 理论，后者基于 ICT/SMC
- [[support-resistance|Support/Resistance]]：订单块是支撑阻力概念在订单流理论下的量化实现
- [[wedge-gravity-dual-core]]：订单块是 V5 引擎新增的独立模块，与供需区同为视觉参考层
- [[breakout-mechanics]]：订单块确认依赖"突破→反向拒绝"的力学模式

## 实战应用
图表上订单块以半透明 box 显示：绿色=多头OB（下方支撑），暗红=空头OB（上方阻力）。OB 强度倍数（1.5）高于供需区（1.2），OB 信号更精选但更少。价格回测多头OB时可能形成做多入场，回测空头OB时可能形成做空入场。但订单块同样不参与自动信号生成——仅为人工交易提供潜在反转区域的视觉标记。

## 来源支撑
- [[article-wedge-gravity-B-signal-execute-v5]]（V5.0 信号执行引擎——订单块识别作为独立模块首次引入）

## 矛盾与待验证
- OB 来自 ICT/SMC 体系，与 Brooks 价格行为学属于不同流派——混用可能造成分析框架不一致
- 确认要求的"前收超越当前极值"条件严格，可能遗漏多数潜在OB
- 仅保留最近3个OB显示，丢失历史关键区域
- 强度倍数 1.5、寿命 80 根均为经验值，未经过回测优化
