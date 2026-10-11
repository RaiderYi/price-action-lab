# MES 5-Min 日复盘日志（2025Q4-2026Q1）

## 元信息
- 作者：huangzongprice
- 日期：2025-10-28 ~ 2026-03-05（约 96 个交易日）
- 原始位置：`raw/books/huangzongprice/MES*.md`（~100 个 PDF→txt 文件）
- 品种：MES（微型标普 500 期货）
- 周期：5 分钟 K 线 + 15min/45min 高级别参考

## 一句话摘要

huangzongprice 的每日 Brooks 价格行为实战复盘日志，覆盖 4 个月 MES 日内交易，系统化记录市场类型判断、逐棒线标注、MC 10+2 评分、入场/离场分析和 AI 辅助评论。

## 核心内容

### 日志结构

每份复盘文件包含以下固定要素：

1. **单行市场总结**：如 "trend trading range all day"、"bear trend from the open then HL MTR"、"climactic reversal then trading range"、"wedge bottom then HL MTR"
2. **逐棒线标注**：B1, B2, B3... 结合 Brooks 术语逐棒线标注市场行为（L1/L2, H1/H2, STC, BTC, AIL/AIS, climax, OB, doji, wedge, TBTL, SPB 等）
3. **MC 10+2 评分**：对关键架构执行 MC 10+2 量化检查清单评分 → [[mc-10-plus-2-checklist]]
4. **多时间框架参考**：15min 和 45min 高时间框架背景标注
5. **入场记录**：含入场方式（STP/LMT）、止损止盈、实际结果（1R/2R/BE/-0.5R）
6. **引经据典**：
   - "For where your treasure is, there will your heart be also."（马太福音 6:21）——交易信念锚
   - "Best Loser Wins"（Tom Hougaard）——亏损管理哲学
7. **AI 辅助评论**（+gemini 文件）：Gemini AI 对特定交易的复盘评论，从 PA 角度分析入场缺陷和可改进点

### 市场类型统计（抽样）

| 日期 | 市场类型 | 关键形态 |
|------|---------|---------|
| 2025-09-25 | trend trading range all day | BO Test → PB vs early Rev |
| 2026-02-13 | trading range all day | CPI day, wedge bear flag, climactic reversal, 20-gap-bar |
| 2026-02-26 | sell climax from open then HL MTR | B1-B13 MC 10+2 65%, B26 L2 sell STP |
| 2026-02-27 | trading range all day | L4 sell STP, bear flag wedge, Outside-Opposite Cut |
| 2026-03-03 | wedge bottom then HL MTR | B4 L1 sell STP→i1R, B23 H1 buy STP, B28 Leg2 buy STP |
| 2026-03-04 | climactic reversal then TR | bull breakout reversal down, B4-B12 MC 10+2 65% |
| 2026-03-05 | bear trend from open then HL MTR | B7 L2 sell STP→3R, B32 climactic reversal TBTL TR |

### 反复出现的 Brooks 交易框架引用

- **Brooks Trading Course 视频引用**：29B/29D/29E (Climaxes), 36A (Trader's Equation), 37A (Trends), 42B (Climactic Reversals), 14E (Signal Bars)
- **PTM 引用**（Price Trading Manual / 交易准则）：PTM20241222, PTM20250126, PTM20250216, PTM20250302, PTM20250322, PTM20250412, PTM20250518, PTM20250525
- **核心原则反复确认**：
  - "Every flag is a trading range, and every trading range is a flag"
  - "A climax typically evolves into a trading range"
  - "You cannot have a reversal without a BO"
  - Probability of success ≥60% rules from Trading Ranges

### MC 10+2 实盘评分体系

这是日志中最系统的量化工具 → 详见 [[mc-10-plus-2-checklist]]

典型格式：
```
MC 10+2: -5%K, -5% Cprior L, -5% doji, -10% BO, mrk regime TR,
+5% price control major swing point 1ABR, +5% time control, Leg2 65%
```

## 提取出的新概念

- [[mc-10-plus-2-checklist]] — MC 10+2 实战评分清单（10 减分项 + 2 加分项）

## 与现有知识的关联

- **已有概念全部涉及**：日志中标注的每个术语（L2/H1/climax/TBTL/wedge 等）都已在 Wiki 中建立概念页
- **MC 10+2 为增量**：这个评分系统在之前的所有来源中均未出现，是实战中提炼的独立框架
- **与 [[brooks-signal-catalog]] 互补**：信号目录是「有哪些信号」，MC 10+2 是「这个信号好不好」
- **与 [[trade-management-system]] 互补**：交易管理是「入场后怎么办」，MC 10+2 是「入场前怎么打分」

## 与已有来源的关系

- 三本书 PDF 在此目录下有副本（趋势篇/反转篇/区间篇），但均为 pdftotext 中文乱码版本，内容已由 English/original 版本在 [[book-brooks-trends-revised]]、[[book-brooks-reversals]]、[[book-brooks-trading-ranges]] 中消化
- `分析背景要走哪几步.md` 同样乱码，已通过 [[article-20250519-brooks-context-4-pine]] 和 [[brooks-four-step-context]] 覆盖
