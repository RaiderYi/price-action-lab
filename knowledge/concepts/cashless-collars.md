---
title: Cashless Collars（零成本领口策略）
created: 2026-05-20
updated: 2026-05-20
type: concept
tags: [options, hedging, reversal, trading-strategy, trade-management]
sources: [sources/book-brooks-reversals-cn.md]
confidence: medium
---

# Cashless Collars（零成本领口策略）

## 一句话定义
买入虚值 Put 保护下行风险 + 同时卖出虚值 Call 获取权利金抵消成本——Brooks 在反转篇（Ch 22-24）推荐的期权对冲策略，三部曲中独有。

## 核心要点
- **目的**：保护持仓免受大幅下跌，同时不产生净期权支出
- **"零成本"（cashless）**：卖出的 Call 权利金 ≈ 买入的 Put 权利金，净支出≈0
- **适用场景**：持有大额现货多头、不愿止损但需要下行保护时
- **代价**：卖出 Call 上限了上行收益——如果股价大涨超过 Call 行权价，收益被锁定
- **Brooks 的用法**：反转篇中作为**长期持仓保护**而非交易信号工具。当 MTR 反转信号出现但不确认时，用领口保护而非清仓

## 与相关概念的关系
- [[major-trend-reversal|Major Trend Reversal]]：MTR 信号出现但未确认 → 领口保护而非立即反转仓位
- [[protective-stops]]：领口本质上是"期权止损"——用时间换空间，避免被噪音触发
- [[trade-management-system]]：领口属于持仓管理环节，非入场决策
- [[trader-equation]]：领口改变了风险/回报方程——限制上行换取下行保护

## 实战应用
持有 A 股仓位、担心系统性回调但中长期看多时，用领口代替清仓：买入 5% OTM Put + 卖出 5% OTM Call，确保最大亏损可控（Put 行权价下方），同时允许 5% 上方收益（Call 行权价上方被限）。

## 来源支撑
- [[book-brooks-reversals-cn]]：Brooks 反转篇 Ch 22-24 期权策略章节。此为三部曲中唯一论述期权对冲的卷。

## 矛盾与待验证
- **A 股期权市场适用性**：国内个股期权覆盖有限（仅上证 50/沪深 300 ETF 期权较为活跃），大部分 A 股无法做领口。可考虑替代：股指期货对冲 + 分批止盈。
- **Brooks 原著的期权论述深度**：反转篇的期权章节是 Brooks 价格行为框架的附属内容，非核心。他本人多次强调\"只做价格行为交易\"即可。
