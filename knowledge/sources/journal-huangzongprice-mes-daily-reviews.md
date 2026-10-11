# huangzongprice MES 每日复盘文集

## 元信息
- 作者：huangzongprice（部分含 Gemini AI 辅助分析）
- 日期：2025-10-28 ~ 2026-03-05（约 5 个月）
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`（约 300 个文件）
- 提取方式：pdftotext（手写笔记 PDF → 文字，部分 OCR 质量一般）
- 交易品种：MES（Micro E-mini S&P 500 期货）
- 时间框架：5 分钟 K 线（辅以 15min/45min 多时间框架）
- 状态：✅ 已消化（文集级处理，非逐日消化）

## 一句话摘要
huangzongprice 约 5 个月的 MES 日内交易每日复盘笔记，是 Brooks PA 理论在实战中的完整演练记录——包含信号评分、入场管理、心态反思和 AI 辅助分析。

## 核心论点

### 1. 复盘结构
每日复盘遵循统一模板：
- **日型总结**：一句话概括当日市场类型（如 "bear trend from the open then HL MTR"、"trending trading range all day"）
- **多时间框架**：45min/15min/5min 三级联动分析
- **逐棒标注**：B1, B2, ... 标注关键 K 线位置、信号类型（L1/L2/H1/H2）、入场/离场
- **交易记录**：实际入场（如 "B16 L4 sell STP, -0.5R"、"B7 L2 sell STP, 1R"）
- **10+2 评分**：对关键信号的 10+2 维度手动评分（见下方）

### 2. 10+2 信号评分清单（核心方法论）
huangzongprice 在复盘中反复使用的手动信号质量评分系统（总分 100%）：

| 维度 | 扣分项（示例） | 加分项（示例） |
|------|-------------|-------------|
| K 线质量 | doji -10%, 无 tick gap -5% | — |
| 前收盘位置 | C prior H/L -5% | — |
| BO 市场体制 | mrk regime -10% ~ -20% | — |
| 延迟腿 | late leg -10% ~ -20% | — |
| 价格控制 | — | swing point 1ABR +5% |
| 时间控制 | — | leg2 45%~70% |
| 腿类型 | complex leg 折扣 | simple leg 满分 |

常见得分区间：55%-70%（合格），<50%（放弃），>70%（优秀信号）。

### 3. 核心交易规则（散见于各日复盘）
- **突破三分类**：「BO Gap = Lack of Info / Spike = Controlled BO / Climax = Unusual Behavior」
- **测试成败**：「Test Success = Trend Resumption = Failed Reversal / Test Failure = New BO = Reversal」
- **分形视角**：「All PBs are TRs on smaller TF / All TRs are PBs on higher TF」
- **PTM 系统**：引用个人交易手册条目（PTM20250112、PTM20250302 等）作为规则来源
- **Brooks 高胜率清单**：多日复盘直接引用 Brooks 区间篇 60%+ 胜率的 9 条规则原文

### 4. 交易心理与哲学
- 引用 Tom Hougaard *Best Loser Wins* 的理念（"Best Loser Wins"、"Cost of Business"）
- "For where your treasure is, there will your heart be also"（每日复盘固定标语）
- Good Loss / BE（盈亏平衡）心态：反复出现 "BE" 出场决策
- FOMO 管理：多次记录 "Fear of missing out on profits"

### 5. AI 辅助复盘
- 约半数文件含 "+gemini" 标记 — Gemini AI 对同一交易日的独立分析
- Gemini 版本通常包含更结构化的分析：Al Brooks 视角 → Ali Afshari 视角 → Tom Hougaard 测试 → 评分
- 人类版更简洁、更倾向实战笔记；AI 版更系统、更倾向理论交叉验证
- 两个版本形成「实战笔记 vs 系统分析」的互补

## 提取出的新概念

以下概念由此文集首次引入 Wiki：

1. **[[rs-scoring]]** — 10+2 手动信号评分清单：huangzongprice 实战中使用的多维度信号质量评分（与代码实现的自动评分互补）
2. **[[journal-huangzongprice-mes-daily-reviews]]** — PTM 个人交易手册系统：个人交易规则的索引化管理方法
3. **[[climax]]** — 突破三类型（缺口/尖峰/高潮突破）：huangzongprice 对突破的实战三分类法
4. **[[journal-huangzongprice-mes-reviews]]** — MES 每日复盘方法论：结构化多时间框架复盘流程

## 与现有知识的冲突

### 10+2 评分 vs 现有评分系统
- 10+2 是**手动定性评分**（交易者在图表上逐项打分），与代码实现的 [[signal-scoring-synthesis]]（lFin/sFin 自动评分）和 [[execution-scoring]]（三因子加权）处于不同层面
- 10+2 的维度（价格控制、时间控制、腿类型）在自动评分中**无直接对应** — 这是人对「感觉」的量化尝试
- 冲突点：[[execution-scoring]] 有 bg×0.55+struct×0.25+sig×0.20 的精确权重，而 10+2 的权重分配是经验的、可变的 — 两种方法论的底层哲学不同（算法确定性 vs 人的概率判断）

### 突破三分类 vs 已有突破理论
- [[breakout-mechanics]] 关注突破→回调→恢复的**过程**，bo-gap-spike-climax 关注突破的**类型/性质**
- [[gaps]] 中的缺口分类与 "BO Gap" 不同 — 前者是 K 线之间的缺口，后者是「缺乏信息的突然突破」

## 备注
- 约 300 个文件覆盖 2025-10-28 至 2026-03-05（约 90 个交易日，含非交易日复盘和同一日多个版本）
- 文件名中的 "gemini" 指 Google Gemini AI 辅助分析，非 Gemini 交易所
- 部分文件因手写笔记 OCR 质量不佳，英文术语可读但中文连接词常有缺失
- PTM 条目（PTM20250112 等）引用的原始内容未包含在本目录 — 推测为 huangzongprice 的 Notion/Obsidian 个人知识库条目
- 与 [[article-huangzongprice-context-engine-v1]] 和 [[article-huangzongprice-execution-layer-v1]] 形成「方法论设计 → 代码实现 → 实战验证」三层闭环
- 已消化概念（无需新建）：H1/H2/L1/L2 信号体系、STC/BTC、SPB、MTR、楔形、高潮、测量走势、AIL/AIS — 这些 Brooks 核心概念已在 Wiki 中完整覆盖，复盘中的使用属于实战应用而非新理论
