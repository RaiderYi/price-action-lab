---
title: 尾盘模式 (End-of-Day Patterns)
created: 2026-05-19
updated: 2026-05-19
type: concept
tags: [timing, btc, trading-management, intraday]
sources: [sources/encyclopedia-brooks-chart-patterns.md]
confidence: medium
---

# 尾盘模式 (End-of-Day Patterns)

## 一句话定义
Brooks 的尾盘交易时间规则：BTC（Buy The Close）行情如果在 12:30 PM PT 之前启动 → 通常无法持续到收盘 → 会在最后半小时内获利了结。

## 核心要点

### 尾盘 BTC 的时间分界线

Brooks 对 End of Day BTC 给出了精确的时间规则：

| 行情启动时间 | 可靠性 | 说明 |
|-------------|--------|------|
| **12:05 PM PT** | 低 | "通常太早"——启动过早的 BTC 行情在收盘前已经耗尽 |
| **12:15 PM PT** | 低 | 仍然太早——能量无法持续 45-60 分钟到收盘 |
| **12:30 PM PT 之后** | 高 | 能量足以持续到收盘——真正的 EOD BTC |
| **TR 日中的 BTC** | 中 | 如果 BTC 启动前是 TR 日（非趋势日），即使是晚启动也可能不持久 |

### 尾盘 BTC 的逻辑

1. **BTC 行情本质**：趋势/TR 交易日中，最后 30-45 分钟的定向运动
2. **启动过早的问题**：
   - 12:05 启动 → 需要维持 55 分钟到达收盘（13:00 PM PT = 美股收盘）
   - 但多空能量在 30 分钟内会自然衰减
   - 早期 BTC 交易者会在 12:35-12:45 开始获利了结 → BTC 行情被扼杀
3. **启动在最佳时间窗口（12:30+）**：
   - 仅需维持 30 分钟 → 能量充足
   - 多数参与者在此时间才确信方向 → 形成自我实现的预言

### Brooks 的另一个关键规则

> "In TR day, if B The Close rally starts before 12:30 pm PT, it usually fails to last to the close."

这即是说：**在 TR 日，即使 BTC 启动在 12:30 之前，也会失败**——因为 TR 日的定向能量本来就弱，叠加过早启动的能量衰减更快。

### 百科全书中的实例

百科全书收录了 4 个 End of Day BTC 的完整图表实例：

1. **趋势日 BTC（成功）**：Bull Trend Day + BTC 启动在 12:30 后 → 持续到收盘
2. **过早启动 BTC（失败）**：BTC 在 12:05 启动 → 12:40 即反转回吐
3. **TR 日 BTC（失败）**：TR 日 + BTC 在 12:15 启动 → 未能突破开盘区间
4. **混合日 BTC**：有趋势但不够强 + BTC 启动晚 → 部分成功

## 与相关概念的关系

- [[btc-stc]]：BTC/STC 概念定义了"什么是尾盘行情"，而 End-of-Day Patterns 定义了"何时发生的尾盘行情才有效"
- [[trend-from-the-open]]：开盘趋势日 → 如果是全天趋势，尾盘通常有延续行情——不需要等待 BTC 启动
- [[trader-equation]]：过早参与的 BTC 会恶化交易者方程式——方向可能对但时间不对 → 亏钱
- [[swing-vs-scalp]]：尾盘 BTC 本质上是一种刮头皮 + 波段混合策略——持有时间 30-60 分钟

## 实战应用

1. **12:00 PM PT = 警惕时间**：开始观察是否有 BTC 行情启动的迹象
2. **12:00-12:25**：如果 BTC 行情启动 → 这可能不是真正的 EOD BTC → 要么等待，要么以刮头皮方式参与
3. **12:30 PM PT 之后**：如果此时出现强定向棒 + 连续跟进 → 可以信任这是一次 EOD BTC → 持有到收盘前 2-3 分钟
4. **TR 日不参与 BTC**：如果在 TR 日中，即使 BTC 在 12:30 后启动，也不应过度信任

## 来源支撑
- [[brooks-signal-catalog]] — End of Day BTC 系列的 4 个幻灯片实例
- [[course-notes-PA-study]] — BTC/STC 概念基础

## 矛盾与待验证
- 这些规则的**时间基准是美国东部时间**（美股收盘 16:00 ET = 13:00 PT）——应用到 A 股（收盘 15:00 CST）时，12:30 规则需要重新校准
- A 股的尾盘交易时段（14:30-15:00）与美股的 12:30-13:00 PT 对应——但 A 股无盘前盘后交易，动力结构不同
- 12:30 这个精确数字可能来自 Brooks 的经验观察，但未提供回测支撑——置信度标记为 medium
