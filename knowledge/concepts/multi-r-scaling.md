---
title: "多R分批止盈"
phase: [range, transition]
signal_types: [pullback-entry]
tags: [分批止盈, 剩余, 保本, 减半, 验证]
difficulty: intermediate
related: [trade-management-system, default-profit-targets, trader-equation, position-sizing, protective-stops, journal-mes-review-collection]
char_count: 956
---
# 多R分批止盈

## 一句话定义
在多个风险倍数（1R/2R/3R/4R）处分批减仓，余仓跟踪止损的利润保护协议。

## 核心要点
- **目标层级**：1R → 2R → 3R → 4R，逐级递进
- **减仓规则**：典型模式为「1/3 2R」——在达到2R时减仓1/3，剩余2/3继续跟踪
- **余仓管理**：未减仓部分设置跟踪止损（trailing stop），允许捕捉超预期行情
- **核心逻辑**：在保证「不亏」的前提下（1R保本），分段锁定利润，同时保留「大赢」的可能
- **与交易者方程的关系**：多R分批止盈通过提高平均盈亏比（R:R）来降低对胜率的要求

## 与相关概念的关系
- [[trade-management-system]]：多R分批止盈是交易管理系统 SPB (Stop-Profit-Breakeven) 组件的参数化实现，提供了具体的减仓比例和触发点
- [[default-profit-targets]]：Brooks 默认利润目标（2x初始风险减半+3x减25%+剩余跟踪）→ 多R分批止盈是同一思想在MES实盘中的更激进版本（最高到4R）
- [[trader-equation]]：多R止盈通过提高平均回报来优化交易者方程
- [[position-sizing]]：分批止盈与仓位规模的联动——初始仓位的大小决定了每层的绝对金额
- [[protective-stops]]：跟踪止损 = 保护性止损的动态版本

## 实战应用
入场后立即设定：1R处移动止损至BE（保本），2R处减仓1/3，3R处再减1/3，剩余1/3用跟踪止损捕捉4R+。如果行情在2R前反转回BE，整体不亏。

## 来源支撑
- [[journal-mes-review-collection]]（40+份MES复盘中统一使用的出场协议）

## 矛盾与待验证
- 「1/3 2R」是否最优减仓比例（1/3 vs 1/2 vs 1/4）未经回测验证
- 4R目标的实现频率：复盘数据显示偶尔到达4R，但统计显著性未知
- 与 [[default-profit-targets]] 的 Brooks 标准（2x减半、3x再减25%）相比更激进——需要更大的行情才能充分发挥
