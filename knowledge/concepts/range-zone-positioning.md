---
title: "区间区域定位"
phase: [trend, range, breakout, transition]
signal_types: [wedge, reversal-entry, flag, failed-breakout]
tags: [反转, atr, playbook, 区间区域, 上沿]
difficulty: intermediate
related: [playbook-engine, trading-range-quality, trend-strength-filter, support-resistance, article-background-v3-upgrade]
char_count: 1068
---
# 区间区域定位

## 一句话定义
在震荡区间中明确当前价格位置——上沿、下沿还是中部，据此决定是否允许交易及允许哪种类型的交易。

## 核心要点
- **三层定位**：
  - 区间上沿（`rangeEdgeShortFlag`）：允许做空反转，优先看假突破失败/边缘楔形
  - 区间下沿（`rangeEdgeLongFlag`）：允许做多反转，优先看假突破失败/边缘楔形
  - 区间中部（`rangeMiddleFlag`）：否决所有交易——中部入场 RR 最差
- **探测方法**：EMA 交叉计数、ATR 压缩比、P3 在区间中的位置评分
- **输出变量**：`rangeDetected`, `rangeUpper`, `rangeLower`, `rangeZone`, `rangeMiddleFlag`, `rangeEdgeLongFlag`, `rangeEdgeShortFlag`
- **方法论根源**：Brooks 强调"在区间中部不要交易"——中部方向最不确定，RR 最差

## 与相关概念的关系
- [[playbook-engine]]：区间边缘触发 playbook=3 区间边缘反转
- [[trading-range-quality]]：区间质量评定（≥8K + ≥2次边界测试）是区间定位的前置条件
- [[trend-strength-filter]]：区间判定与趋势过滤互斥——两者不会同时为真
- [[support-resistance|Support/Resistance]]：区间边界本质上就是 Major S/R，Module C 的 S/R 环境识别直接为区间定位提供边界

## 实战应用
- 区间上沿 + playbook=3 → 优先找空头反转信号（假突破、楔形、三推衰竭）
- 区间下沿 + playbook=3 → 优先找多头反转信号
- 区间中部 → 无论信号多好都不入场，等待价格走向边界
- ATR 压缩（区间收窄）→ 即将突破的预警，应从"边缘反转"切换为"突破观察"

## 来源支撑
- [[article-background-v3-upgrade]]

## 矛盾与待验证
- 区间边界的具体定义（价格距离上沿/下沿多少百分比算"边缘"？）未在设计稿中量化。
- ATR 压缩比的阈值（多小算"压缩"？）同样待标定。
- 现有的 FSM 已有基础的 range 检测和唐奇安边界判断，区间区域定位是增强还是替代现有逻辑？设计稿中未明确。
