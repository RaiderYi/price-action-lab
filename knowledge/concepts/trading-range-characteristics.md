---
title: "交易区间特征"
phase: [trend, range, breakout, transition]
signal_types: [scalp]
tags: [doji, 交易区间, brooks, 特征, 双向交易]
difficulty: intermediate
related: [buy-vacuum-sell-vacuum, tight-trading-range, barbwire, breakout-mode, trading-range-quality, channel-to-trading-range, fsm-market-cycle, breakout-mechanics, book-brooks-trading-ranges]
char_count: 1548
---
# 交易区间特征

## 一句话定义
交易区间 = 任何存在双向交易的区域，其标志（Hallmark）是不确定感——突破方向不明，多头和空头都没有控制权。

## 核心要点

### Brooks 的广义定义
交易区间可以是：一根 DOJI 棒（一棒区间）、几根棒、整个屏幕、甚至几天的图表。关键是**双向交易**正在发生。

### 15+ 项可观测特征
1. **方向不确定性** — 突破方向不明
2. **低把握** — 几乎所有交易不超过 55% 确定
3. **双向信号并存** — 合法多头和空头入场设置同时出现
4. **多次转向** — 屏幕上多次方向变化
5. **水平分布** — 左右边棒线在屏幕垂直中间三分之一
6. **中段密集** — 大部分棒在屏幕中间，边界附近突然反转
7. **反复扫止损** — 强趋势棒突破边界后下一棒立即反向
8. **趋势棒孤立** — 极少连续 3-4 根同向趋势棒
9. **突出影线** — 棒线有明显上下影线
10. **高重叠度** — 很多棒与前一棒重叠 50% 以上
11. **多棒重叠** — 三根以上棒各自重叠 50% 以上
12. **多 DOJI** — 大小 DOJI 频繁出现
13. **均线平坦** — 移动平均线近乎水平
14. **左侧持续** — 屏幕左侧的历史也在区间内
15. **近期高潮** — 刚出现强力买入或卖出高潮
16.  — 顶部多头发力尖刺、底部空头发力尖刺，都突破失败反转
17. **腿细分** — 很多两小段后反向两小段

### 不确定 vs 紧迫
- 趋势 = **确定感**（相对确定）和**紧迫感**
- 区间 = **不确定感**（Hallmark）
- 经验交易者极少感到恐惧或贪婪，而是在这两种情绪之间切换

## 与相关概念的关系
- [[buy-vacuum-sell-vacuum]]：区间顶部/底部的磁吸现象 —— 是区间特征之一但机制足够独立，单独建页
- [[tight-trading-range]]：区间的一个特殊子类型，有自己的交易规则
- [[barbwire]]：紧密区间的极端形式（3+ 棒重叠含 DOJI）
- [[breakout-mode]]：当区间收敛到突破即将发生时，进入突破模式
- [[trading-range-quality]]：huangzongprice 量化版的两个硬性指标（≥8K + ≥2测），Brooks 原著用「足够长到失去短期预测力」定性描述
- [[channel-to-trading-range]]：通道如何演变为区间 → 当区间特征越来越多时确认转变
- [[fsm-market-cycle]]：区间是市场周期四阶段的核心组成部分
- [[breakout-mechanics]]：区间必然产生突破尝试 → 80% 失败

## 实战应用
当屏幕上出现 5+ 项区间特征时，切换到区间交易模式：「买低卖高刮头皮」。不要追突破——大部分会失败。在边界附近做逆势（Fade），在中间不交易。具体入场点见 Chapter 21 的止损/限价入场清单。

## 来源支撑
- [[book-brooks-trading-ranges]] — Part IV 引言（pp.634-653）

## 矛盾与待验证
- Brooks 用「不确定感」定性定义区间，huangzongprice 用 `n_in_tr >= 8` 和 `test_count >= 2` 定量定义 — 哪种更准确？可能取决于时间框架和品种
- 「80% 突破失败」是经验估计还是可量化统计？不同市场、不同 TF 是否有差异？
