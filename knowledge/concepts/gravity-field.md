---
title: "引力场"
phase: [range]
signal_types: [wedge, pullback-entry, swing]
tags: [gscore, 权重, atr, 高斯衰减, ctxscore]
difficulty: intermediate
related: [signal-scoring-synthesis, atr-scaling, fsm-market-cycle, support-resistance, article-20260520-wedge-gravity-brooks-context-v3, article-wg-v15-analysis, article-20260519-wedge-gravity-v41-flowchart, article-huangzongprice-wedge-gravity-v5-cycle-structure, article-wedge-gravity-v14-source]
char_count: 1439
---
# 引力场

## 一句话定义
对 EMA20、Pivot 高低点、波段 50% 回调、三日开盘区间重心等关键位，用高斯型权重累加为 `gScore`，量化当前价格是否处于"值得交易的位置"。

## 核心要点
- **引力源**：
  - EMA20（权重×3）
  - ph0/pl0（权重×5）——最近分型高低点，引力最强
  - ph1/pl1（权重×3）——次近分型
  - `fib50`（权重×4）——波段 50% 回调位
  - 三日开盘区间重心（权重×4）——仅当 `gap3H-gap3L > 0.5×ATR14` 时追加
- **权重函数**：高斯衰减 `w × exp(-0.5 × (dist/ATR14)^2)`，距离用 ATR14 归一化，超过 2×ATR 贡献为 0
- **门槛**：`gravOK = gScore > i_gThr`（默认 5.0）
- **环境分**：`ctxScore = min(gScore / (2*i_gThr), 1)` → 进入 `lFin`/`sFin` 的环境权重部分（`i_ctxW`）

## 与相关概念的关系
- [[signal-scoring-synthesis]]：引力场提供 `ctxScore`，是最终分数中的"环境"分量
- [[atr-scaling]]：引力场的距离归一化完全依赖 ATR 标尺
- [[fsm-market-cycle]]：引力场计算在 FSM 状态判定之后执行，FSM 决定可否入场，引力场决定值不值得
- [[support-resistance|Support/Resistance]]：引力场本质上是对多个支撑/阻力位的数值化建模

## 实战应用
价格落在多个引力源重叠区域时，`gScore` 高 → `ctxScore` 高 → 最终信号分 `lFin`/`sFin` 更高。远离所有引力源时，即使结构形态好，分数也会被压低。

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：高斯衰减公式 + 6 个引力源精确权重 + gScore > 5.0 阈值触发）
- [[article-wg-v15-analysis]]
- [[article-20260519-wedge-gravity-v41-flowchart]]（引力场在 Location 层贡献 +0.12 分；环境分 ctxScore = min(gScore/(2×i_gThr),1) 进入信号合成）
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]（V5.0 明确六类引力源权重 + 三日开盘区间重心追加条件；gScore 通过 invisible plot 6 输出给指标 B）
- [[article-wedge-gravity-v14-source]]（V1.4 源码第362-387行——高斯衰减 `f_gauss()` 函数 + 6个关键位权重 + `gravOK` 阈值判定）

## 矛盾与待验证
- 高斯衰减的 2×ATR 截断半径是经验参数，不同品种/周期可能需要调整。
- 与纯 Brooks 手工分析中"价格是否在支撑/阻力附近"的判断相比，引力场的数值化方法是否系统性地更优，尚无对比数据。
