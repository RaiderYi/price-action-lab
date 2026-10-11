---
title: "趋势/反转信号分离评分"
phase: [trend, range, breakout, transition]
signal_types: [reversal-entry]
tags: [反转信号, fsm, 信号, 阈值, 多头趋势]
difficulty: intermediate
related: [signal-scoring-synthesis, fsm-market-cycle, signal-grading-system, article-wg-v2-master]
char_count: 1016
---
# 趋势/反转信号分离评分

## 一句话定义
根据当前 FSM 方向将信号分为"顺势趋势信号"和"逆势反转信号"，两者采用不同的额外加成权重——趋势重动量（70%）、反转重位置（60%）。

## 核心要点
- **趋势信号**：当 `signalingDir == fsmDir`（如 FSM 多头趋势中的做多信号），动量权重高
- **反转信号**：当 `signalingDir ≠ fsmDir`（如 FSM 多头趋势中的做空信号），位置权重高
- **趋势加成公式**：`extraBonus = (momScore × 0.70 + posScore × 0.30) × 0.10`
  - momScore = 实体占比×0.6 + 破位幅度×0.4
- **反转加成公式**：`extraBonus = (posScore × 0.60 + momScore × 0.40) × 0.10`
  - posScore = nearT1?1.0:nearT2?0.6:0.0 + gravOK?0.25:0.0
- **反转信号可选更高阈值**：`i_useRevFilter=true` 时，反转信号的触发分阈值 +0.10

## 与相关概念的关系
- [[signal-scoring-synthesis]]：趋势/反转分离是 V2 对 lFin/sFin 公式的最大改造——从单一公式变为情境化评分
- [[fsm-market-cycle]]：FSM 的 fsmDir 是判断趋势/反转的唯一依据
- [[signal-grading-system]]：反转信号天然更难达到 A 级（因为 `extraBonus` 中位置权重高但位置条件苛刻 + 可选更高阈值）

## 实战应用
在 FSM 多头趋势中——做多=趋势信号（侧重判断动能是否延续），做空=反转信号（侧重判断是否在关键位置）。反转信号需额外谨慎：关键位是否正确（nearT1/T2）、引力场是否触发（gravOK）、收盘位置是否极端。

## 来源支撑
- [[article-wg-v2-master]]

## 矛盾与待验证
- V1.5 无此分离逻辑（所有信号同权重），V3 执行引擎也无此分离——需要判断哪种设计在实战中表现更好
- Brooks 原著强调"趋势中只顺势"，但 V2 的反转信号设计是否过于宽松（仅+0.10阈值）？
