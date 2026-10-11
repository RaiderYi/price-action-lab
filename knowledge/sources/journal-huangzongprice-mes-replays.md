# huangzongprice MES 每日复盘日志

## 元信息
- 作者：huangzongprice（Brooks PA 量化开发者）
- 日期范围：2025-01-05 ~ 2026-03-05（约 8 个月）
- 原始位置：`raw/books/huangzongprice/MES*.md`（约 146 个复盘文件 + 50 个 PDF 原档）
- 格式：PDF 手写图表标注 → pdftotext OCR 提取 → Markdown
- 品种：MES（Micro E-mini S&P 500）5 分钟 K 线图

## 一句话摘要
huangzongprice 约 8 个月、146+ 天的 MES 日线复盘日志——Brooks 价格行为学在真实交易中的完整实战记录，包含手写图表标注、10+2 评分框架和 Gemini AI 协同分析。

## 核心内容

### 复盘结构（每篇日志的固定格式）
1. **日类型概览**：一句话总结当日市场形态，如 "bear trend from the open then HL MTR"、"wedge top then failed BO up and bear SPB"
2. **图表标注**：在 MES 5 分钟 K 线图上逐根标注 Brooks 术语（swing point、H1/H2/L1/L2、BTC/STC、climax、wedge、PB、TTR、MM、SPB 等）
3. **10+2 评分**：对关键架构（setup）进行 10 项基础 + 2 项加成的量化评分
4. **交易记录**：入场/出场/盈亏标注（如 "B12 buy STP, 2R"、"B37 sell STP, BE"）
5. **Gemini 分析**（部分文件）：AI 协同解读图表——标注 Gemini 对每个架构的独立判断（Context/Hitting the Wall/Trap Analysis/Micro-Execution）

### 涉及的 Brooks 核心概念（按出现频率）
| 概念 | 在日志中的使用方式 |
|------|-------------------|
| H1/H2/L1/L2 | 架构入场计数，几乎每篇出现 |
| swing point | 主要摆动点标注（"major swing point"） |
| BTC/STC | 买入/卖出收盘动态识别 |
| climax | 买入/卖出高潮、高潮反转 |
| MTR (Major Trend Reversal) | HL MTR / LH MTR 反转日识别 |
| wedge | 楔形顶/底、抛物线楔形 |
| channel / spike and channel | 通道阶段、尖峰+通道 |
| PB / pullback | 回撤腿识别 |
| TTR / Tight Trading Range | 紧密区间识别 |
| MM / Measured Move | 测量走势目标投影 |
| SPB | 止损回撤（Stop Pull Back）管理 |
| 80/20 Rule | 趋势中 80% 反转失败 / 区间中 80% 突破失败 |
| Final Flag (FF) | 末端旗形反转信号 |
| TBTL | 十棒两腿反转确认 |
| AIS/AIL (Always In) | 市场主导方向判断 |

### Gemini AI 协同分析的独特贡献
约半数复盘文件包含 Gemini 的独立分析（文件标记为"+gemini"）。Gemini 的分析特点：
- **Context 先行**：先判断背景（趋势/TR/反转），再评架构
- **多理论家交叉验证**：引用 Al Brooks、Tom Hougaard、Ali Afshari 三人观点
- **"墙"（The Wall）概念**：识别阻力支撑的强硬度
- **"What-If" 分析**：对每个架构做反事实推演
- **Evolutionary Verdict**：给每个架构打 A/B/C 等级

### 跨文件重复出现的 PTM 引用
日志中频繁引用 `PTM`（推测为 Price Action Template Method 或 Personal Trading Manual）编号，如：
- PTM20241222、PTM20250525、PTM20250615、PTM20250727、PTM20250803
这些可能是 huangzongprice 的内部交易模板/规则编号系统。

## 提取出的新概念
本次 ingest 从复盘日志中提取了 2 个新概念（Wiki 此前未覆盖）：

1. [[journal-huangzongprice-mes-replays]] — 每日复盘的结构化方法论：日类型→图表标注→10+2评分→交易记录→AI协同分析
2. [[rs-scoring]] — 手工 10+2 架构评分框架：10 项基础评分（K线/收盘位置/Cpiror/十字星/tick gap/市场体制/晚腿/价格控制/时间控制/腿%）+ 2 项加成（摆动点 ABR/腿2%）

## 与现有知识的关联

### 对已有概念的实战验证
- [[eighty-percent-rule]]：日志中多次出现 "80% of reversal attempt fails in trend" 的实际应用
- [[h2-l2-state-machine|H2/L2 State Machine]]：H1/H2/L1/L2 是日志中最频繁使用的标注，验证了其在实战中的核心地位
- [[climax]]：买入/卖出高潮在日志中频繁出现，作为反转预警
- [[final-flag]]：FF（Final Flag）在日志中作为 TTR 后的末端反转信号
- [[three-push-wedge|Three Push Wedge]]：楔形标注在日志中高频出现

### 对量化系统的启发
- **10+2 评分框架**：提供了一个手工评分范本，可与 [[signal-scoring-synthesis]]（lFin/sFin 自动评分）交叉对照
- **SPB 止损管理**：日志中频繁出现的 SPB 技术，在现有 [[trade-management-system]] 中未覆盖
- **Gemini 协同分析**：为未来的 AI 辅助复盘系统提供方法论参考

### 三大理论家对话
日志中 Gemini 频繁引用三位交易教育者：
- [[al-brooks]]（PA 理论核心）
- Tom Hougaard（"Best Loser Wins"、"Price is truth"、"Trap Analysis"）
- Ali Afshari（"Simple Leg"、"Micro Channel"、MTR 简化方法）

## 与现有知识的冲突
- **无直接冲突**。复盘日志本质上是 Brooks 理论的实战应用记录，不提出新理论主张。
- 部分 OCR 乱码导致具体标注细节不可读，但不影响整体方法论价值。

## 待办
- [ ] 如有原始高质量图片，可考虑用多模态模型重新提取标注
- [ ] 统计 8 个月日志中各类日形态的分布（趋势日 vs TR 日 vs 反转日）
- [ ] 提取所有 PTM 引用编号，反向推导 huangzongprice 的交易规则体系
- [ ] 对比手动 10+2 评分与自动 RS 评分的一致性
