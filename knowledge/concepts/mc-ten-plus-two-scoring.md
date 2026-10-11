---
title: "MC10+2 交易评分系统"
phase: [trend, range, breakout]
signal_types: [h2-entry, l2-entry, swing]
tags: [leg, swing, point, huangzongprice, doji]
difficulty: intermediate
related: [signal-scoring-synthesis, execution-scoring, rs-scoring, trade-management-system, huangzongprice-mes-reviews]
char_count: 2063
---
# MC10+2 交易评分系统

## 一句话定义
huangzongprice 的 12 维度交易后复盘评分体系——逐项为每笔已成交交易打分，正分加分、负分扣分，合成综合质量评估。

## 核心要点
- 全称：Market Context 10+2（可能为"10 个市场背景维度 + 2 个附加维度"）
- 用途：**交易后复盘**（非入场前信号筛选），对已完成交易的质量做结构化审计
- 评分方向：负分（-5%、-10%）= 减分项（该维度不满足交易标准）；正分（+5%）= 加分项（该维度表现优异）
- 对比：与 [[signal-scoring-synthesis]]（入场前评分）和 [[execution-scoring]]（执行决策评分）分属不同阶段
- 来源：仅见于 huangzongprice 的 MES 每日复盘，未见独立的系统文档

## 12 维度明细（基于复盘文件中的实际出现频率整理）

### 减分项（常见 -5% ~ -20%）
| 维度 | 缩写 | 典型扣分 | 含义 |
|------|------|---------|------|
| K 线质量 | `K` | -5% | 信号棒 K 线形态是否理想（doji、小实体等） |
| 与前收盘关系 | `Cprior L/H` | -5% | 当前价格相对于前收盘的位置 |
| doji 出现 | `doji` | -5% | 是否出现十字星（方向不确定） |
| 无 tick gap | `no tick gap` | -5% | 缺少跳空缺口（趋势动量不足） |
| 突破市场体制 | `BO mrk regime` | -10% | 当前处于突破模式（高失败率环境） |
| 滞后期/腿 | `late leg` | -10% ~ -20% | 入场在趋势腿的晚期（剩余空间有限） |
| TR 环境 | `TR` | -20% | 处于交易区间而非趋势（逆势风险大） |

### 加分项（常见 +5%）
| 维度 | 缩写 | 典型加分 | 含义 |
|------|------|---------|------|
| 价格控制 | `price control` | +5% | 价格在关键 swing point 附近受控 |
| 时间控制 | `time control` | +5% | 腿的时间长度达到预期 |
| swing point 确认 | `swing point 1ABR` | +5% | swing point 距入场在 1 倍 ABR 内 |

### 其他观察到的维度
- `ABR` — Average Bar Range 相关
- `leg2` — 第二腿确认（如 `leg2 55%~65%`）
- `H1/H2/L1/L2` — 信号层级（二次信号优于一次信号）

## 与相关概念的关系

- [[signal-scoring-synthesis]]：lFin/sFin 五因子合成体系——这是**入场前**信号筛选评分，MC10+2 是**交易后**复盘评分。两者的维度完全不重叠（lFin/sFin 侧重结构/形态/引力，MC10+2 侧重 K 线位置/市场体制/时机成熟度）
- [[execution-scoring]]：v3 三因子加权评分（bg×0.55+struct×0.25+sig×0.20）——这是**执行决策时**的评分。MC10+2 的维度更接近 bg（背景）层的拆分，但粒度细得多（12 维 vs 3 维）
- [[rs-scoring]]：0-100 综合评分，默认阈值 70%——RS 评分的内部维度未公开，但 MC10+2 提供了可见的维度清单
- [[trade-management-system]]：MC10+2 评分直接服务于复盘中的交易管理评估（止损位置、BE 时机、追踪执行）

## 实战应用
在每笔交易结束后，逐项对照 12 维度打分——不用于决定是否入场，而是用于识别自己的高频失误模式（例如：是否总在 `late leg` 入场？是否在 `BO mrk regime` 期间频繁交易？）

## 来源支撑
- [[huangzongprice-mes-reviews]] — 约 100 份 MES 每日复盘，每份至少含 1~3 组 MC10+2 评分卡

## 矛盾与待验证
- **12 维度的完整清单和精确权重未公开**：以上维度清单是从 OCR 碎片中拼凑的，可能有遗漏。与 lFin/sFin 和 v3 三因子评分的确切关系需要 huangzongprice 本人确认
- **"10+2" 的"10"和"2"具体指什么不确定**：可能 10 个背景维度 + 2 个信号质量维度，也可能 10 个基础维度 + 2 个加分维度
- **评分计算方式未知**：各维度如何汇总为最终分数（简单求和？加权？阈值判定？）
