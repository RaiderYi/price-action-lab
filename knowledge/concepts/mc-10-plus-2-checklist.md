---
title: "MC 10+2 实战评分清单"
phase: [trend, range, breakout, transition]
signal_types: [l2-entry, swing]
tags: [control, brooks, doji, 清单, 入场]
difficulty: intermediate
related: [brooks-signal-catalog, signal-scoring-synthesis, ctx-scoring, trader-equation, tbtl, eighty-percent-rule, execution-scoring, replay-journal-mes-huangzongprice-2025-2026]
char_count: 2163
---
# MC 10+2 实战评分清单

## 一句话定义

huangzongprice 从 Al Brooks 交易体系中提炼的 10 项扣分 + 2 项加分 = 综合胜率估算的实盘评分系统。

## 核心要点

### 评分结构

MC 10+2 包含三个部分：

**10 项基础检查（扣分项，每项 -5% 至 -20%）**

| # | 检查项 | 通常扣分 | 含义 |
|---|--------|---------|------|
| 1 | K 线质量 | -5% | 信号棒是趋势棒还是 doji/十字星 |
| 2 | C prior H | -5% | 收盘相对于前高关系（上方=趋势延续信号弱） |
| 3 | C prior L | -5% | 收盘相对于前低关系 |
| 4 | H prior H | -5% | 高点相对于前高（未创新高=动能减弱） |
| 5 | doji | -5% | 信号棒是否为 doji（doji=不确定性） |
| 6 | 无 tick gap | -5% | 信号棒与前棒之间有/无 tick gap |
| 7 | BO / mrk regime | -10% | 突破状态与市场周期阶段不匹配 |
| 8 | late leg | -10% | 是否为趋势晚期腿（Late Leg） |
| 9 | price control | +5% | 价格控制——关键 swing point 是否在有利位置 |
| 10 | time control | +5% | 时间控制——调整时间是否充分（TBTL ≥10 棒两腿） |

**2 项加分项（+5% 各）**

- **+5% price control**：价格在关键 major swing point 或 support/resistance 位置，1 ABR 范围内
- **+5% time control**：调整时间充分（≥10 棒含 2 腿），符合 TBTL 标准

**综合得分 = Base(100%) + Σ扣分 + Σ加分 = 预估胜率**

### 判断阈值

- **≥60%**：可交易（满足 Brooks 60% 概率最低要求 + Trader's Equation）
- **50%-59%**：边界区域，需额外确认（等二次信号/更高时间框架验证）
- **<50%**：不可交易（概率不支撑正期望值）

### 实战使用

MC 10+2 并非自动交易系统的硬编码公式，而是：
1. **盘后检查清单**：用于复盘时评估已做交易的架构质量
2. **实盘快速筛查**：在关键架构出现时快速心算是否值得入场
3. **学习工具**：通过反复使用内化 Brooks 的多维度评估思维方式

## 与相关概念的关系

- [[brooks-signal-catalog]]：MC 10+2 是「信号质量评分」，不定义信号类型，而在所有 16 种信号上叠加使用
- [[signal-scoring-synthesis]]：WG V1.5 的 lFin/sFin 五因子合成是自动化版本，MC 10+2 是手工实战版——核心维度重叠（棒型/背景/结构）但权重和具体阈值不同
- [[ctx-scoring]]：Brooks Context 4 Pine 的四步评分（ctx1/ctx2/ctx3/Step4）侧重「背景是否允许交易」，MC 10+2 侧重「当前这个具体架构好不好」
- [[trader-equation]]：MC 10+2 的 ≥60% 阈值直接来源于交易者方程式——胜率×回报 > 失败概率×风险
- [[tbtl]]：MC 10+2 的 "time control" 加分项直接引用 TBTL 原则
- [[eighty-percent-rule]]：MC 在区间/趋势环境下对 BO 权重调整（TR 中 BO 扣更多分）
- [[execution-scoring]]：V3 执行引擎的三因子加权（bg×0.55+struct×0.25+sig×0.20）与 MC 10+2 形成量化-手工对照

## 实战应用

在 MES 5-min 图表上：看到架构 → 暂停 → 逐项扫描 MC 10+2 清单 → 计算得分 → ≥60% 入场 / <60% 等待。日志中的典型应用：B1-B13 MC 10+2 65% → B26 L2 sell STP 入场。

## 来源支撑

- [[replay-journal-mes-huangzongprice-2025-2026]] — 96 个交易日复盘中反复使用

## 矛盾与待验证

- MC 10+2 各分项的具体百分比权重在日志中未完整列出（部分条目因 PDF 乱码不可读），以上权重为从可读条目中推断的常见值
- 与 [[signal-scoring-synthesis]]（lFin/sFin 五因子）的精确差异需要逐项对照——两者共享部分维度但组织逻辑不同，一致性待交叉验证
- 在不同市场类型（趋势 vs TR vs 反转日）中 MC 10+2 的各分项权重是否应动态调整，日志中未明确说明
