# huangzongprice MES 每日复盘合集

## 元信息
- 作者：huangzongprice
- 日期：2025-09-25 ~ 2026-03-05（约 5.5 个月）
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`（52 个文件）
- 提取方式：pdftotext（OCR 质量一般，含 PDF 碎片残留）

## 一句话摘要
huangzongprice 对 MES（Micro E-mini S&P 500）期货的每日收盘后复盘笔记，包含多周期图表标注、MC 评分、交易执行记录和 Gemini AI 辅助分析。

## 核心论点

### 1. 复盘框架
每篇复盘遵循统一结构：
- **一句话日概**：顶部标注当日市场类型（如 "bear trend from the open then HL MTR"）
- **多周期分析**：45min → 5min → 1min 逐级标注关键价位和结构
- **MC 评分**：每段行情标注 MC10+2 评分，含逐项 ±% 调节
- **交易执行记录**：标注入场棒（STP = 止损价入场）、目标（1R/2R/3R/4R）、止损调整（BE = 盈亏平衡）
- **参考来源标注**：引用 Brooks Trading Course 视频编号（如 14E, 29B）和 PTM 日期

### 2. MC 评分实战注释
在实战复盘中，MC 评分系统展示了各维度的具体取值：
```
MC10+2 -5%K, -5%Cprior, -5%doji, -10%BOmrk regimeTR, 
+5% price control major swing point, +5% time control leg2 75%
```
表明实战中对 K 线质量、收盘位置、市场阶段（TR vs 趋势）、价格控制（major swing point 附近）和时间控制（腿2百分比）的权重调节。

### 3. Gemini AI 辅助复盘
部分文件（标注 +gemini）含 Gemini 对具体交易的 AI 分析，例如：
- "The L1 Trap" — L1（Low 1）陷阱识别：B34 惊喜棒使 B35 的 L1 变为低质量信号
- "Immediate Failure" — 外包棒后的立即失败判定
- AI 给出 Evolutionary Verdict（演变判定），将原始标注与 Brooks 理论对照

### 4. 实战语言记号体系
复盘中使用的简洁注记语言：
- `STP` = 止损价入场（Stop Entry），`OB` = 突破点（Outside Bar 或 Order Block）
- `STC` = 收盘价出场（Sell/Buy The Close）
- `STB` = 止损出场，`BE` = 移至盈亏平衡
- `cxbar` = 高潮棒（Climax Bar），`spike` = 尖峰走势
- `TTR` = 紧密交易区间（Tight Trading Range）
- `CHOB` = Close Higher Open Bar
- `RSK` = 相对强弱 K 线，`IB` = Inside Bar
- `MC` = Market Context 评分标注
- `PTM` = Prior Trading Memory（历史交易记忆，标注日期）

### 5. 时间跨度与覆盖
- **52 个交易日**覆盖约 110 个自然日
- 含 Gemini AI 辅助版：约 20+ 篇
- 最早：2025-09-25（MES2050925复盘.md）
- 最晚：2026-03-05（MES20260305复盘.md）
- 多周期：45min（高级别背景）、5min（交易周期）、1min（精细入场）

## 提取出的新概念

### 创建的
- [[daily-trade-review-framework]] — 每日交易复盘框架：从一句话日概到 MC 评分到多周期标注的完整复盘方法论
- [[trade-review-notation]] — 复盘速记记号体系：STP/STC/STB/BE/cxbar/TTR 等实战缩写语言

### 已覆盖的（不重复创建）
以下概念在复盘中被大量实战应用，但已在 Wiki 中有对应概念页：
- [[climax]] — 高潮识别（cxbar 标注）
- [[trend-resumption]] — 趋势恢复（"trend resumption" 日概）
- [[major-trend-reversal|Major Trend Reversal]] — MTR 识别（"HL MTR" 标注）
- [[trading-range-quality]] — TR 质量（TTR 标注、TR 背景切换）
- [[three-push-wedge|Three Push Wedge]] — 楔形（"failed wedge" 标注）
- [[ctx-scoring]] — MC 背景评分（MC10+2 实战注释）
- [[spike-and-channel]] — 尖峰+通道（spike 标注）
- [[gaps]] — 缺口（tick gap, micro gap 标注）
- [[measured-move]] — 测量走势（MM 标注，1R/2R 目标投影）
- [[protective-stops]] — 止损（STP, BE, 追踪止损）
- [[brooks-four-step-context]] — Brooks 四步上下文（实战应用）

## 与现有知识的冲突

### 与量化系统的张力
复盘中大量使用 Brooks 定性判断（"Major HL"、"climactic reversal"、"failed wedge"），而 huangzongprice 的量化系统（WG V1.5/V3）将这些概念转化为精确的 ATR 倍数和状态机规则。复盘中的"双轨制"——人工定性判断 + 代码量化信号——展示了实际交易中两者如何互补。

### MC 评分与 Pine Script 实现的差异
复盘中标注的 MC10+2 评分使用了 % 调整项（如 `-5%K`, `+5% price control`），但 Pine Script 实现中的评分权重未公开。复盘笔记提供了评分系统的实战校准参考。

## 三本 Brooks 书（OCR 降级副本）

此目录下还包含三本 Brooks 中文版的 pdftotext 输出，均因 OCR 乱码不可读：

| 文件 | 行数 | 状态 |
|------|------|------|
| `价格行为交易之趋势篇 中文 木羊（修订版）.md` | 3,180 | OCR 乱码，中文全部丢失，仅残留英文术语碎片 |
| `价格行为交易之反转篇 中文 木羊（党生版）.md` | 3,356 | OCR 乱码，同上 |
| `价格行为交易之区间篇 中文 木羊.md` | 3,623 | OCR 乱码，同上 |
| `分析背景要走哪几步.md` | 89 | OCR 乱码，几乎无内容 |

这些书的内容已通过以下更优质来源消化：
- 趋势篇：[[book-brooks-trends-revised]]（罗光海译 修订版）、[[book-brooks-reading-price-charts]]（英文原版）
- 反转篇：[[book-brooks-reversals]]（木羊 党生版 + 英文原版）
- 区间篇：[[book-brooks-trading-ranges]]（木羊版 + 英文原版）
- 分析背景：[[article-20250519-brooks-context-4-pine]]（Pine Script 工程化版）

**建议**：如需获取可读书籍，应从 `raw/books/al-brooks-series/` 目录读取（已 ingest 的优质版本），或将 huangzongprice 持有的原始 PDF 重新 OCR。
