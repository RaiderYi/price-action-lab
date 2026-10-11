# MES 每日复盘合集（huangzongprice）

## 元信息
- 作者：huangzongprice
- 日期范围：2020-06-10 ~ 2026-03-05（约6年）
- 文件数量：302 个（含 68 个 Gemini AI 增强版）
- 覆盖交易日：135 个
- 原始位置：`raw/books/huangzongprice/MES*.md`
- 格式：pdftotext 提取自手写批注 PDF，文字部分可读但 OCR 碎片较多
- 标的：MES（Micro E-mini S&P 500）5分钟K线图

## 一句话摘要
huangzongprice 长达6年的 MES 5分钟图表每日复盘笔记合集，记录了从 Brooks 价格行为学理论到实战应用的完整演进轨迹——包含独创的"10+2"复盘评分体系和 AI 辅助复盘实验。

## 核心架构

### 每日复盘格式

每篇复盘遵循固定结构：

1. **日型总结**（第1行）：`MES 5 Min: <市场类型>` — 如 "bear trend from the open then HL MTR"
2. **棒线标注**：B1、B2……逐棒标注 Brooks 形态（L2、H1、BTC、STC、climax、TR、SPB 等）
3. **评分清单**（"10+2"体系）：对关键架构进行加权质量评级
4. **测量走势**（MM）：1R/2R/3R/4R 目标投影
5. **多时间框架**：45min/15min/5min 三层背景嵌套
6. **跨日引用**：PTM（Prior Trading Memory）标注历史相似形态日期
7. **Brooks 课程引用**：标注参考文献出处（如 "Brooks Trading Course 37A"）

### "10+2" 复盘评分体系

这是 huangzongprice 独创的**每笔交易执行质量复盘清单**（出现在多数复盘文件中）：

```
10+2 评分维度：
  -5%  K线质量（趋势棒判定）
  -5%  Cprior L/H（收盘 vs 前高低）
  -5%  doji（十字星惩罚）
  -5%  no tick gap（无跳动缺口）
  -10% BO mrk regime（突破市场体制不匹配）
  -5%  price control（价格控制）
  +5%  time control（时间控制）
  +5%  swing point 1ABR（波段点 ABR 确认）
  leg2 60%（第二腿概率估计）
```

该体系**不同于交易前的信号评分**（如 [[signal-scoring-synthesis]] 或 [[execution-scoring]]）——它是**交易后的执行质量审计工具**，用于回答"这笔交易按系统规则执行得如何"而非"该不该做这笔交易"。

### AI 辅助复盘（Gemini 版）

68 个文件标注 `+gemini`，时间集中在 2025-12 ~ 2026-03。Gemini 版本在原始批注基础上增加了：
- 更结构化的英文分析段落
- Brooks 课程原文引用（完整句子）
- PA 形态的自动识别补充
- 多时间框架的一致性验证

这是价格行为学领域**AI辅助交易复盘**的早期实践记录。

### 演进时间线

| 时期 | 特征 |
|------|------|
| 2020-06 ~ 2025-08 | 稀疏复盘，主要为关键交易日的手工批注 |
| 2025-08 ~ 2025-11 | 复盘频率增加，10+2评分体系逐渐成型 |
| 2025-12 ~ 2026-03 | 高频复盘 + Gemini AI 辅助实验，几乎每个交易日均有记录 |

## 提取出的新概念

### 新概念（1）

- [[book-huangzongprice-mes-daily-reviews]] — 每日复盘评分：10+2项标准化清单用于交易执行质量的逐笔回顾

### 已被已有概念覆盖的内容

以下在复盘中高频出现的概念已在 Wiki 中被覆盖：

| 复盘中的用法 | 对应概念 |
|-------------|---------|
| L2 sell/buy STP | [[h2-l2-state-machine|H2/L2 State Machine]] · [[setup-anatomy]] |
| BTC/STC | [[btc-stc]] |
| climax / climactic reversal | [[climax]] |
| TR / trading range | [[trading-range-quality]] · [[fsm-market-cycle]] |
| MM (Measured Move) | [[measured-move]] |
| SPB (Spike and PullBack) | [[spike-and-channel]] |
| AIL/AIS | [[always-in]] |
| HL DB / LH DT | [[major-trend-reversal|Major Trend Reversal]] |
| 20-gap bar | [[gaps]] |
| micro channel / ET | [[micro-channels]] |
| 80% fade | [[eighty-percent-rule]] |
| 40-60 rule | [[forty-sixty-rule]] |

## 与现有知识的互补

### 实战 vs 理论对照价值

这批复盘的核心价值不在于引入新理论概念，而在于：

1. **理论验证**：Brooks 理论在真实 MES 市场中的逐日验证记录
2. **模式频率**：哪些形态最常出现（L2/BTC/climax 是最高频操作）
3. **失败案例**：标注了大量 STC（Sell The Close/止损）、STP（止损）的真实失败交易
4. **时间框架嵌套**：45min/15min/5min 三层嵌套的具体应用示例
5. **AI 辅助复盘方法论**：人工批注 + AI 增强的协作模式探索

### 与已有复盘系统的对比

| 维度 | 本文（MES 复盘） | [[live-trading-monitor]] |
|------|-----------------|------------------------|
| 性质 | 交易后批注（PDF 手写） | 实时系统推送 |
| 评分 | 10+2 执行质量审计 | RS 评分 + 信号面板 |
| 时间框架 | 静态日复盘 | 动态实时监控 |

## 待办

- [ ] 提取 135 个交易日的日型分类统计（趋势日/区间日/反转日占比）
- [ ] 对 10+2 评分维度的权重做统计分析（哪些维度与实际盈亏相关性最高）
- [ ] 对比 Gemini 增强版与纯手工版的信息增量
- [ ] 与 A 股分析系统的每日复盘流程做方法论对齐
