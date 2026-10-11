# MES 复盘合集（2025-08 ~ 2026-03）

## 元信息
- 作者：huangzongprice
- 日期：2025-08-12 至 2026-03-05（约 150 份日复盘）
- 原始位置：`raw/books/huangzongprice/MES*.md`
- 格式：PDF → pdftotext（部分可读，图表层丢失）

## 一句话摘要
huangzongprice 的 MES（微型标普 500 期货）每日交易复盘笔记合集，覆盖约 7 个月、150+ 个交易日。包含了实盘信号评估、入场/离场标注和 Gemini AI 辅助分析。

## 核心论点

### 1. 复盘结构
每份复盘通常包含：
- **日型判断**：一行总结当日市场主旋律（如 "bear trend from the open"、"climactic reversal then trading range"、"trading range all day"）
- **逐棒信号标注**：`B1-B10 MC10+2` 格式的评分速记（见 [[mes-review-scoring]]）
- **入场记录**：`B7 L2 sell STP, 1R, 2R` — 棒号 + 信号类型 + 入场方式 + 盈亏结果
- **市场环境指标**：45min TR 状态、ATM Straddle 隐含波动率（见 [[atm-straddle-gauge]]）、5min TR 占比
- **多时间框架**：1min / 5min / 15min / 35min / 45min 多层级信号交叉验证
- **Gemini AI 解读**：标注 `+gemini` 的文件包含 AI 对关键信号棒的中文解读（如 "L1 STC 是高潮陷阱"、"SPB 三要素确认"）

### 2. 重复出现的交易主题
- **高潮→TR 过渡**：至少在 10+ 个交易日出现 — 开盘卖出/买入高潮后转入交易区间，随后 HL/LH MTR 反转
- **楔形底部→HL MTR**：楔形作为趋势末期信号，配合 TBTL 确认后反转
- **SPB（小回撤趋势）**：小回撤牛市/熊市趋势日，EMA 始终在一侧
- **TR 全天**：无方向的区间震荡日 — 刮头皮为主，不追突破
- **腿 2 / 复杂腿 2**：几乎所有信号入场都标注了腿计数（Leg1→Leg2），强调二次入场

### 3. 实盘中的 Brooks 概念应用
- **H1/H2/L1/L2**：最常用的入场信号层级
- **STC/BTC**：Sell/Buy The Close — 高潮后反向入场
- **Major HL/LH**：趋势反转的结构性确认
- **TBTL**：10 棒两条腿 — 高潮后 TR 确认
- **测幅（MM）**：几乎每份复盘都计算了测量目标
- **BO mark regime**：突破标记作为背景判断因子
- **Negative gap / Measured gap**：缺口分析

### 4. 常量元素
- "Best Loser Wins" — 每份复盘末尾的签名（Tom Hougaard 的交易心理书）
- "For where your treasure is, there will your heart be also" (Matthew 6:21) — 时间戳标记
- "by SC2" — 复盘模板来源标注

## 提取出的新概念

### 已创建概念页
- [[mes-review-scoring]] — MC10+2 信号棒评分速记系统：12 个评分维度的实盘评估框架
- [[atm-straddle-gauge]] — ATM 跨式期权作为日内波动率/区间预期指标
- [[review-methodology]] — huangzongprice 的三层复盘方法论：日型→逐棒评分→多TF验证

### 已存在于 Wiki 的概念（在复盘中大量应用）
[[climax]] · [[tbtl]] · [[major-trend-reversal|Major Trend Reversal]] · [[trend-from-the-open]] · [[trending-trading-range-days]] · [[wedge-gravity-dual-core]] · [[h2-l2-state-machine|H2/L2 State Machine]] · [[three-push-wedge|Three Push Wedge]] · [[measured-move]] · [[gaps]] · [[spike-and-channel]] · [[opening-reversals]] · [[trading-range-quality]] · [[always-in]] · [[buying-selling-pressure]]

## 与已有来源的关系
- 本合集是 Brooks 理论在 **实盘层面的应用记录**，与 Wiki 已有的理论层（Brooks 原著/课程笔记）和量化实现层（huangzongprice V1.5/V3 指标代码）形成三层互补
- 展示了 huangzongprice 如何将 [[brooks-signal-catalog]] 中的 16 种信号类型在真实图表中逐一识别和评分
- MC10+2 评分系统是 [[signal-scoring-synthesis]]（lFin/sFin 代码评分）的**人工复核版本** — 前者是 Pine Script 自动化评分，后者是交易者肉眼评分

## 与现有知识的冲突
- 复盘中的信号评分偶有与 Wiki 概念定义不完全一致的情况（如 "L1 STC" 作为入场信号，而 Wiki 中 L1 通常不被视为强信号），这是实盘灵活应用 vs 教科书的正常差异
- 复盘频繁使用 "leg2"（腿2/二次入场）概念，与 Brooks "二次入场更可靠" 原则一致，体现了实战中对二次入场的偏好

## 数据局限性
- PDF 提取后图表完全丢失，无法验证标注的信号棒形态
- Gemini AI 解读部分较为完整（标注 `+gemini` 的文件），但纯复盘部分有大量 PDF 碎片残留
- 145+ 份中的大部分文件 ≤2KB，仅信号速记，非完整文本分析
- 部分文件含备注：`2025.12` 可能是模板版本号
