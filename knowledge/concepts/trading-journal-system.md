---
title: "交易日志系统"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, failed-breakout]
tags: [ptm, brooks, min, trading, stp]
difficulty: intermediate
related: [mc-daily-scoring, always-in, brooks-signal-catalog, trade-management-system, playbook, trader-equation, journal-huangzongprice-mes-review-collection]
char_count: 2040
---
# 交易日志系统

## 一句话定义
huangzongprice 的结构化 4 组件每日交易复盘方法论，含 PTM（Prior Trade Memory）历史关联机制，是将 Brooks 价格行为学从理论到实战的过渡桥梁。

## 核心要点
- 4 组件结构：市场背景（1 行）→ 交易执行审计 → MC 评分 → AI 辅助分析
- PTM 系统（Prior Trade Memory）：每笔交易关联到历史相似交易日，形成跨时间的模式识别网络
- 双时间框架分析：15min 定背景方向 + 5min 定精确入场
- 每份复盘标注 ATM 跨式期权隐含波动率作为市场情绪参考维度
- "Best Loser Wins" 哲学贯穿全部复盘——将接受亏损制度化
- Gemini AI 辅助标注为第二步的质量控制层——对原始判断进行事后理论验证

## 4 组件详解

### 1. 市场背景（1 行总结）
格式：`MES 5 Min: [日类型]`
- 趋势日：bear/bull trend from the open, trend resumption, HL/LH MTR
- 区间日：trading range all day, trend trading range all day
- 转折日：climactic reversal then trading range, wedge bottom then HL MTR
- 目的：为当日所有交易提供最顶层的背景定调

### 2. 交易执行审计
格式：`[时间框架] B[N] [信号] [入场方式], [结果]`
- 例：`15min B7 L2 sell STP, I1R 2R`
- 例：`5min B23 H1 buy STP, BE`
- 记录：棒线编号、信号类型（H1/H2/L1/L2/BTC/STC/OB）、入场方式（STP/LMT）、结果（1R/2R/BE/-1R）
- 失败交易特别标注执行缺陷，如 "(The Execution Flaw)"、"(The Bull Surprise)"、"(The Outside-Opposite Cut)"

### 3. MC 10+2 评分
见 [[mc-daily-scoring]]，每份复盘对当天所有微通道独立评分

### 4. Gemini AI 辅助分析
- 对每笔交易用 Brooks 理论进行事后验证
- 标注关键形态：Barbwire、OB、Failed Breakout、Bull Surprise、Buy Climax 等
- 引用 Brooks Trading Course 具体章节（如 `Brooks Trading Course 37A`、`29B`、`42B`）
- 标注改进方向：入场时机、回撤深度判断、TTR 处理

## PTM 系统

| 要素 | 说明 |
|------|------|
| PTM 引用格式 | `PTM[YYYYMMDD]`（如 `PTM20241222`、`PTM20250412`） |
| 关联逻辑 | 当前交易形态与历史某日的形态高度相似→引用该日期作为参考先例 |
| 理论基础 | Brooks "所有图表本质上是一张图"——市场的重复模式在不同时间重复出现 |
| 实战价值 | 遇到不确定形态时，PTM 提供历史锚点——"上次出现类似形态时发生了什么" |

## 与相关概念的关系
- [[mc-daily-scoring]]：MC 评分是日志系统的核心组件
- [[always-in]]：AIL/AIS 为日志中的市场背景判断提供方向框架
- [[brooks-signal-catalog]]：16 种信号是日志中交易审计的命名基础
- [[trade-management-system]]：日志中的 STP/BE/1R/2R 结果与 TMS 六组件框架一致
- [[playbook]]：v3 的 5 种玩法分类为日志中的策略归属提供了系统化框架
- [[trader-equation]]：每笔交易的结果统计最终服务于交易者方程式验证

## 实战应用
交易日结束后，按 4 组件结构完成复盘，将 PTM 引用写入，标注关键棒线，对每笔交易执行审计。次日开盘前回顾最近 3-5 份复盘以进入交易状态。

## 来源支撑
- [[journal-huangzongprice-mes-review-collection]]

## 矛盾与待验证
- PTM 系统未见自动化工具支撑——全部为手动标注，规模化后维护成本高
- Gemini AI 标注仅覆盖约 50% 的复盘且集中在新近日期，早期复盘无 AI 辅助
- 日志格式在 2025-10 到 2026-03 期间持续演变（早期较简略，后期增加了 MC 评分和 AI 标注），格式标准化程度仍在迭代中
