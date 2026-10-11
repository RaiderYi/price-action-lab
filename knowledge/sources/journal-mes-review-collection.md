# MES 每日复盘合集（2026.01-03）

## 元信息
- 作者：huangzongprice（交易者/记录者），Gemini（AI 辅助注释，部分文件）
- 日期：2026.01.07 – 2026.03.05（约 40+ 个交易日）
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`（含纯手写版 + Gemini AI 标注版）
- 提取方式：pdftotext（PDF → 文本）
- 状态：⚠️ 部分 OCR 乱码（图表标注丢失、中文零星乱码），但交易信号、评分、入场/出场记录大部分可解析

## 一句话摘要
huangzongprice 的 MES 5min 日内价格行为实战交易日志合集，展示了 Brooks PA 理论在实盘中的完整落地流程。

## 文件清单（代表性样本）

| 文件 | 标题（市场结构概括） | 含 Gemini |
|------|-------------------|----------|
| MES20260305复盘 | bear trend from the open then HL MTR | — |
| MES20260304复盘 | climactic reversal then trading range | — |
| MES20260303复盘+gemini | wedge bottom then HL MTR | ✓ |
| MES20260226复盘+gemini | sell climax from the open then HL MTR | ✓ |
| MES20260211复盘 | bear trend from the open then trading range | — |
| MES20260210复盘+gemini | ... | ✓ |
| MES20260209复盘 | ... | — |
| MES20260206复盘+gemini | ... | ✓ |
| MES20260205复盘+gemini | ... | ✓ |
| MES20260204复盘+gemini | ... | ✓ |
| MES20260203复盘+gemini | ... | ✓ |
| MES20260202复盘+gemini | ... | ✓ |
| MES20260130复盘+gemini | ... | ✓ |
| MES20260129复盘+gemini | ... | ✓ |
| MES20260128复盘 | ... | — |
| MES20260127复盘-gemini | ... | ✓ |
| MES20260126复盘+gemini | ... | ✓ |
| MES20260123复盘 | ... | — |
| MES20260123 gemini | ... | ✓ |
| MES20260122复盘 | ... | — |
| MES20260122 gemini | ... | ✓ |
| MES20260121复盘 | ... | — |
| MES20260121 gemini | ... | ✓ |
| MES20260120复盘 | ... | — |
| MES20260116复盘 | ... | — |
| MES20260116 gemini | ... | ✓ |
| MES20260115复盘 | ... | — |
| MES20260114复盘 | ... | — |
| MES20260114 gemini | ... | ✓ |
| MES20260113复盘 | ... | — |
| MES20260113 gemini | ... | ✓ |
| MES20260112复盘 | ... | — |
| MES20260109复盘 gemini | ... | ✓ |
| MES20260108复盘 | ... | — |
| MES20260107复盘 | ... | — |
| MES20260107复盘 gemini | ... | ✓ |

（共约 40+ 个文件，覆盖 2026年1月-3月的交易日）

## 核心论点

### 1. 复盘标准化流程

每份复盘遵循统一的结构：

```
① 市场结构一句话 → ② 多时间框架（45min TR / 5min 信号）→ ③ ATM Straddle 背景
→ ④ MC 评分（微通道逐棒打分）→ ⑤ 关键交易记录（信号/入场/出场/时长/盈亏）
→ ⑥ Gemini AI 深度注解（+gemini版独有）
```

### 2. MC 微通道评分系统（MC Scoring）

这是复盘中**最核心**的量化分析方法——将每段微通道分解为逐棒打分：

```
B4-B12 MC10+2  -5%K, -5%Cprior L, -5% doji, -10% BO mark regime
                climactic reversal TR +5% price control, +5% time control
                Leg2 65%, L1
```

**评分因子权重表**（从多份复盘中汇总）：

| 因子 | 权重 | 说明 |
|------|------|------|
| K棒形态不良 | -5% | 非趋势棒形态 |
| 前收盘价位置不利 | -5% | close vs prior close |
| Doji/十字星 | -5% ~ -20% | 根据doji严重程度 |
| 无tick gap | -5% | 无跳空缺口 |
| BO标记/Regime不利 | -10% | 突破标记与当前方向不符 |
| Late Leg（延迟腿） | -20% | 已经走了太多腿 |
| 价格控制 (Price Control) | +5% | swing point 1ABR范围内 |
| 时间控制 (Time Control) | +5% | 走势持续时长达标 |
| MC=Climax（高潮）=TR | 定性标签 | 微通道本身构成高潮→预期反转 |

### 3. 多R分批止盈协议（Multi-R Scaling）

所有复盘统一使用多R目标管理：

```
1R → 2R → 3R → 4R
"1/3 2R" = 在2R减仓1/3，余仓跟踪止损
```

模式：**部分止盈 + 余仓跟踪**，允许单笔交易覆盖多个目标位（最高观察到4R）。

### 4. 信号到交易的完整链路

以 MES20260303+gemini 为例：

```
B23 H1 buy STP → AIL → B25 → B28 BTC leg2 → B34 buy STP leg2 → B37 leg2
         ↑                  ↑                ↑
    OB反转入场          BTC失望离场       Leg2二次入场
```

每条记录包含：**信号类型 → 入场方式(STP/LMT) → 持仓管理(AIL/BE/部分止盈) → 离场(目标/Signal反转)**。

### 5. Gemini AI 辅助复盘（+gemini 版专属）

标注有 "+gemini" 的文件包含 AI 生成的深度注释，示例：

```
B12 STC gemini:
  B12 L1 (The Climax Trap)
  B11 → B12 STC (Sell The Close) → Take Profit
  B11 B12 Doji / PA分析：
    1. Doji "L1" → STC止盈
    2. Climax → Doji "Exhaustion Pause" → STC
    L1/H1 Doji → L1/H1 Complex Pullback → L2/H2 → TR
```

Gemini 注释的特点：
- 识别陷阱结构（如 "The Climax Trap"、"The Execution Flaw"、"The Bull Surprise"）
- 引用 Brooks 规则（如 "Rule #5"、"Every flag is a trading range"）
- 多时间框架联动分析（5min vs 15min vs 45min）
- 标注心理陷阱（如 "Timing & Drawdown"）

### 6. 贯穿始终的哲学标签

每份复盘末尾都有：
```
Best Loser Wins ...... ...... ----by SC2
```
以及经文引用：
```
"For where your treasure is, there will your heart be also." — Matthew 6:21
```

这反映了 huangzongprice 的交易哲学：**接受亏损、专注于正确的过程而非结果**。

## 提取出的新概念

| 概念 | 说明 |
|------|------|
| [[mc-scoring-framework]] | MC微通道逐棒评分系统（10-bar + 11项加权因子） |
| [[multi-r-scaling]] | 多R分批止盈协议（1R→4R，部分减仓+余仓跟踪） |
| [[gemini-pa-review]] | Gemini AI 辅助价格行为复盘方法论 |

## 与现有知识的衔接

MES 复盘合集与 Wiki 已有概念的关系：

- **理论层**：所有信号类型（L1/L2/H1/H2/STC/BTC/MTR/climax/wedge/TR/microchannel）均已在 [[brooks-signal-catalog]]、[[h2-l2-state-machine|H2/L2 State Machine]]、[[fsm-market-cycle]] 等概念中覆盖
- **量化层**：MC 评分系统与 [[ctx-scoring]]（上下文评分）和 [[signal-scoring-synthesis]]（信号评分合成）形成三层次评分互补——背景→微结构→信号
- **实践层**：多R分批止盈协议与 [[trade-management-system]]（6组件交易管理）的 SPB 组件对应，但提供了更具体的参数化操作规则
- **工具层**：Gemini AI 复盘法为 [[live-trading-monitor]] 的"人机协同"维度提供了具体工作流

## 与现有知识的冲突

无直接冲突。MC 评分系统是新的量化视角，与已有评分系统互补而非矛盾。

## 待办
- OCR 乱码导致部分 MC 评分的具体数值无法精确提取，建议日后对原始 PDF 做更好的 OCR
- Gemini 注释的 "Rule #1-#5" 具体引用需对照 Brooks 原著验证
- "Best Loser Wins --- by SC2" 中的 SC2 身份待确认
