---
title: "确认K线（Confirmation Bar）"
phase: [trend, range, breakout, transition]
signal_types: [failed-breakout]
tags: [atr, 确认, 信号候选, confatrmul, 确认条件]
difficulty: intermediate
related: [execution-scoring, execution-engine-architecture, signal-bars, protective-stops, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]
char_count: 1163
---
# 确认K线（Confirmation Bar）

## 一句话定义
v3 执行引擎的可选二层过滤机制——信号候选在下一根 K 线突破前一根极值且幅度超过 ATR 倍数阈值时才确认入场。

## 核心要点
- **开关**：用户可配 `i_useConfirm`（默认关闭）
- **确认条件（做多）**：信号候选产生后，下一根 K 线的收盘价 > 前一根 K 线最高价 + `ATR14 × i_confAtrMul`
- **确认条件（做空）**：信号候选产生后，下一根 K 线的收盘价 < 前一根 K 线最低价 - `ATR14 × i_confAtrMul`
- **ATR 倍数**：`i_confAtrMul` 默认 0.60（即突破幅度需 ≥ ATR14 的 60%）
- **延迟确认**：信号候选在当前 K 线产生，但确认检查在下一根 K 线——因此启用确认后，入场时机推迟一根 K 线
- **与等级过滤的先后关系**：信号候选先经过等级过滤，再经过确认K线——两者可叠加使用

## 与相关概念的关系
- [[execution-scoring]]：确认K线是评分完成后的最终关卡
- [[execution-engine-architecture]]：确认K线是执行引擎的可选组件
- [[signal-bars]]：Brooks 原版中信号棒与入场棒是两个概念——确认K线将入场棒形式化为可量化的 ATR 阈值规则
- [[protective-stops]]：确认K线推迟入场=错过部分行情，但也避免假突破被套——是盈亏比和胜率之间的权衡

## 实战应用
趋势中建议关闭确认K线（趋势中突破跟进性强，等确认会错过）；区间和反转场景中建议开启（假突破多，确认K线能过滤掉约 30-40% 的失败信号）。ATR 倍数 0.60 是较宽松的设置——如果频繁被假突破止损，可提高到 0.80-1.00。

## 来源支撑
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]

## 矛盾与待验证
- 确认K线本质上是一种"迟滞"过滤——在强趋势中，等确认K线可能意味着入场价格恶化 0.5-1.0 ATR。需要测算是"迟滞成本"更大还是"假突破损失"更大。
- V1.5 的信号确认是收盘位置检查（`close > midPt`）——即时确认但条件松。v3 的确认K线更严格但延迟一根 K 线。两种确认哲学（即时松 vs 延迟严）各有适用场景，尚无统一结论。
- 确认幅度使用 ATR14（短周期）而非 ATR20（长周期），对日内波动更敏感——对于波动率突变的市场（如开盘/数据发布），可能产生过多或过少确认。
