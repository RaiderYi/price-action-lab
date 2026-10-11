---
title: "MES 结构化复盘协议"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, swing]
tags: [step, 分钟, min, trend, 复盘协议]
difficulty: intermediate
related: [live-trading-monitor, signal-dashboard, mc-ten-plus-two-scoring, ptm-cross-reference, trade-management-system, huangzongprice-mes-reviews]
char_count: 2230
---
# MES 结构化复盘协议

## 一句话定义
huangzongprice 的 MES 日内交易七步复盘法——从日类型标签到 PTM 交叉引用，将 Brooks PA 理论落地为可复现的每日交易审计流程。

## 核心要点
- 时间框架：MES 5min K 线执行，15min/45min 背景参考
- 协议覆盖完整交易生命周期：盘前背景→盘中标注→盘后评分→跨日对比
- 非自动化：逐棒手工标注（或带 AI 辅助），强调人工复盘的学习价值
- 对比：与 [[live-trading-monitor]]（实时监控系统）和 [[signal-dashboard]]（信号面板）是互补关系——前者管"盘中看什么"，本协议管"盘后复盘什么"

## 七步复盘流程

### Step 1：日类型标签（Regime Label）
用一句话定义当日主导市场形态。标签决定了后续所有入场策略的优先顺序。常见类型：
- **趋势日**：`bear/bull trend from the open`
- **趋势恢复**：`trend resumption`
- **反转日**：`HL MTR` / `LH MTR` / `climactic reversal`
- **区间日**：`trading range all day` / `trend trading range days`
- **SPB 日**：`bull/bear SPB all day`（Strong Pullback 主导）
- **混合日**：`bear trend then bull trend and TR`

### Step 2：时间框架背景（HTF Context）
- 45min K 线：TR 边界、方向偏向、波动率（ATM Straddle 溢价）
- 15min K 线：主要 swing point、入场窗口
- Globe X high/low 标记

### Step 3：逐棒 PA 标注（Bar-by-Bar Annotation）
按 B1→B2→B3... 序列为每根 5min K 线标注 Brooks PA 身份：
- **棒型**：trend bar / doji / OB / IB / climax bar
- **信号**：H1/H2/L1/L2、wedge、TBTL、double top/bottom
- **入场**：STP（Stop 入场）/ LMT（Limit 入场）
- **离场**：BTC（Buy The Close）/ STC（Sell The Close）
- **状态**：AIL/AIS、BLSHS、SPB
- **位置**：EMA 关系、swing point、50% PB、MC formation

### Step 4：MC10+2 交易评分
为每一笔已成交交易填写 12 维度评分卡（见 [[mc-ten-plus-two-scoring]]），识别高频失误模式。

### Step 5：交易结果记录
- 入场棒号和入场类型（STP/LMT）
- 止损逻辑和 BE 移动时机
- 盈亏倍数（1R/2R/3R/-1R）
- 止损触发/过早离场的反思

### Step 6：PTM 交叉引用
标注与历史上相似市场形态的交易日编号（`PTM20250322` 等，见 [[ptm-cross-reference]]），建立跨日模式记忆。

### Step 7：收盘总结
- ATM Straddle 溢价与日波幅对比（市场定价 vs 实际波动）
- 当日最佳/最差交易
- Brooks 课程引用（Video XX 相关内容验证）
- 圣经引用（个人纪律仪式）

## 与相关概念的关系

- [[live-trading-monitor]]：盘中实时推送 vs 盘后手工复盘——同一交易系统的「盘中」和「盘后」两面
- [[signal-dashboard]]：7 维度诊断面板——盘中「看什么」，复盘协议「回顾什么」
- [[mc-ten-plus-two-scoring]]：复盘协议的 Step 4 评分子系统
- [[ptm-cross-reference]]：复盘协议的 Step 6 跨日对比子系统
- [[trade-management-system]]：6 组件自动化管理——复盘协议中的止损/BE/追踪评估直接对应管理系统的各组件

## 实战应用
每天收盘后，严格按照七步流程走一遍：先写日类型标签（15 秒）→ 回顾 HTF（2 分钟）→ 逐棒标注（5-10 分钟）→ MC10+2 评分（3 分钟/笔）→ 记录结果（1 分钟）→ PTM 引用（2 分钟）→ 总结（2 分钟）。总量约 20-30 分钟/天。

## 来源支撑
- [[huangzongprice-mes-reviews]] — 约 100 份复盘文件，覆盖 5 个月交易日

## 矛盾与待验证
- **协议是否标准化**：七步流程是从复盘文件的结构中推断的，huangzongprice 可能未明确文档化此协议——存在不同日期的复盘完整度不一致的情况
- **+gemini 版本的角色**：部分复盘有 Gemini AI 的补充分析。AI 是替代了手工标注还是作为辅助？复盘协议是否包含 AI 辅助这一步？
