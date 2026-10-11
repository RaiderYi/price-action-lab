# MES 每日复盘合集 (2025.09 - 2026.03)

## 元信息
- 作者/交易者：SC2（推测，文件标注 "by SC2"）
- 日期范围：2025-09-25 ~ 2026-03-05
- 原始位置：`raw/books/huangzongprice/`
- 提取方式：pdftotext（部分 OCR 损坏——中文内容丢失，Brooks 英文术语可辨识）
- 文件数量：约 100 个（含初版、gemini 版、纯手工版）
- 交易标的：MES（Micro E-mini S&P 500），5 分钟 K 线为主

## 一句话摘要
交易者 SC2 在 6 个月内对 MES 的每日 Brooks 价格行为复盘手稿——包含了从市场结构判定、bar-by-bar 交易标注、MC 评分到 LLM（Gemini）辅助分析的完整实战记录。

## 核心论点

### 复盘结构（每篇 3-5 层）
1. **市场结构判定**：一句话总结当日市场类型（如 "small pullback bull trend all day"、"wedge bottom then HL MTR"、"trend trading range all day"）
2. **Bar-by-Bar 交易标注**：按 K 线编号记录入场/出场（如 `B7 L2 sell STP`、`B23 H1 buy STP`）、止损移动（`BE`）、测量走势（`MM`）、盈亏（`1R/2R/3R`）
3. **MC 评分（10+2 维度）**：对关键架构做 Market Cycle 评分，维度包括：K 线形态（±5%）/ 前高前低位置/ doji 判定/ 跳空缺口/ 突破标记/ 价格控制/ 摆动点质量/ ABR/ 时间控制/ 腿计数 + 阶段标签（L1/L2/L3）
4. **Gemini AI 分析**（约半数文件）：将 PA 手稿提交 Gemini 做二次解读，标注 "The Execution Flaw"、"The Bull Surprise"、"Evolutionary Verdict" 等分类，提供 Brooks 理论对照
5. **Best Loser Wins 哲学**：每篇末尾标注，反映 Tom Hougaard "最佳输家赢"的交易心态框架

### Brooks 术语在实战中的使用模式
- **入场**：H1/H2（多头回调入场）、L1/L2（空头反弹入场）、OB（外包棒突破）
- **离场**：STP（止损触发）、STC（收盘卖出/BTC 多头收盘买入）、SPB（保护性止损移动）
- **市场背景**：AIL/AIS（始终在场内多头/空头）、TR（交易区间）、TTR（紧密交易区间）
- **形态**：wedge（楔形）、MTR（主要趋势反转）、climax（高潮）、channel（通道）、spike（尖峰）
- **测量**：MM（测量走势）、1R/2R/3R（风险倍数目标）

### 资料来源引用链
- **PTM**：推测为 "Plan The Market" 或交易计划笔记本，标注日期如 `PTM20241222`、`PTM20250412`、`PTM20250525`——这些是交易者的预判框架参考
- **Brooks Trading Course**：明确引用课程视频编号（如 14E、37A）
- **Brooks 原著**：引用 *Trading Price Action - Trading Ranges* 原文章节（如 "Probability of success of 60 percent or better..." 段落）
- **Gemini**：AI 辅助分析标注，系统性地对每个交易架构做二次验证

## 提取出的新概念

### 与本 Wiki 的增量价值
这些复盘文件的最大价值**不是新理论**——所有 PA 概念已被 Wiki 覆盖。增量在于：

1. **实战应用范例**：概念页讲"是什么"，复盘展示"怎么看/怎么做"——如 H1 buy STP 在真实 K 线序列中的具体位置
2. **MC 10+2 评分实战**：此前只在 `[[article-20250519-brooks-context-4-pine]]` 中描述过四步上下文框架，复盘展示了评分在实际交易中的逐步应用
3. **LLM 辅助 PA 分析**：Gemini 在交易复盘中的应用模式——这是 Brooks PA 学习/验证的新方法
4. **Best Loser Wins 整合**：将 Tom Hougaard 的交易心理框架与 Brooks PA 技术分析系统整合

### 建议抽取的新概念
- **`daily-pa-review`**：Brooks PA 每日复盘方法论——从市场结构判定→MC 评分→交易标注→AI 辅助验证的四层递进
- **`mes-trading-context`**：MES 5 分钟 K 线的交易环境特征（ATM 跨式宽度/ABR/开盘 gap 的影响）

## 与现有知识的冲突
无重大冲突。复盘是 Brooks 正统 PA 的应用，与 Wiki 理论一致。但有以下观察：
- 复盘中的 MC 评分维度（10+2）比 `[[brooks-four-step-context]]` 的 4 步框架更细粒度，可能代表交易者自创的评分体系
- "Leg2"、"complex leg 2" 等腿计数方式在 Brooks 原著中无明确定义，可能为交易者个性解读

## 文件清单（代表性样本）

| 日期 | 文件 | 市场类型 |
|------|------|---------|
| 2025-09-25 | `MES2050925复盘.md` | trend trading range all day |
| 2026-01-07 | `MES20260107复盘.md` | trading range then reversal down |
| 2026-02-06 | `MES20260206复盘+gemini.md` | small pullback bull trend all day |
| 2026-03-03 | `MES20260303复盘+gemini.md` | wedge bottom then HL MTR |
| 2026-03-05 | `MES20260305复盘.md` | bear trend from the open then HL MTR |

完整文件 100 个，覆盖 2025-09-25 至 2026-03-05。

## 待办
- 如能获得原生 PDF（非 pdftotext），可重新提取完整中文注释
- PTM 笔记本（PTM20241222 等）如能获得，可作为独立来源消化
