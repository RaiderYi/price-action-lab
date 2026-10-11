---
title: "复权"
phase: [trend, range, breakout]
signal_types: [h2-entry, wedge, pullback-entry, flag]
tags: [adjustflag, 后复权, 本为基准, 历史价格, 前复权]
difficulty: intermediate
related: [multi-market-architecture, support-resistance, atr-scaling, article-ashare-guide, integration-summary-20260306]
char_count: 1125
---
# 复权

## 一句话定义
A 股因分红送股导致股价跳空，通过复权调整历史价格以保证 K 线数据连续性。

## 核心要点
- **后复权**（`adjustflag='3'`，默认推荐）：以当前股本为基准向前调整历史价格，保证价格序列的数学连续性，适合回测
- **前复权**（`adjustflag='2'`）：以历史股本为基准向后调整当前价格，适合查看历史买入成本
- **不复权**（`adjustflag='1'`）：原始价格，分红送股处会出现跳空缺口，破坏趋势线和支撑阻力位的连续性
- 复权不影响成交量，仅调整 OHLC 价格

## 复权模式对比

| 维度 | 后复权 | 前复权 | 不复权 |
|------|--------|--------|--------|
| 当前价格 | 真实市价 | 被下调 | 真实市价 |
| 历史价格 | 被上调 | 真实（但无参考意义） | 真实 |
| K 线连续性 | ✅ 连续 | ✅ 连续 | ❌ 有缺口 |
| 适用场景 | 回测、技术分析 | 查看历史成本 | 查看除权除息日 |

## 与相关概念的关系
- [[multi-market-architecture]]：加密货币不涉及复权，A 股必须处理复权——这是双市场架构中 A 股数据适配层的核心功能之一
- [[support-resistance|Support/Resistance]]：不复权会产生虚假的支撑阻力位（分红缺口被误识别为价格突破），后复权后 SR 位置才可靠
- [[atr-scaling]]：不复权数据中分红日的 ATR 会异常放大（因为包含跳空缺口），导致基于 ATR 的止损/止盈计算失真

## 实战应用
回测 A 股时必须使用后复权（`adjustflag='3'`），否则分红日会出现虚假的暴跌信号和错误的盈亏计算。查看单只股票的当前持仓成本时切换到前复权。

## 来源支撑
- [[article-ashare-guide]]（ASHARE_GUIDE.md — 复权选型说明及 baostock 参数）
- [[integration-summary-20260306]]（A 股数据适配层设计）
- [[multi-market-architecture]]（市场差异表中的复权行）

## 矛盾与待验证
- Brooks 原著针对美股期货（无复权概念），复权对 Brooks 信号（H1/H2 回调位、楔形第三推的精确位置）的具体影响尚未系统验证
- 后复权在多次分红后会显著抬高历史价格（例如茅台历史价可能数万元），是否影响图表形态的视觉识别→主观判断的一致性，待评估
