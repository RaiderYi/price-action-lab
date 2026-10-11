# huangzongprice MES 每日复盘合集

## 元信息
- 作者：huangzongprice
- 日期范围：2025-10-06 ~ 2026-03-05（约 5 个月）
- 文件数量：约 100 份（含 .md 文本版 + .pdf 原版）
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`
- 提取方式：pdftotext（部分 + Gemini AI 补充分析）
- 时间框架：5min K 线执行，15min/45min 背景，MES（微型标普 500 期货）

## 一句话摘要
huangzongprice 的 MES 日交易日志合集——每日用 Brooks PA 语言标注 5min K 线序列 + MC10+2 评分系统自评每笔交易 + PTM（Prior Trading Memory）跨日模式交叉引用。这是 Brooks 价格行为学在真实日内交易中最完整的实战记录。

## 核心结构（每份复盘的标准格式）

每份复盘包含以下固定元素：

### 1. 日类型标签（Regime Label）
一行总结当日市场主导形态，例如：
- `bear trend from the open then HL MTR` — 开盘空头趋势→高位主要趋势反转
- `climactic reversal then trading range` — 高潮反转→区间震荡
- `bear trend from the open then bull trend and TR` — 空转多+区间
- `trend trading range all day` — 全天趋势性区间
- `bear trend from the open then trend resumption` — 趋势恢复
- `sell climax from the open then HL MTR` — 卖出高潮→MTR
- `bear trend from the open then bull SPB all day` — SPB 反弹全天

### 2. 逐棒标注（Bar-by-Bar Annotation）
按 B1, B2, B3... 序列标注每根 5min K 线的 PA 身份：
- **入场信号**：L1/L2 sell STP、H1/H2 buy STP、Bx buy/sell LMT
- **离场信号**：STC（Sell The Close）、BTC（Buy The Close）
- **形态标签**：climax、TBTL、MC（Micro Channel）、TTR（Tight Trading Range）、OB（Outside Bar）、IB（Inside Bar）、doji、spike、wedge
- **位置标记**：EMA、swing point、Globe X low/high、ATH、50% PB
- **状态标记**：AIL（Always In Long）、AIS（Always In Short）、BLSHS（Buy Low Sell High Scalp）、SPB（Strong Pullback）

### 3. MC10+2 交易评分卡
每笔交易都附带 12 维度评分表（见 [[mc-ten-plus-two-scoring]]），格式为：
```
Bx MC10+2 -5%K, -5% Cprior, -5% doji, -5% no tick gap, -10% BO mrk regime, 
-10% late leg, +5% price control, +5% time control, ...
```
正分=加分项，负分=扣分项，综合得分指示交易质量。

### 4. 交易结果记录
- 入场棒和入场方式（STP/LMT）
- 风险管理（BE 移动、trailing stop）
- 盈亏倍数（1R / 2R / 3R / 4R / -1R）
- 止损触发记录（"STP -> BE" 表示从止损移到盈亏平衡）

### 5. 时间框架嵌套
- 45min K 线：TR 宽度、方向、Straddle 溢价
- 15min K 线：入场信号、swing point 确认
- 5min K 线：执行、微结构（MC、TTR、climax）
- ATM Straddle 数据：每日隐含波动率参考

### 6. PTM 交叉引用系统
格式如 `PTM20250322`、`PTM20250420`，引用历史上相似市场环境的交易日（见 [[ptm-cross-reference]]）。

### 7. 其他固定元素
- **圣经引用**（每份末尾）：「For where your treasure is, there will your heart be also.」（马太福音 6:21）
- **"Best Loser Wins" 水印**：`...... ...... ----by SC2`
- **日期标注**：`YYYY.MM.DD` 中文日期格式
- **+gemini 版本**：部分文件附带 Gemini AI 对关键交易的中英文混合深度分析

## 核心论点

### Brooks PA 实战验证
这是 Brooks 价格行为学在真实 5min 期货交易中最完整的实战应用记录。每根 K 线都用 Brooks 语言标注（H1/H2/L1/L2、BTC/STC、climax、TBTL、MC、wedge、SPB 等），验证了 Brooks 理论在日内交易中的实际可操作性。

### 结构化交易复盘的价值
MC10+2 评分系统+PTM 交叉引用构成了一套完整的「交易复盘系统」——不仅记录对错，更量化为每个决策维度打分并跨日对比。这是从「凭感觉复盘」到「系统化复盘」的质变。

### 时间框架嵌套的实战落地
45min/15min/5min 三时间框架嵌套不是理论概念，而是每日实际执行的框架——45min 判 TR 边界和方向，15min 确认信号，5min 执行和离场。

## 提取出的新概念

以下概念在本次 ingest 中新建，均源于 MES 复盘合集的独特方法论：

- [[mc-ten-plus-two-scoring]] — MC10+2 交易评分系统（12 维度逐项打分）
- [[mes-review-protocol]] — MES 结构化复盘协议（日类型→逐棒标注→评分卡→PTM 引用）
- [[ptm-cross-reference]] — PTM 跨日模式交叉引用系统

## 与现有知识的冲突

### 评分维度差异
MC10+2 评分维度与已有 [[signal-scoring-synthesis]]（lFin/sFin 五因子合成）和 [[execution-scoring]]（三因子加权 0.55/0.25/0.20）存在显著差异：
- MC10+2 是**交易后复盘评分**（回顾性），维度最多（12 项）、最细化
- signal-scoring-synthesis 是**信号生成时评分**（前瞻性），五因子合成
- execution-scoring 是**执行决策时评分**（bg×0.55+struct×0.25+sig×0.20）
- 三种评分系统的权重体系完全不同，目前未见统一或互相引用的证据

### OCR 质量限制
原始 PDF 的 pdftotext 转换质量差——中文几乎全部丢失，K 线标注碎片化，图表内容无法提取。+gemini 版本虽然补充了 AI 分析，但原始标注的完整性已不可恢复。本来源页提取的方法论和概念仅基于残留的英文术语和结构化元素推断。

## 待办
- [ ] 如有条件，用更好的 OCR 工具重新提取原始 PDF
- [ ] 统计 MC10+2 各维度的平均分和权重分布（需要逐份手工提取）
- [ ] 提取 PTM 引用图谱（哪些日期的哪些形态被频繁交叉引用）
- [ ] 分析日类型标签的分布（哪种市场环境出现频率最高）
- [ ] 对比 MC10+2 评分与实际盈亏的相关性
