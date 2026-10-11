---
title: 买入收盘/卖出收盘 (Buy The Close / Sell The Close)
created: 2026-05-19
updated: 2026-05-19
type: concept
tags: [trend, entry, price-action, al-brooks]
sources: [sources/course-19-29-sr-basic-patterns.md]
---

# 买入收盘/卖出收盘 (BTC / STC)

## 一句话定义
在强趋势中，交易者在趋势棒收盘时立即以市价入场，押注趋势继续。

## 核心要点

### BTC（Buy The Close）——强多头趋势
- 交易者在强势多头棒收盘时立即买入
- 押注收盘价是更高价格的信号，即使先出现回调
- 连续多条多头棒时，交易者在每条棒的收盘价都买入
- 他们还会在第一条空头棒收盘时买入（仍相信趋势）

### STC（Sell The Close）——强空头趋势
- 交易者在强势空头棒收盘时立即卖出
- 押注收盘价是更低价格的信号，即使先出现反弹

### 当回撤令人失望时
当回调太强（卖压/买压过大）：
- **BTC 多头转为 TR 思维**：认为多头趋势已结束，现在是 TR。在低位加仓，试图在第一次入场价盈亏平衡退出，在第二次入场获利
- **STC 空头转为 TR 思维**：认为空头趋势已结束，现在是 TR。在高位加仓，试图在第一次入场价盈亏平衡买回，在第二次入场获利

### BTC/STC 入场价成为 S/R 的机制
- **多头最高收盘价=阻力**：BTC 多头用限价单在最高收盘价卖出→形成阻力
- 多头在最初的入场棒收盘价下限价卖单→该价位产生阻力
- 只要多头卖出就产生阻力，空头也会在此做空
- **空头最低收盘价=支撑**：STC 空头用限价单在最低收盘价买入→形成支撑
- 空头在第一次卖出棒收盘价下限价买单→该价位产生支撑
- 只要空头买入就产生支撑，多头也会在此做多

### 失望交易者的行为
- 看到强回撤后，BTC 多头得出结论：多头趋势结束，现在是 TR
- 他们试图在第一次入场价退出整个头寸（盈亏平衡）
- 在第二次入场（低位加仓）获利
- TR 思维→低买高卖（BLSHS），刮头皮

## 与相关概念的关系
- [[scale-in-dynamics]]：BTC/STC 交易者在回撤时加仓→入场价成为 S/R
- [[support-resistance|Support/Resistance]]：BTC 最高收盘=阻力，STC 最低收盘=支撑
- [[breakout-test]]：共同的驱动力——被套者盈亏平衡退出

## 实战应用
在强趋势中，顺着趋势方向在趋势棒收盘时入场。一旦出现令人失望的回撤（卖压突然增大），立即从趋势思维切换到 TR 思维：不再追高/追低，而是低买高卖刮头皮。

## 来源支撑
- [[course-19-29-sr-basic-patterns]]（19D: Slides 66-85, 19E: Slides 86-104）

## 矛盾与待验证
- 无

### 书-码差异（来源：[[article-huangzongprice-pa-shape-audit]]）
**bear_stc（Sell The Close，major_diff，2 samples）**：
- 趋势前提：书本 `always_in_short`（AIS 状态）→ 代码 `AIS_like`（AIS 类似状态，非完全等价）
- 腿计数：书本 `spike_or_SPB` → 代码 `multi_strong_bear_bars`（多根连续强阴线）
- 信号棒：书本「强阴线收盘接近最低点」→ 代码额外要求「至少 3 根最近 K 为阴线」
- 额外过滤：`regime_penalty` 在 `climax_bear` 中大幅降分（书本仅建议"climax 附近避免 STC 追空"）

**bull_btc（Buy The Close，major_diff，6 samples）**：
- 趋势前提：书本 `always_in_long` → 代码 `AIL_like`
- 腿计数：书本 `spike_or_SPB` → 代码 `multi_strong_bull_bars`
- 信号棒：代码额外要求「至少 3 根最近 K 为阳线」+「Bar range 不超 2 ATR」

**关键问题**：书本的 Always In 是一个全市场状态判断（任何时刻都应有方向），代码的 `AIS_like`/`AIL_like` 仅看最近 N 根 K 线——两者的判断范围不同。另 bear_stc 仅 2 samples、bull_btc 仅 6 samples，样本量不足以验证差异的实际影响。
