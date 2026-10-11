---
title: "楔形质量三子评分"
phase: [trend, range, breakout]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry]
tags: [三子评分, 上轨斜率, ratioscore, 空间对称, 收口收敛]
difficulty: intermediate
related: [three-push-wedge, signal-scoring-synthesis, wedge-gravity-dual-core, article-wg-v2-master]
char_count: 1060
---
# 楔形质量三子评分

## 一句话定义
三推楔形的质量评分从 V1.5 的简单对称比升级为三个子维度：空间对称40% + 收口收敛35% + 跨度25%，每个子维度归一化到 0-1。

## 核心要点
- **空间对称（40%）**：前后两段价格波幅的比值是否接近1.0
  - `symScore = (ratioScore(价格比) + ratioScore(时间比)) × 0.5`
  - `ratioScore(r, lo, hi) = 1.0 - |r-1.0| / max(1.0-lo, hi-1.0)` — 偏离1.0越远分越低
- **收口收敛（35%）**：上下边界斜率是否收敛（上升楔形收口=下轨斜率≥上轨×0.8；下降楔形收口=上轨斜率≤下轨×0.8）
  - `convScore = 1.0 - |下轨斜率-上轨斜率| / |上轨斜率|`
- **跨度（25%）**：楔形的时间跨度相对于最大允许跨度的位置
  - `spanScore = (实际跨度 - 10) / (i_wMax - 10)`，最小10根K线起算
- **三子评分仅用于上升/下降楔形各自的计算，不影响楔形识别本身**（识别仍用二元逻辑）

## 与相关概念的关系
- [[three-push-wedge|Three Push Wedge]]：三子评分是对三推楔形识别后的质量量化，不改变"是否识别为楔形"的判断
- [[signal-scoring-synthesis]]：`structScoreL/S` = 楔形时用三子评分加权，H2/L2时固定0.55
- [[wedge-gravity-dual-core]]：V2 的楔形模块比 V1.5 更精细，但比 V3 的三推回撤分析（findPullback+scorePullbacks）更简洁

## 实战应用
三子评分越高的楔形，突破后的方向越可靠。上升楔形（看跌信号）的三子评分可用于判断做空信心——symScore 接近1.0 且 convScore 接近1.0 = 教科书级楔形。面板中不直接显示三子评分，但可通过楔形形态标签间接感知。

## 来源支撑
- [[article-wg-v2-master]]

## 矛盾与待验证
- V3 的楔形质量评分公式不同（对称35%+收敛35%+动量30%），V2 的跨度维度在 V3 中缺失——哪个维度更有预测力？
- 三子评分是纯形态学评分，未纳入成交量/市场背景——是否应考虑加权 FSM 状态？
