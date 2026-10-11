# huangzongprice MES 交易复盘日志合集

## 元信息
- 作者：huangzongprice
- 日期：2025-10-28 至 2026-03-05
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`（96 篇）
- 提取方式：pdftotext（手写标注 → PDF → 文本）
- 文件规模：每篇 20-200 行，总计约 100 个文件

## 一句话摘要
huangzongprice 的 MES（Micro E-mini S&P 500）5 分钟 K 线实盘交易日志，横跨约 4.5 个月，使用 Brooks 价格行为学术语全程标注每日行情结构与每笔交易。

## 核心论点

### 日志结构
每篇日志包含以下固定组件：
1. **日型判断**：首行概括当日市场结构（如 `bear trend from the open then HL MTR`、`trading range all day`、`wedge bottom then HL MTR`）
2. **交易标注**：以 Brooks 速记符号逐棒标注关键事件（L1/L2/H1/H2 入场、STP/BE 止损与盈亏平衡、1R/2R/3R/4R 盈亏比、Bxx 棒号）
3. **MC 10+2 评分**：对关键交易节点执行 ，逐项量化市场背景
4. **高层级确认**：标注 15min/45min 的高层级信号与 ATM Straddle 波动率参考
5. **PTM 交叉引用**：引用过往交易日的类似行情（如 `PTM20250302`、`PTM20250412`），构建个人形态库
6. **心理座右铭**：`Best Loser Wins` 和 `For where your treasure is, there will your heart be also.` 反复出现
7. **双重复盘**：多数日期有"初版"（自我复盘）和"+gemini"（AI 辅助审查）两个版本，构成 

### 日志中反复出现的 Brooks 核心概念
- **H1/H2/L1/L2** — 趋势结构中基于回调计数的入场（H=多头回调，L=空头回调）
- **TBTL** — 十棒两腿，Post-Climax 反转确认
- **Climax / Climactic Reversal** — 买卖高潮，预示趋势暂停或反转
- **STC / BTC** — Sell The Close / Buy The Close，强趋势中失望交易者行为
- **AIL / AIS** — Always In Long / Short，市场主导方向判断
- **楔形 / Wedge** — 三推衰竭形态
- **MTR** — Major Trend Reversal，主要趋势反转
- **BO / Breakout Test** — 突破及回测机制
- **Spike and Channel** — 尖峰+通道趋势结构
- **Measured Move (MM)** — 测量走势目标投影
- **TR** — Trading Range 交易区间，与趋势的交替循环

### 交易策略偏好
- 偏好 **H2/L2 入场**（等第二次回调）胜过 H1/L1
- 大量 **刮头皮（scalp）** 交易，目标 1R-2R
- 严格使用 BE（盈亏平衡）止损移动
- 重视 **leg2**（第二腿）的盈亏比潜力
- 50% 回撤作为关键加仓位/止损位

## 提取出的新概念
- [[mc-checklist]] — MC 10+2 市场周期评分清单（huangzongprice 自研的标准化盘前/盘中评估表）
- [[emotions-trading|Best loser wins]] — "最佳输家"交易心理哲学（截断亏损让利润奔跑的心法）
- [[journal-huangzongprice-mes-review]] — 双重复盘工作流（初版自评 + Gemini AI 二次审查，人类-AI 协同复盘方法论）

## 与现有知识的冲突
- 无直接冲突。日志中的 Brooks 概念使用与已有 Wiki 理论页一致，证明 huangzongprice 对 Brooks 理论的理解与应用是连贯的。
- MC 10+2 清单是 huangzongprice 的独创量化框架，在 Brooks 原著中无直接对应——这是理论到实践的个性化落地。

## 与已有概念的关系
- [[fsm-market-cycle]] — 日志每日以市场周期判断开篇（趋势/TR/趋势恢复日/趋势性TR日）
- [[fsm-market-cycle]] — MC 10+2 清单可视为此概念的实盘操作化版本
- [[h2-l2-state-machine|H2/L2 State Machine]] — H2/L2 入场是日志中最频繁出现的入场信号
- [[climax]] — Climax + TBTL 是日志中反转判断的核心组合
- [[tbtl]] — 经常与 Climax 配合使用
- [[trade-management-system]] — 日志中的 BE/追踪止损操作与此概念一致
- [[trader-equation]] — 日志中 1R-4R 的盈亏记录体现交易者方程式的实际应用
- [[gap-reversal]] / [[opening-reversals]] — 日志中多次出现开盘缺口的交易机会
- [[atr-scaling]] — ATM Straddle 作为日内波动率参考
- [[swing-vs-scalp]] — 日志以刮头皮为主，偶有波段持仓
- [[emotions-trading]] — 日志中的心理座右铭和"Best Loser Wins"哲学
- [[trend-from-the-open]] — 开盘趋势日是日志中最常见的日型之一
- [[trending-trading-range-days]] — 趋势性TR日也是常见日型
- [[trading-range-quality]] — 日志中频繁判断 TR 的质量（TR 占比、ATM 波动率）

## 日志时间线概览
| 时段 | 篇数 | 特征 |
|------|------|------|
| 2025-10-28 ~ 2025-11-26 | ~20 篇 | 初版单版本，较短 |
| 2025-12-01 ~ 2025-12-31 | ~25 篇 | 开始出现 +gemini 双版本 |
| 2026-01-02 ~ 2026-01-30 | ~25 篇 | 双版本常规化，MC 评分格式化 |
| 2026-02-02 ~ 2026-03-05 | ~25 篇 | 格式稳定，引用 PTM 增多 |
