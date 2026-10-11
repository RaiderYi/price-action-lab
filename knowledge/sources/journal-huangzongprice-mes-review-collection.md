# huangzongprice MES 每日复盘合集

## 元信息
- 作者：huangzongprice
- 日期范围：2025-10-22 ~ 2026-03-05（约 4.5 个月）
- 资料数量：~100 份复盘记录（含 gemini AI 辅助标注版本）
- 原始位置：`raw/books/huangzongprice/MES*.md`
- 标的：MES（Micro E-mini S&P 500）5 分钟 K 线

## 一句话摘要
huangzongprice 的 MES 日内交易每日复盘笔记集，采用结构化 4 组件复盘系统（市场背景→交易执行审计→MC 评分→AI 辅助分析），是 Brooks 价格行为学在实际交易中的完整落地样本。

## 核心方法论

### 复盘结构（每份复盘包含 4 个组件）

1. **市场背景（第 1 行）**：一句话描述当日市场类型，如 "bear trend from the open then HL MTR"、"trading range all day"、"climactic reversal then trading range"
2. **交易执行审计**：记录每笔入场的棒线编号（如 B7 L2 sell STP）、入场理由、止损位、结果（1R/2R/BE/-1R）
3. **MC 10+2 评分**：对每个 Micro Channel 用加权清单逐项评分（详见 [[mc-daily-scoring]]）
4. **Gemini AI 辅助分析**（约 50% 的复盘包含）：对每笔交易用 Brooks 理论进行事后解读，标注执行缺陷、形态识别错误、可改进之处

### 核心元素

| 元素 | 说明 |
|------|------|
| **MC 评分** | 10+2 项加权评分清单，每项 ±5%~±20%，对微通道质量进行系统评估 |
| **PTM 引用** | Prior Trade Memory——引用历史相似交易日（如 `PTM20241222`），将当前形态与历史先例关联 |
| **"Best Loser Wins"** | 贯穿全部复盘的交易哲学信条——接受亏损是交易的必要成本 |
| **Bible 引用** | 每份复盘末尾：`For where your treasure is, there will your heart be also.` |
| **15min / 5min 双周期** | 所有入场标注 15min 和 5min 两个时间框架的信号 |
| **ATM Straddle** | 每份复盘记录当日 ATM 跨式期权隐含波动率作为市场情绪参考 |

### 复盘中的 Brooks 概念高频引用
- H1/H2/L1/L2 回调入场（最常用入场信号）
- TBTL（十棒两腿）反转确认
- BTC/STC（Buy/Sell The Close）强趋势动态
- Climax / Climactic Reversal
- OB (Outside Bar) / BOM (Breakout Mode)
- TTR (Tight Trading Range)
- Wedge / Failed Wedge
- AIL/AIS (Always In)
- MC (Micro Channel)
- Leg 2（第二腿入场）

### Gemini 标注的典型内容
- 识别执行缺陷（如 "The Execution Flaw"）
- 对照 Brooks Trading Course 章节进行理论验证（如 "Brooks Trading Course 37A"）
- 标注意外棒型（如 "Bull Surprise Bar"、"Outside-Opposite Cut"）
- 分析入场时机与回撤深度

## 提取出的新概念

本合集贡献了两个 Wiki 此前未覆盖的新概念：

1. [[mc-daily-scoring]] — MC 10+2 每日评分系统：huangzongprice 将 Brooks 微通道理论落地为可操作的加权评分清单
2. [[trading-journal-system]] — 交易日志系统：结构化 4 组件复盘方法论 + PTM 历史关联机制

## 与现有知识的关联

- 本资料是 [[huangzongprice]] 将 Brooks 价格行为学应用于实战的完整记录
- MC 评分系统是 [[micro-channels]] 概念在实战中的操作化落地
- PTM 系统是 Brooks "所有图表都是同一张图" 理念的实践工具
- 复盘中的入场信号直接对应 [[brooks-signal-catalog]] 中的 16 种信号类型
- 交易管理（STP/BE/1R/2R）与 [[trade-management-system]] 的 6 组件框架一致

## 限制与注意事项

- PDF 转文本质量差：原始文件为手写笔记 + 图表标注 PDF，pdftotext 提取后中文全部丢失、英文片段化严重
- 图表不可见：大量的价格形态标注、趋势线、通道线等信息存在于原始 PDF 图表中，无法从文本提取中获取
- MC 评分权重未完全公开：10+2 项的具体权重和计算公式需要查看原始笔记图表
- 部分复盘仅有 gemini 版本或仅有原始版本，两者不总是配套
