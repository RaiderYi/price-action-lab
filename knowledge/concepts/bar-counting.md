---
title: "数棒法 (Bar Counting)"
phase: [trend, range, breakout]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, flag]
tags: [bar, brooks, 都是, high, huangzongprice]
difficulty: intermediate
related: [h2-l2-state-machine, three-push-wedge, double-top-bottom, fsm-market-cycle, book-brooks-price-action-manual, al-brooks]
char_count: 1066
---
# 数棒法 (Bar Counting)

## 一句话定义
通过计数回调中下降/上升的腿数来确定入场时机的 Brooks 基础方法——H1/H2/L1/L2 系统。

## 核心要点
- **H1 (High 1)**：上升趋势中，当某根 K 线的低点低于前一根 K 线的低点时，该 K 线就是回调的开始。在此 K 线高点上方挂止损买单，即为 H1 入场。
- **H2 (High 2)**：如果 H1 未被触发、市场继续下跌形成第二腿，新回调 K 线上的止损买单即为 H2。**所有双底都是 H2 买入架构**。
- **H3 (High 3)**：第三腿回调，通常是楔形牛旗。
- **L1/L2/L3**：下降趋势中的镜像概念。
- **H4**：锯齿形回调（在艾略特波浪中相当于 zigzag），也可视为"第一个 H2 失败、重新计数"的结果。

## 与相关概念的关系
- [[h2-l2-state-machine|H2/L2 State Machine]]：huangzongprice 将 H2/L2 量化为状态机——本概念是其 Brooks 原始理论来源
- [[three-push-wedge|Three Push Wedge]]：任何三推形态都是楔形——H3 = 楔形牛旗、L3 = 楔形熊旗
- [[double-top-bottom]]：所有双底都是 H2 买入架构、所有双顶都是 L2 卖出架构
- [[fsm-market-cycle]]：数棒法在突破后趋势中最可靠——通道阶段的 H2 比区间内的 H2 胜率更高

## 实战应用
当看到趋势中的回调时：数腿。第一腿回调 = 挂 H1 止损单。如果 H1 未触发、回调加深 = 挂 H2 止损单。数不清时不要纠结——看到好的牛/熊信号棒直接入场即可。

## 来源支撑
- [[book-brooks-price-action-manual]]（第 28-30 页专章：Bar Counting）
- [[al-brooks]]（Reading Price Charts Bar by Bar 全书基础工具）

## 矛盾与待验证
- 较小时间框架上（如 1min vs 5min），同一个"高 2"可能对应不同的计数——Brooks 明确说"计数不重要，看信号棒质量"
- 与 huangzongprice 的 H2/L2 状态机在量化标准上有差异：Brooks 更依赖主观判断，huangzongprice 添加了超时保护和精确的量化阈值
