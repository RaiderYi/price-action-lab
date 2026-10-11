---
title: "MC10+2 信号棒评分速记"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry, swing]
tags: [leg, control, doji, 质量, 完成度]
difficulty: intermediate
related: [signal-scoring-synthesis, brooks-signal-catalog, atr-scaling, setup-anatomy, review-mes-huangzongprice-collection]
char_count: 1754
---
# MC10+2 信号棒评分速记

## 一句话定义
huangzongprice 在每日 MES 复盘中使用的 12 因子信号棒质量评估速记系统（10 个核心因子 + 2 个附加因子）。

## 核心要点

### 评分格式
```
B1-B10 MC10+2 -5%K, -5% Cprior H, -5% -5%, -5% doji, -10% BOmrk regime, 
-10% late leg, +5% price control swing point 1ABR, +5% time control leg2 65%
```

### 12 因子清单

| # | 因子 | 典型权重 | 含义 |
|---|------|---------|------|
| 1 | K 质量 | ±5% | 信号棒 K 线本身的质量（实体/影线比例） |
| 2 | C prior H | ±5% | 收盘价相对前高的位置 |
| 3 | C prior L | ±5% | 收盘价相对前低的位置 |
| 4 | (第四项) | ±5% | 通常为与前 N 根 K 线的关系 |
| 5 | doji | ±5~20% | 十字星/犹豫不决的扣分 |
| 6 | BO mark regime | ±10~20% | 突破标记/市场状态（趋势/TR/climax/wedge） |
| 7 | late leg | ±5~10% | 是否为腿的末期——越晚越危险 |
| 8 | price control | ±5% | 多头/空头对价格的控制程度（swing point） |
| 9 | swing point 1ABR | ±5% | 摆动点与 1 倍 ATR 的关系 |
| 10 | time control | ±5% | 多头/空头的时间控制（leg 完成度 %） |

| 附加 | 因子 | 说明 |
|------|------|------|
| +1 | complex leg 2 | 复杂腿 2 —— 是否为二次复杂回调 |
| +2 | leg2 完成度 | 腿 2 是否已完成（如 "leg2 65%" = 腿2 完成 65%） |

### 评分机制
- 每个因子得分为 -20% 到 +5%（负分 = 扣分/不利，正分 = 加分/有利）
- doji 和 BO mark regime 权重最重（±10~20%），决定了棒线的背景合法性
- K 线质量、C prior H/L 权重较轻（±5%），是微调项
- 总体思路：**扣分为主、加分为辅**——默认不信任信号，需要证据说服

## 与相关概念的关系

- [[signal-scoring-synthesis]]：MC10+2 是人工肉眼评分版本，lFin/sFin 是 Pine Script 自动评分。人工版多了 "time control" 和 "leg2 完成度" 两个时间维度
- [[brooks-signal-catalog]]：MC10+2 评分的对象是 Brooks 16 种信号类型中的具体信号棒
- [[atr-scaling]]：MC10+2 中的 "1ABR" 使用了 ATR 标尺
- [[setup-anatomy]]：MC10+2 本质上是对 "架构 = 信号棒 + 背景" 的量化拆解

## 实战应用
在每日复盘中，对每一段行情的信号棒区域进行 12 因子评分，评分结果为负（如 "-20%"）则放弃该信号，为正（如 "+15%"）则考虑入场。doji 和 late leg 是最常见的否决理由。

## 来源支撑
- [[review-mes-huangzongprice-collection]]

## 矛盾与待验证
- MC10+2 的确切 12 个因子名称和权重边界尚未从代码或文档中正式确认——上述清单是从 145+ 份复盘的速记字符串中反推的
- "K 质量" 的具体定义（实体/影线比例阈值？ATR 倍数？）未在复盘文本中明确
- 与 [[signal-scoring-synthesis]] 的 lFin/sFin 五因子公式的精确对应关系待验证
