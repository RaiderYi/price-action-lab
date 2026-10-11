# MES 每日复盘合集

## 元信息
- 作者：huangzongprice（部分含 Gemini AI 辅助分析）
- 日期：2025-10-28 ~ 2026-03-05（约 100 个交易日）
- 原始位置：`raw/books/huangzongprice/MES*.md`
- 格式：MES 5 Min K 线图标注式复盘，pdftotext 提取（OCR 有损）
- 包含版本：初版复盘 / `+gemini` AI 辅助版

## 一句话摘要
huangzongprice 约 5 个月的 MES (Micro E-mini S&P 500) 每日 Brooks 价格行为复盘训练记录，包含全套 Brooks 速记体系、PTM 跨期对照、MC 10+2 评分和 Gemini AI 辅助分析。

## 核心论点

### 1. 复盘方法论：四层结构

每个复盘文件包含四层信息：

| 层级 | 内容 | 示例 |
|------|------|------|
| **日型判断** | 一句话概括当日市场类型 | "bear trend from the open then HL MTR" |
| **Bar级标注** | B1-Bn 每根K线的信号判定 | B15 sell STP, B24 climax, B52 L2 bear flag |
| **上下文评分** | MC 10+2 维度量化评估 | "-5% K, -5% Cprior L, -5% doji, -10% BO" |
| **记忆索引** | PTM 跨日期模式对照 | PTM20250302, PTM20250518 |

### 2. Brooks 速记体系完整使用

复盘中的核心符号和缩写：

| 符号 | 含义 | Brooks 来源 |
|------|------|------------|
| **B1-Bn** | 当日第n根K线编号 | — |
| **STP** | Sell The Close (卖出入场) | — |
| **STC** | Sell To Open (卖出开仓) | — |
| **L1/L2/H1/H2** | 第1/2腿回调买入卖出点 | Brooks Trading Course |
| **AIL/AIS** | Always In Long / Always In Short | Brooks 核心概念 |
| **MC** | Micro Channel（微通道） | Brooks 趋势篇 |
| **TTR** | Tight Trading Range（紧交易区间） | Brooks 区间篇 |
| **cxbar** | Climax Bar（高潮棒） | Brooks 反转篇 |
| **TBTL** | Ten Bars Two Legs（十棒两腿） | Brooks 区间篇 |
| **SPB** | Small Pullback Bear/Bull trend | Brooks 趋势篇 |
| **MTR** | Major Trend Reversal | Brooks 反转篇 |
| **EMA** | 20周期指数均线参考 | Brooks 基础 |

### 3. MC 10+2 评分体系

每个架构的评估使用 12 项因子：

| # | 因子 | 评分方向 |
|---|------|---------|
| 1 | K线形态 | -5%（doji/弱势）+5%（强趋势棒） |
| 2 | 收盘在棒线位置 | -5% Cprior L/H |
| 3 | 重叠度 | -5%-5% |
| 4 | Doji 判定 | -5% doji |
| 5 | Tick gap | -5% no tick gap / +5% good gap |
| 6 | 突破/市场阶段 | -10% BO mrk regime, -20% late leg |
| 7 | 价格控制 | +5% price control |
| 8 | 主要摆动点 | +5% major swing point |
| 9 | ABR 参照 | +5% 1ABR |
| 10 | 时间控制 | +5% time control |
| 11 | 腿2比例 | +5% leg2 65-75% |
| 12 | 盈亏比 | 目标 R 倍数标注 |

**典型评分示例**（MES20260305 复盘）：
```
B7-B9 MC 10+2:
-5% K, -5% Cprior L, -5%-5% Hprior H, -5% doji, -5% no tick gap,
-10% BO mrk regime, -10% late leg,
+5% price control swing point, +5% 1ABR, +5% time control, leg2 55%
→ 总计约 -30%（弱势架构）
```

### 4. PTM (Prior Trading Memory) 跨期对照

huangzongprice 的核心训练方法——遇到当前形态时，主动回忆历史上相似形态：

- `PTM20250302` — 参考 2025-03-02 的类似模式
- `PTM20250525` — SPB 开盘趋势持续全天的历史实例
- `PTM20250216` — Brooks 关于速度/动量的物理类比
- `PTM20241222` — 结构完成后的 HTF 上下文切换
- `PTM20250112` — Failed Wedge 的测量走势教训
- `PTM20250126` — 高潮反转后的交易区间演变

**PTM 的价值**：将离散的每日复盘连接成持续的学习曲线，实现 Brooks 所说的 "screen time" 积累。

### 5. Gemini AI 辅助分析

部分复盘带有 `+gemini` 后缀，包含 AI 对特定架构的深度解读：

| Gemini 分析特点 | 示例（MES20260212） |
|---------------|-------------------|
| **高潮识别** | "K range > ABR × 1.3~1.5 → Exhaustion → Sell Climax" |
| **陷阱过滤** | "The best looking bar late in a trend is usually a trap" |
| **K线进化判定** | "Surprise Bar → L1 不可靠 → 等 L2 确认" |
| **出场建议** | "Climax Bar = Exit Immediately" |

### 6. 覆盖的市场日型

从 100 天复盘中可归纳的日型分类：

- **趋势型**：bear trend from the open / bull trend resumption / SPB all day
- **反转型**：climactic reversal then TR / HL MTR / opening reversal
- **区间型**：trending trading range all day / tight trading range
- **混合型**：bear trend then HL MTR / sell climax from open then HL MTR

## 提取出的新概念

以下概念在已有 Wiki 中无对应页面，需新建：

1. [[prior-trading-memory]] — PTM 跨期交易记忆对照法
2. [[mc-scoring]] — MC 10+2 架构评分系统
3. [[mes-daily-review-workflow]] — MES 每日复盘工作流
4. [[gemini-assisted-review]] — Gemini AI 辅助交易复盘方法

## 与现有知识的关联

这些复盘是 Brooks 理论体系在 MES 实盘上的 **日常应用演练**，与以下已有概念直接关联：

- [[brooks-signal-catalog]] — 所有信号类型均在复盘中出现
- [[climax]] — 高潮识别是最常见的日型触发点
- [[major-trend-reversal|Major Trend Reversal]] — HL MTR 是出现频率最高的日型结尾
- [[trend-from-the-open]] — SPB/开盘趋势日频繁出现
- [[spike-and-channel]] — MC 评分直接使用尖峰+通道模型
- [[trading-range-quality]] — TTR 判定使用区间质量评估
- [[h2-l2-state-machine|H2/L2 State Machine]] — H1/H2/L1/L2 计数贯穿所有复盘
- [[ctx-scoring]] — MC 10+2 是独立于 ctx 评分系统的另一套评分
- [[protective-stops]] — 每笔入场标注止损位置和 R 倍数
- [[brooks-four-step-context]] — 日型判断 = 四步上下文的第一步

## 与现有知识的冲突

无冲突。MC 10+2 评分系统与 [[ctx-scoring]] 是 **不同层级的评分**：
- **ctx-scoring**：宏观背景评分（市场阶段/动能/否决）
- **MC 10+2**：微观架构评分（单笔交易的K线质量/位置/结构）

两者互补，MC 10+2 可视为 ctx 通过后的"入场确认层"。

## 文件清单（代表性样本）

| 日期 | 日型 | 版本 |
|------|------|------|
| 2025-10-28 | MES 复盘初版 | 初版 |
| 2025-11-03 ~ 2025-12-31 | 每日复盘 | 初版/+gemini 双版 |
| 2026-01-02 ~ 2026-01-30 | 每日复盘 | 初版/+gemini 双版 |
| 2026-02-02 ~ 2026-03-05 | 每日复盘 | 初版/+gemini 双版 |
| 2025-09-25 | 早期复盘（含物理速度类比注释） | 单版 |

完整清单见 `raw/books/huangzongprice/` 目录，共约 100 个文件。
