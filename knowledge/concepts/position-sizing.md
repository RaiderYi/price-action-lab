---
title: "仓位规模 (Position Sizing)"
phase: [range]
signal_types: []
tags: [仓位, 账户, 风险, brooks, 我不在乎]
difficulty: intermediate
related: [trader-equation, z-score, scaling-in, trade-management-system, emotions-trading, i-dont-care-size, money-stop, course-notes-30-36-prerequisites, encyclopedia-brooks-price-action-manual, course-slides-brooks-price-action-fundamentals]
char_count: 1397
---
# 仓位规模 (Position Sizing)

## 一句话定义
用止损点数反推仓位大小，确保每笔交易的风险不超过账户的设定百分比——这是连接策略与资金管理的桥梁。

## 核心要点
- **止损决定仓位**：先确定止损距离（基于技术位置），再根据 `仓位 = (账户 × 风险%) / 止损点数` 计算可交易的手数/股数
- **新手规则**：每笔交易风险 ≤ 账户的 1%。例如 10,000 美元账户，每笔最多亏 100 美元
- **"我不在乎"仓位 (I Don't Care Size)**：练习阶段交易最小规模，允许自己做正确的事而不考虑金钱——不能致富，但可以最低成本学习
- **Emini 示例**：$10,000 账户 → 风险 $100 → 2 点止损 → 最多 1 张合约
- **外汇示例**：$10,000 账户 → 风险 $100 → EURUSD 100 点止损 → 10,000 单位；或 20 点止损 → 50,000 单位
- **Z 值与仓位**：Z 值越高（策略越可靠），每笔可冒的风险百分比越大（优秀交易者 2-3%，Z≈5 时可更高）
- **初学者必亏**：无论什么系统，初学者都会因为犯错而亏损——这是学习的代价，所以必须小仓位

## 与相关概念的关系
- [[trader-equation]]：方程中的 Risk 项直接用于仓位计算
- [[z-score]]：Z 值决定每笔交易可冒的风险百分比上限
- [[scaling-in]]：加仓后的总仓位暴露不能超过仓位规模上限
- [[trade-management-system]]：仓位规模是交易管理的前置条件——先算仓位，再设定止损/BE/追踪
- [[emotions-trading]]："我不在乎"仓位是情绪控制的唯一有效手段——仓位小到你不关心盈亏时，才能客观跟随机构
- [[i-dont-care-size]]：Brooks 仓位管理的心理核心——先做对的事，赚钱是副产品
- [[money-stop]]：Brooks 资金止损法——以 ADR 百分比设定止损距离，以此反推仓位

## 实战应用
每笔交易前执行三步：① 确定技术止损位置 → ② 计算止损点数 → ③ `仓位 = 账户 × 1% / 止损点数`。计算结果向下取整，绝不超仓。

## 来源支撑
- [[course-notes-30-36-prerequisites]]（Video 30C Slide 8-10, Video 33A~G）
- [[encyclopedia-brooks-price-action-manual]]（仓位管理完整章节——"我不在乎"仓位、止损反推仓位、账户规模建议）
- [[course-slides-brooks-price-action-fundamentals]] Slide 2602-2607（Money Stop 与仓位规模的关系）

## 矛盾与待验证
- Brooks 建议新手每笔 ≤1%，但 A 股市场（T+1、涨跌停限制）的止损距离与 Emini/Forex 差异巨大——A 股的仓位公式是否需要特殊调整（如考虑流动性、停板风险）？
- 本 Wiki 的 A 股分析系统中仓位计算逻辑是否已对齐 Brooks 的"止损反推仓位"原则？
