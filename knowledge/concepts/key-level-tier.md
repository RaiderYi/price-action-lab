---
title: "关键位分层体系"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry, reversal-entry, scalp]
tags: [tier, atr, neart, posscore, gravok]
difficulty: intermediate
related: [support-resistance, signal-scoring-synthesis, brooks-four-step-context, gravity-field, fsm-strategy-constraints, article-20260519-wedge-gravity-brooks-v1-pine, trend-reversal-separation, article-wg-v2-master]
char_count: 2895
---
# 关键位分层体系

## 一句话定义
将价格附近的关键 S/R 位置分为 Tier-1（核心边界）和 Tier-2（次级参考）两层，按距离 ATR 归一化后决定位置评分和过滤决策。

## 核心要点
- **Tier-1（核心边界）**：最近高极点 ph0、最近低极点 pl0、唐奇安上轨 donchH、唐奇安下轨 donchL。判定标准：`|close - level| ≤ 1.0×ATR14`
- **Tier-2（次级参考）**：次近高极点 ph1、次近低极点 pl1、EMA20、50% 引力中线 fib50。判定标准：`|close - level| ≤ 0.8×ATR14`
- **位置评分**：`posScore = clamp01(nearT1 ? 1.0 : nearT2 ? 0.6 : 0.0 + (gravOK ? 0.25 : 0.0))`——Tier-1 满分、Tier-2 六折、无关键位为零，引力场额外加分
- **关键位过滤**：`i_useKeyFilter = true` 时，`keyOK = gravOK or nearT1 or nearT2`——至少满足三者之一才允许信号输出
- **在趋势/反转信号中的不同权重**：反转信号 `revExtra = posScore×0.60 + momScore×0.40`（位置主导），趋势信号 `trendExtra = momScore×0.70 + posScore×0.30`（动量主导）
- **与 Brooks Step1 的关系**：Step1 的 `minKeyAtr` 取所有关键位（含 Tier-1/2）的最小 ATR 距离，统一量化为 ctx1_score——分层粒度比 Step1 更细
- **默认关闭**：`i_useKeyFilter = false`，关键位分层仅在开启后才作为信号过滤条件

## 与相关概念的关系
- [[support-resistance|Support/Resistance]]：分层体系是 S/R 概念的操作化——将「所有 S/R 都重要」细化为「越近越重要」
- [[signal-scoring-synthesis]]：`posScore` 通过 `extraBonusL/S` 以 0.10 系数注入最终信号评分
- [[brooks-four-step-context]]：Step1 的 `ctx1_score` 和分层体系的 `posScore` 是对同一组关键位的两种量化角度——Step1 是连续衰减，分层是离散二值
- [[gravity-field]]：引力场 OK (`gravOK`) 在分层体系中享有特权——即使不靠近任何具体关键位，引力场触发即可通过 `keyOK` 过滤
- [[fsm-strategy-constraints]]：TR 中的方向许可用唐奇安边界（Tier-1 级别），通道中的逆势剥头皮用极点距离（`|close-ph0/pl0| < 1.5×ATR14`，超出 Tier-1 范围）

## 实战应用
在信号标签中观察 `posScore`（位置因子）——nearT1 + gravOK = 满分 1.0 的位置支持；如果 nearT2 但 gravOK 未触发 = 仅 0.60 位置分，信号底气不足。

## 来源支撑
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — Pine Script 源码，第 620–627 行定义 Tier-1/Tier-2 判定，第 658、668–671 行定义位置评分和趋势/反转权重分配

## 矛盾与待验证
- **T1=1.0×ATR14 和 T2=0.8×ATR14 的阈值**：Tier-2 的距离阈值反而比 Tier-1 更严格——次级位置需要更贴近才算「靠近」。这在概念上合理（次级 S/R 弱，需要更精确的触及才有意义），但未经回测验证
- **仅两层是否足够**：Brooks 原著中 S/R 有 16+ 种类型，两层体系合并了磁力位、均线、极点等多种不同性质的 S/R——可能丢失了 S/R 类型之间的质量差异


---

## Merged Content (from key-level-tiering)

# 关键位分层过滤

## 一句话定义
将关键价位按重要性分为 Tier-1 和 Tier-2 两级，当前价格靠近 T1 或 T2 时信号更可靠——T1 距离容忍度 = ATR14×1.0（默认），T2 = ATR14×0.8（默认）。

## 核心要点
- **Tier-1（一级关键位）**：ph0（最近摆动高点）/ pl0（最近摆动低点）/ 唐奇安上轨 / 唐奇安下轨 —— 当前市场结构的"硬边界"
- **Tier-2（二级关键位）**：ph1（前一摆动高点）/ pl1（前一摆动低点）/ EMA20 / 50%回撤位（fib50）—— 辅助参考位
- **过滤逻辑**：`keyOK = (not i_useKeyFilter) or gravOK or nearT1 or nearT2`
  - 即：关闭过滤时全部放行；开启时至少满足引力触发或靠近 T1 或靠近 T2 之一
- **T1/T2 距离判定**：`math.abs(close - keyLevel) <= tierMul × ATR14`
- **位置评分加成**：`posScore = nearT1 ? 1.0 : nearT2 ? 0.6 : 0.0 + gravOK ? 0.25 : 0.0`

## 与相关概念的关系
- [[support-resistance|Support/Resistance]]：Tier-1/Tier-2 是对 Brooks 16+ 种 S/R 类型中「最重要 vs 次要」的量化分层
- [[gravity-field]]：引力场（gravOK）可替代关键位过滤——即使不在 T1/T2 附近，只要引力得分足够高也算「在值得交易的位置」
- [[trend-reversal-separation]]：反转信号的 posScore 权重更高（60%），因此关键位过滤对反转信号的影响更大

## 实战应用
开启关键位过滤后，远离所有关键位的信号将被屏蔽——相当于强制"不在关键位不入场"的纪律。T1/T2 的 ATR 倍数可根据品种波动率调整：高波动品种（如 BTC）可放宽到 1.5×/1.2×，低波动品种（如 A 股大盘）可收紧到 0.7×/0.5×。

## 来源支撑
- [[article-wg-v2-master]]

## 矛盾与待验证
- A 股分析系统的 RS 评分中是否也有类似的关键位分层？还是全部关键位等权重？
- T1/T2 列表是否完整——Brooks 原著的整数关口、缺口、前日高/低是否应纳入？
