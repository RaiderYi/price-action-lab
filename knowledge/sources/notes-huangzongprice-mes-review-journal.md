# huangzongprice MES 复盘日志合集

## 元信息
- 作者：huangzongprice
- 日期范围：2025-01-05 至 2026-03-05（约 14 个月）
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`（151 个条目，各含 .md + .pdf）
- 品种：MES（Micro E-mini S&P 500）
- 主时间框架：5 分钟 K 线（部分 1 分钟 / 15 分钟 / 45 分钟）
- 格式：PDF 手写笔记 → pdftotext 提取 → 部分含 Gemini AI 辅助分析
- OCR 质量：⚠️ 中等 — 英文术语可辨识，中文部分碎片化，需结合 Brooks 术语体系解读

## 一句话摘要
huangzongprice 约 14 个月的 MES 日内交易日报，以 Brooks 价格行为学为理论框架，包含每根 K 线的逐棒分析、入场/出场/仓位管理记录和 AI 辅助复盘——是 Brooks 理论实战落地的最完整一手记录。

## 文件结构

每个交易日条目通常包含以下层次：

1. **日型概览**（第 1 行）：一句话分类，如 "bear trend from the open then HL MTR"、"trading range all day"、"climactic reversal then trading range"
2. **逐棒分析**：按 K 线编号（B1, B2, ...）记录关键事件
3. **MC 10+2 评分**：对微型通道的 10 因子评分系统
4. **实际交易记录**：入场类型（STP/LMT/STC/BTC）、P&L（R 倍数）
5. **Gemini AI 分析**（部分文件）：AI 对关键入场的中文 PA 解读
6. **跨时间框架参考**：引用 15min / 45min / 1min 图表
7. **Brooks 课程引用**：指向具体视频（如 "Brooks Trading Course 29B"）

## 核心速记系统

huangzongprice 发展了一套高度压缩的 Brooks 术语速记，以下是主要符号：

| 速记 | 全称 | 含义 |
|------|------|------|
| B1, B2, ... | Bar 1, Bar 2, ... | K 线编号（从当日第 1 根起） |
| H1/H2/H3/H4 | High 1/2/3/4 | 多头回调计数（更高低点） |
| L1/L2/L3/L4 | Low 1/2/3/4 | 空头回调计数（更低高点） |
| AIL / AIS | Always In Long/Short | 总在场内多头/空头 |
| STC / BTC | Sell/Buy The Close | 收盘卖出/买入 |
| STP | Stop Order | 突破入场（stop 单） |
| LMT | Limit Order | 限价入场（回调入场） |
| SPB | Small Pullback Bull Trend | 小回撤牛市趋势 |
| MC | Micro Channel | 微型通道 |
| TR / TTR | Trading Range / Tight TR | 交易区间 / 紧交易区间 |
| MM | Measured Move | 测量走势 |
| TBTL | Ten Bars Two Legs | 10 棒两条腿 |
| OB / IB | Outside Bar / Inside Bar | 外包棒 / 内包棒 |
| EMA | Exponential Moving Average | 20 EMA |
| BE | Breakeven | 保本止损 |
| MTR | Major Trend Reversal | 主要趋势反转 |
| HL | Higher Low | 更高低点 |
| 1R, 2R, -1R | Risk multiples | 盈亏（R 倍数） |
| cxbar | Climax Bar | 高潮棒 |
| BO | Breakout | 突破 |
| RSK | Resistance | 阻力 |
| leg1 / leg2 | Leg 1 / Leg 2 | 第一腿 / 第二腿 |

## MC 10+2 评分系统

多份复盘出现一套 MC（微型通道）10+2 因子评分法，用于评估微型通道突破的质量：

| 因子 | 权重 | 说明 |
|------|------|------|
| K 线质量 | -5% | 信号棒强弱 |
| Cprior (H/L) | -5% | 收盘位置 vs 前高/低 |
| doji | -5% | 十字星惩罚 |
| BO mrk regime | -10%~-20% | 突破市场状态（趋势 vs TR vs 高潮反转） |
| price control | +5% | 价格控制权 |
| swing point 1ABR | +5% | 波段点 ATR 倍数 |
| time control | +5% | 时间控制权 |
| leg 完成度 | 55%~70% | 腿形完成百分比（最重要因子） |
| late leg | -10% | 末段腿惩罚 |
| climax/TBTL | 特殊标记 | 高潮后的 TBTL 状态 |
| 总评估 | — | 综合得分用于背景许可判断 |

> ⚠️ 此评分的精确计算公式在复盘笔记中未公开，上述信息从分散的批注中重建。与 Wiki 已有的 [[ctx-scoring]]（Ctx 上下文评分）和 [[execution-scoring]]（三因子执行评分）属于不同层级的评估体系——MC 10+2 聚焦于单条微型通道的质量评估。

## 日型分布

从可辨识的日型概览中提取的常见分类：

| 日型 | 出现频率 | Brooks 对应概念 |
|------|---------|---------------|
| trading range all day | 高 | [[trading-range-quality]] |
| trend from the open | 中高 | [[trend-from-the-open]] |
| bear/bull trend then TR | 中 | [[spike-and-channel]] |
| wedge bottom then MTR | 中 | [[three-push-wedge|Three Push Wedge]] · [[major-trend-reversal|Major Trend Reversal]] |
| climactic reversal then TR | 中 | [[climax]] · [[tbtl]] |
| trending trading range | 中低 | [[trending-trading-range-days]] |
| small pullback bull/bear trend | 中低 | [[micro-channels]] |
| HL MTR / LH MTR | 低 | [[major-trend-reversal|Major Trend Reversal]] |

## 跨时间框架分析习惯

复盘文件展示 huangzongprice 的多时间框架分析框架：

1. **45 分钟**：HTF 背景（PTM 标记 — Prior Trend/Market structure），判断当日大方向
2. **15 分钟**：中间框架，用于波段交易入场
3. **5 分钟**：主交易框架，所有 K 线编号和分析基于此
4. **1 分钟**：精细入场/出场时机

ATM Straddle（跨式期权隐含波动率）被用作日波动率预期参考，常见值 0.55%~0.68%。

## 交易管理习惯

从逐棒记录中提取的交易管理特征：

- **入场方式**：STP（突破追入）为主，LMT（限价回调）为辅
- **止损移动**：BE（保本）在 1R 后常见；部分记录显示过早移 BE 导致被扫
- **利润目标**：1R~2R 为常规目标，偶尔出现 4R（如 L1 STC 在高潮后）
- **仓位**：多数记录未标注仓位大小
- **胜率**：未汇总统计，单日记录显示盈亏交替（-1R 与 +1R/+2R 交替）

## 反复出现的 Brooks 课程引用

| Brooks 视频 | 引用频率 | 相关主题 |
|------------|---------|---------|
| 29B, 29D, 29E (Climaxes) | 高 | 高潮反转、TBTL |
| 37A (Always In) | 中 | AIL/AIS 方向判断 |
| 42B (Trading Climactic Reversals) | 中 | 高潮反转交易 |
| 12A (Market Cycle) | 低 | 市场周期 |
| 14E (Spike) | 低 | 尖峰特征 |

## 反复出现的交易格言

| 格言 | 来源 | 含义 |
|------|------|------|
| "Best Loser Wins" | Tom Hougaard | 接受亏损、快速止损是赢家特质 |
| "For where your treasure is, there will your heart be also." | 马太福音 6:21 | 心态/纪律提醒 |
| "Every flag is a trading range, and every trading range is a flag." | Al Brooks | 旗形与 TR 的时间框架相对性 |
| "A climax typically evolves into a trading range." | Al Brooks | 高潮后的标准演变 |
| "All PBs are Trading Ranges on smaller time frame... All Trading Ranges are PBs on higher time frames" | Al Brooks | 分形嵌套原理 |

## 提取出的新概念

**无全新独立概念。** 本合集是 Brooks 理论的实战应用记录，不引入新理论框架。以下观察值得注意：

1. **MC 10+2 评分**：一套非正式的微型通道质量评分法，可能对应 huangzongprice 量化系统中 signal-scoring 的前身或简化版
2. **速记系统**：高度压缩的 PA 注释法，可用于快速手写复盘
3. **ATM Straddle 参考**：将期权隐含波动率作为日内振幅预期的辅助参考

这些已在来源页中记录，不单独建概念页。

## 与已有知识的关系

| 已有概念 | 本文贡献 |
|---------|---------|
| [[h2-l2-state-machine|H2/L2 State Machine]] | 展示了 H1-H4 / L1-L4 在真实交易中的逐棒应用 |
| [[climax]] | 多次出现 "climactic reversal then TR" 模式，验证 Brooks "高潮→TR" 规律 |
| [[three-push-wedge|Three Push Wedge]] | 楔形底部后的 MTR 是高频模式 |
| [[major-trend-reversal|Major Trend Reversal]] | HL MTR / LH MTR 的实战识别 |
| [[tbtl]] | TBTL 被用作高潮后的反转确认信号 |
| [[trade-management-system]] | 展示了 STP/LMT/BE/Trailing 的实际使用 |
| [[fsm-market-cycle]] | 日型分类直接对应市场周期阶段 |
| [[trend-from-the-open]] | 多次出现开盘趋势日 |
| [[spike-and-channel]] | "trend then TR" 对应尖峰→通道演变 |

## 与现有知识的冲突

无冲突。本合集是 Brooks 理论的实战验证，所有观察与已有概念一致。

## 待办

- [ ] 如能恢复原始 PDF 中的手写图表标注（pdftotext 丢失），可提取更多视觉信息
- [ ] MC 10+2 评分是否在 huangzongprice 量化代码中实现？如找到源码可创建独立概念页
- [ ] 151 个交易日的 P&L 汇总统计（胜率、平均 R、最大回撤等）

## 文件清单（部分代表性条目）

| 日期 | 日型 | 时间框架 | Gemini |
|------|------|---------|--------|
| 2025-01-05 | - | 5min | ✓ |
| 2025-08-06 | - | 5min | - |
| 2025-09-25 | trend trading range all day | 5min | - |
| 2025-12-30 | - | 5min | ✓ |
| 2025-12-31 | - | 5min | ✓ |
| 2026-01-02 | - | 5min | ✓ |
| 2026-01-06 | - | 5min | ✓ (3版) |
| 2026-01-07 | - | 5min | ✓ |
| 2026-01-08 | - | 5min | - |
| 2026-01-09 | - | 5min | ✓ |
| 2026-01-12 | - | 5min | - |
| 2026-01-13 | - | 5min | ✓ |
| 2026-01-14 | - | 5min | ✓ |
| 2026-01-15 | - | 5min | - |
| 2026-01-16 | - | 5min | ✓ |
| 2026-01-20 | - | 5min | - |
| 2026-01-21 | - | 5min | ✓ |
| 2026-01-22 | - | 5min | ✓ |
| 2026-01-23 | - | 5min | ✓ |
| 2026-01-26 | - | 5min | ✓ |
| 2026-01-27 | - | 5min | ✓ |
| 2026-01-28 | - | 5min | - |
| 2026-01-29 | - | 5min | ✓ |
| 2026-01-30 | trend trading range all day | 1min+5min | ✓ |
| 2026-02-02 | - | 5min | ✓ |
| 2026-02-03 | - | 5min | ✓ |
| 2026-02-04 | - | 5min | ✓ |
| 2026-02-05 | - | 5min | ✓ |
| 2026-02-06 | - | 5min | ✓ |
| 2026-02-09 | - | 5min | - |
| 2026-02-10 | - | 5min | ✓ |
| 2026-02-11 | - | 5min | - |
| 2026-02-12 | - | 5min | ✓ |
| 2026-02-13 | - | 5min | - |
| 2026-02-17 | - | 5min | - |
| 2026-02-19 | trading range all day | 1min+5min | ✓ |
| 2026-02-23 | - | 5min | ✓ |
| 2026-02-24 | - | 5min | ✓ |
| 2026-02-25 | trading range then small pullback bull trend | 5min | ✓ |
| 2026-02-26 | - | 5min | ✓ |
| 2026-02-27 | trading range all day | 5min | - |
| 2026-03-02 | - | 5min | ✓ |
| 2026-03-03 | wedge bottom then HL MTR | 5min | ✓ |
| 2026-03-04 | climactic reversal then trading range | 5min | - |
| 2026-03-05 | bear trend from the open then HL MTR | 5min | - |

> 完整清单含 151 个条目，以上为代表性样本。日型概览仅列出 OCR 可辨识的条目。
