# huangzongprice MES 每日复盘合集

## 元信息
- 作者：huangzongprice
- 日期范围：2025-09-25 ~ 2026-03-05（约 5.5 个月）
- 文件数量：46 个复盘文件（含 Gemini AI 分析版）
- 原始位置：`raw/books/huangzongprice/MES*.md`
- 品种：MES（微型标普500期货），5min / 1min K线

## 一句话摘要
huangzongprice 长达 5.5 个月的 MES 期货日内交易日志——每笔交易按 Brooks 信号类型入场/出场，含手写 MC 10+2 上下文评分和 Gemini AI 辅助交易分析。

## 核心论点

### 1. 结构化复盘模板
每篇复盘均包含以下要素：
- **日类型判定**（顶行）: 如 "trend trading range all day"、"bear trend from the open then HL MTR"、"bull broad channel all day"、"wedge bottom then HL MTR"
- **MC 10+2 上下文评分**：对关键波段按 12 项维度做 +5%/-5%/-10%/-20% 加减分
- **逐笔交易记录**：入场信号类型（L1/L2/H1/H2/BTC/STC）+ 止损 + 结果（1R/2R/-1R/BE）
- **测量移动标记**：1R MM、2R MM 标记目标和实际到达
- **ATM 期权数据**：当日的 Straddle 定价（%）
- **关键价位标记**：Major Swing Point、trendline、EMA 位置
- **Brooks 课程引用**：精确到视频编号（如 "Brooks Trading Course 29D Climaxes"）

### 2. MC 10+2 上下文评分体系
这是复盘中最独特的元素——一个手动的 12 维波段时间评分清单：

| 维度 | 评分 | 说明 |
|------|------|------|
| K线质量 | -5% | 趋势棒质量差 |
| C vs prior H/L | -5% | 收盘位置不利 |
| Doji | -5% | 十字星/犹豫 |
| Tick gap | -5% | 无跳空缺口 |
| BO/市场体制 | -10% | 突破/区间状态不利 |
| 特殊减分项 | -10%~-20% | 高潮反转/末期腿/楔形/TR |
| 价格控制 | +5% | 多/空方控价 |
| Major Swing Point | +5% | 处于主要摆动点 |
| 1ABR | +5% | 1倍平均棒线波幅 |
| 时间控制 | +5% | 多方/空方掌控时间 |
| Leg2 百分比 | +5%~ | 第二腿强度评级 |

> 此评分体系与后期 Pine Script 实现的 [[ctx-scoring]]（ctx1/ctx2/ctx3 0-1 分数 + Step4 否决）共享相同设计思想，可视为 **人工先行版 → 自动化后行版** 的进化关系。

### 3. 日类型分类模式
从 5.5 个月的复盘中提取的高频日类型：
- **trend trading range all day**（最常见）— 倾斜的 TR 中双向交易
- **trading range all day** — 纯横向区间，边界反转交易
- **bear/bull trend from the open** — 开盘即单边
- **climactic reversal then trading range** — 高潮→TBTL→TR
- **wedge bottom/top then HL/LH MTR** — 三推楔形反转为 MTR
- **bull/bear broad channel** — 宽通道日内趋势

### 4. Gemini AI 辅助分析
约 30+ 篇复盘包含 Gemini AI 对特定交易的点评，分析维度包括：
- **Context Recognition**（背景识别）：趋势/TR/突破判定
- **Signal & Entry Mechanics**（信号与入场机制）：L2 陷阱、OB 突破
- **Trade Management & Risk**（交易管理与风险）：止损位置、BE 时机
- **Mathematical Expectancy**（数学期望）：概率 vs 回报权衡
- **Trap Analysis**（陷阱分析）：Second Leg Trap、Outside-Opposite Cut
- **Timing & Drawdown**（时机与回撤）：入场急躁 vs 耐心等待

### 5. 交易结果统计（抽样）
从可读样本中统计的典型日结果：1-3 笔交易/日，R 倍数范围 -1R ~ 4R，BE（保本出）频繁出现。

### 6. 反复出现的经典实战教训
- **The Execution Flaw**：在背景不支持的信号上入场（如 TR 中追 L2、高潮后立即反向）
- **Second Leg Trap**：高潮后的 L2 常是陷阱（post-climax TBTL 需要 10+ 棒冷却）
- **Surprise Bar 后不急于反向**：大棒经常标记 TR 开始而非反转
- **Micro Channel Blockade**：紧通道内的 H1/H2 入场被微通道否决
- **1R vs Leg2**：1R 目标的交易 ≠ Leg2 延续交易，概率结构根本不同

## 提取出的新概念
1. **[[rs-scoring|10+2 scoring]]** — MC 10+2 上下文评分清单：huangzongprice MES 复盘中的手动 12 维波段评估框架
2. **[[review-huangzongprice-mes-daily-journal]]** — 每日复盘方法论：从日类型判定→上下文评分→逐笔分析→AI辅助→教训提炼的完整流程

以下概念已在之前 ingest 中创建，本合集为其提供实战案例支撑：
- [[ctx-scoring]]（MC 10+2 可视为早期手动版）
- [[surprise-bar]]（多篇复盘中出现 Surprise Bar 实战处理）
- [[three-push-wedge|Three Push Wedge]]（wedge bottom/top 复盘中高频出现）
- [[climax]]（climactic reversal → TBTL 复盘中高频出现）
- [[major-trend-reversal|Major Trend Reversal]]（HL MTR 多篇复盘的核心主题）
- [[final-flag]]（wedge/末期旗复盘中出现）
- [[trading-range-quality]]（TR 日复盘的区间判定）
- [[traps-in-out]]（Second Leg Trap、Outside-Opposite Cut）
- [[protective-stops]]（复盘中的 BE/BE+1/追踪止损操作）
- [[trade-management-system]]（多点位分批出场）

## 与现有知识的冲突
- **MC 10+2 vs ctx-scoring**：MC 10+2 的 12 维度加减分制与 ctx-scoring 的三层 0-1 数值评分在方法论上一致但在具体维度上有差异。MC 10+2 更像 **交易前检查清单**，ctx-scoring 更像 **自动化评分引擎**。两者的关系已在 [[rs-scoring|10+2 scoring]] 和 [[ctx-scoring]] 中交叉标注。
- **Second Leg Trap 未独立建概念**：复盘中的"Second Leg Trap"是 [[traps-in-out]] 在牛市高潮后的具体实例，不单独建页。
- **PTM 引用体系未建概念**：复盘中的 PTM（如 PTM20241222, PTM20250412）是作者的个人交易原则记忆系统，由于无法从 raw 中还原其出处和完整内容，仅在来源页中标注。

## 价值评估
本合集是 Wiki 中唯一的 **连续性实战交易日志**——不同于理论书籍（Brooks 原著）、课程笔记（Brooks Trading Course）、量化代码（WG V1.5/V3），它展示了 Brooks 理论在每天真实市场中的具体应用和不断试错的过程。特别是 MC 10+2 评分体系，为理解 [[ctx-scoring]] 的设计思路提供了"需求来源"视角。

## 已知局限
- **PDF 手写 OCR 导致部分文字乱码**：中文注释和图表标注区有碎片残留，但不影响核心交易数据的可读性
- **部分日期的 gemini 版和纯复盘版内容重复**：同一笔交易可能在两个文件中出现（手动复盘 + Gemini AI 复盘），已在来源页中合并处理
- **ATM 数据不连续**：部分日期没有 Straddle 定价数据
