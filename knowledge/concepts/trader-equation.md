---
title: "交易者方程 (Trader's Equation)"
phase: [trend, range, breakout]
signal_types: [breakout-entry]
tags: [交易者方, 回报, probability, risk, 胜率]
difficulty: intermediate
related: [z-score, scaling-in, position-sizing, always-in, trade-management-system, default-profit-targets, stop-run-trap, emotions-trading, course-notes-PA-study, course-37-42-trading-trends, encyclopedia-brooks-price-action-manual, forty-sixty-rule]
char_count: 1312
---
# 交易者方程 (Trader's Equation)

## 一句话定义
`(胜率 × 回报) > (亏损概率 × 风险)` —— 所有交易决策的数学基础，正数即具有数学优势（Edge）。

## 核心要点
- **公式**：`(Probability_win × Reward) > (Probability_loss × Risk)`
- **等价形式**：胜率 40%、盈亏比 2:1，则 `0.4 × 2R > 0.6 × 1R` → 期望值 +0.2R，可稳定盈利
- **胜率通常在 40%-60% 之间**：强势突破时接近 60%，交易区间中可能只有 40%
- **三个变量不可兼得**：高概率、高回报、低风险 —— 完美交易不存在，因为总有机构站在对面
- **两个简化变量**：概率 + 风险回报比（RR）。每笔交易都是在概率和 RR 之间做权衡
  - 早期入场 → 好 RR（小风险大回报）+ 低概率
  - 晚期/突破入场 → 高概率 + 差 RR（远止损小回报）

## 与相关概念的关系
- [[z-score]]：Z 值检验交易者方程在统计上是否稳定可靠；方程为正 ≠ 策略可靠
- [[scaling-in]]：加仓改变方程——提高概率但增加总风险（恶化 RR）
- [[position-sizing]]：仓位大小由方程中的 Risk 项推导
- [[always-in]]：Always In 方向判断直接影响概率项——顺势时概率 > 50%
- [[trade-management-system]]：交易管理的 6 组件服务于方程中的 Reward 和 Risk 项
- [[default-profit-targets]]：交易者方程的实战机械化应用——确保数学期望为正的获利方法
- [[stop-run-trap]]：止损触发=风险变量临时放大；50%陷阱概率影响实际风险计算
- [[emotions-trading]]：概率的不确定性是交易情绪的根源——方程告诉你数学上可行，但心理上需承受连续亏损

## 实战应用
每一笔入场前问自己：在当前市场背景下，我的胜率大约多少？止损和盈利目标各多少点？代入方程——如果是正数，且 Z 值稳定，入场就是合理的。

## 来源支撑
- [[course-notes-PA-study]] (30A-30E)
- [[course-37-42-trading-trends]]（视频37B：40-60规则详解；视频39C：没有完美交易）
- [[encyclopedia-brooks-price-action-manual]]（交易者方程完整章节 + 40-60 规则原始阐述）
- [[forty-sixty-rule]]：Brooks 对概率变量的经验取值依据（90% 时间概率 40%~60%）

## 矛盾与待验证
- Brooks 说"概率永远不确定"，但 Wiki 中的 RS 评分系统尝试用 10+2 维度量化信号质量——这是否能在一定程度上"逼近"概率？量化系统是否验证了方程中的 Probability 项？
