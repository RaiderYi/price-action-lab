---
title: "追价突破（Late Breakout）"
phase: [trend, range, breakout]
signal_types: [pullback-entry]
tags: [atr, donchian, latebreakatr, 支撑, close]
difficulty: intermediate
related: [trend-maturity, position-layer-scoring, breakout-mechanics, protective-stops, article-huangzongprice-context-engine-v2, article-huangzongprice-context-engine-v1]
char_count: 1825
---
# 追价突破（Late Breakout）

## 一句话定义
价格已大幅突破近期边界（旧 Donchian 高/低），同时远离同向支撑/阻力且已贴近对向阻力/支撑——此时顺势入场属于「追在末端」，面临高概率回调风险。

## 核心要点
- **判定条件（多方）**：`close > donchHPrev + i_lateBreakAtr × ATR14` 且 远离多方支撑（> 1.20 ATR）且 已贴近空方阻力（< 1.20 ATR）
- **判定条件（空方）**：`close < donchLPrev - i_lateBreakAtr × ATR14` 且 远离空方阻力（> 1.20 ATR）且 已贴近多方支撑（< 1.20 ATR）
- **三层影响**：
  1. 位置层：扣分 -0.20（直接压低 `locScore`）
  2. 动能层：通过趋势成熟度间接扣分（占成熟度权重 0.25）
  3. 否决层：在阻力位追价做多 / 在支撑位追价做空 → 触发背景否决
- **与顺向突破的区别**：顺向突破是「突破旧边界+仍在支撑/阻力附近」→ 健康突破；追价突破是「突破旧边界+已远离进场区+已靠近出场区」→ 迟到入场

## 判定逻辑详解

### 多方追价（`lateBreakoutLong`）
```
close > donchHPrev + 0.60 × ATR14    ← 已突破旧 Donchian 上沿超过 0.6 ATR
AND bullSupportDist > 1.20 ATR       ← 已远离所有多方支撑(pl0/DonchianL/EMA/Fib50)
AND bearResistDist < 1.20 ATR        ← 已贴近空方阻力(ph0/DonchianH/EMA/Fib50)
```

### 空方追价（`lateBreakoutShort`）
```
close < donchLPrev - 0.60 × ATR14    ← 已突破旧 Donchian 下沿超过 0.6 ATR
AND bearResistDist > 1.20 ATR        ← 已远离空方阻力
AND bullSupportDist < 1.20 ATR       ← 已贴近多方支撑
```

**关键细节**：使用 `donchHPrev`/`donchLPrev`（前一Bar的 Donchian 值）而非当前值——防止当前 Bar 自身扩展 Donchian 边界造成误判。

## 与相关概念的关系
- [[trend-maturity]]：追价是趋势成熟度的第二权重因子（0.25），追价出现 = 趋势已运行到中后段
- [[position-layer-scoring]]：追价在位置层扣分，使 `locScore` 下降
- [[breakout-mechanics]]：追价是突破机制的负面版本——突破发生但已错过最佳入场时机
- [[protective-stops]]：追价入场导致止损空间异常大（止损需放在支撑/阻力后方，距离远超正常范围）

## 实战应用
当 Context Engine 面板的「位置特征」行显示追价标记（出现在否决文案中）、且「成熟度 L/S」行偏高时——不追。等回调到支撑/阻力附近再考虑入场。如果追价触发了背景否决（bgVeto），则无论信号多强都不入场。

## 来源支撑
- [[article-huangzongprice-context-engine-v2]]（v2 实现 lateBreakout 判定三条件完整源码 + i_lateBreakAtr 可配置化）
- [[article-huangzongprice-context-engine-v1]]（v1 首次引入追价判定，但 lateBreakAtr 为内联常量）

## 矛盾与待验证
- `i_lateBreakAtr` 默认值 0.60——即突破旧边界 0.6 个 ATR 就算追价。对于高波动品种（如 BTC），0.6 ATR 可能仍属正常波动；对于低波动品种（如某些 A 股），0.6 ATR 已是大幅运动
- 判定中同时要求「远离同向支撑」和「贴近对向阻力」——这意味着追价判定需要一个「已到达对向区域」的确认，而非仅看突破幅度。这是一个保守设计
