# huangzongprice MES 日内复盘日志集 (2025.08–2026.03)

## 元信息
- 作者：huangzongprice
- 日期：2025-08 ~ 2026-03（约100篇，覆盖~8个月）
- 原始位置：`raw/books/huangzongprice/MES*.md`
- 品种：MES (Micro E-mini S&P 500) 5分钟K线
- 提取方式：手写标注 PDF → pdftotext → OCR碎片

## 一句话摘要
huangzongprice 的 Brooks 价格行为学日内交易实战日志——每篇包含日类型标签、逐棒H1/H2/L1/L2注释、10+2背景评分、具体入场/止损/退管记录，其中~30篇附带 Gemini AI 辅助分析。

## 核心内容

### 日志结构
每篇复盘通常包含：
1. **日类型标签**：如 "bull trend from the open then trading range"、"bear trend from the open then LL MTR"
2. **棒线标注**：B1-Bn 逐棒标注，标注 H1/H2/L1/L2、swing point、measured move、wedge、SPB、BTC/STC 等 Brooks 关键形态
3. **背景评估**：10+2 评分体系（微通道长度/棒线重叠度/K线实体百分比/BO突破模式/EMA位置/价格控制/时间控制/Leg2概率等）
4. **交易记录**：入场（buy STP / sell STP）、止损（STP）、盈亏比（1R/2R）、保本（BE）、pass（跳过）

### 日类型分布（部分样本）
- **趋势日**：bull/bear trend from open all day, trend resumption
- **混合日**：trend from open → TR, TR → trend, wedge bottom then bull trend
- **区间日**：expanding TRI, TR day, trading range then small pullback trend
- **反转日**：LL MTR, HL MTR, midday reversal, climactic reversal

### 多框架融合
日志中频繁引用三类交易思想：
- **Al Brooks**：价格行为结构（H1/H2/L1/L2、SPB、楔形、高潮、测量走势、80%法则）
- **Tom Hougaard**："Best Loser Wins" 交易心理——"I expect it to work immediately"、"Good Loss"、"Run!"、BE快速移动
- **Ali Afshari**：背景质量评估、Simple Leg、Micro Channel 判定

### PTM 系统
大量标注 `PTM20241222`、`PTM20250412`、`PTM20250112` 等日期引用——这是 huangzongprice 的个人模式匹配系统，将当前K线形态与历史相似形态做对照（详见 [[journal-mes-collection-202508-202603]]）。

### AI 辅助复盘
~30篇包含 "gemini" 版本的复盘，展示了 AI 对同一图表的独立分析——包括评分（A+/A/B+/C+/D）、多框架注释（Brooks/Hougaard/Afshari视角）和交易管理评估。

## 提取出的新概念
- [[journal-mes-collection-202508-202603]] — PTM（Pattern-Matching）日期参照系统：将历史K线形态按日期编码为个人模式库
- [[journal-mes-collection-202508-202603]] — MES复盘方法论：日类型→棒线标注→背景评分→交易记录→AI复核的五步流程

## 与现有知识的关联

### 已有概念的应用验证
日志为以下 Wiki 概念的实战应用提供了直接证据：
- [[brooks-signal-catalog]] — 16种信号类型在真实K线中的逐棒出现
- [[h2-l2-state-machine|H2/L2 State Machine]] — H1/H2/L1/L2 在每根棒线上持续更新
- [[trend-from-the-open]] — 开盘趋势日的20%/20%/60%概率分布被反复引用
- [[eighty-percent-rule]] — "80% of reversal attempts fail in a trend" 多次出现
- [[ctx-scoring]] — 10+2 背景评分系统与 `brooks-four-step-context` 形成对照
- [[trading-range-quality]] — TR 质量判定规则（≥8K、≥2测试）在实战中应用
- [[climax]] — 高潮反转的信号识别（climactic reversal, consecutive climaxes）
- [[protective-stops]] — 止损管理（STP/BE/1R/2R）的逐笔记录
- [[trade-management-system]] — 完整的入场→止损→BE→追踪→退出的全流程

### 与量化系统的关系
日志中的 10+2 评分体系与 [[article-huangzongprice-context-execution-linkage-setup]] 中描述的 Context Engine 评分系统高度对应，但在手动交易中增加了更多定性维度（如 "price control"、"time control"、"major swing point" 等）。

## 与现有知识的冲突
无冲突——本日志集是已有 Brooks 理论的实战应用，不引入新理论观点。

## 备注
- 三本 Brooks 中文译著（趋势篇/反转篇/区间篇）在 `raw/books/huangzongprice/` 中与 `raw/books/al-brooks-series/` 完全重复，未重复 ingest
- `分析背景要走哪几步.md` 为 OCR 乱码，内容不可读，跳过
- 日志均为 pdftotext 从手写标注 PDF 提取，术语密集但结构碎片化——BM（棒线编号）、Brooks术语、PTM日期引用为主
- 这是 Wiki 首次 ingest huangzongprice 的实战交易内容，与之前所有理论/量化来源形成互补
