---
title: "信号评分合成（lFin / sFin）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, reversal-entry]
tags: [lfin, sfin, ctxw, ctxscore, extrabonus]
difficulty: intermediate
related: [gravity-field, three-push-wedge, h2-l2-state-machine, signal-grading-system, cycle-strategy-gating, bar-close-position, wedge-gravity-dual-core, signal-reliability-pipeline, signal-scoring-synthesis, execution-scoring, confirmation-bar, article-20260520-wedge-gravity-brooks-context-v3, article-wg-v15-analysis, article-huangzongprice-wedge-gravity-v2-master, article-20260519-wedge-gravity-brooks-v1-pine, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked, article-20260519-wedge-gravity-v41-flowchart, article-20250519-brooks-context-4-pine, article-wedge-gravity-v14-source, article-huangzongprice-context-engine-v3-rebuild]
char_count: 3561
---
# 信号评分合成（lFin / sFin）

## 一句话定义
将环境分、K 线分、引力加成、结构分、趋势反转加成加权求和为 0-1 的最终分数，与阈值比较决定信号是否"够格"。

## 核心要点
- **K 线分 `lScore`/`sScore`**（0-1）：收盘靠近极值、实体 vs 5 均实体、下/上影占比
- **结构分 `structScoreL/S`**：楔形用对称/收口/跨度加权，纯 H2/L2 给固定 0.55
- **环境分**：`ctxScore` 由引力场提供，权重 `i_ctxW`
- **加成项**：`gravBonus`（引力）、`extraBonus`（趋势/反转，最多约 0.1）
- **合成公式**（截断在 1）：
  ```
  lFin = ctxScore * i_ctxW + lScore * (1 - i_ctxW) + gravBonus + structScoreL + extraBonusL
  ```
- **阈值**：`lThr`/`sThr` = `i_sigThr`，反转可选加价 `i_revAdd`
- **中点条件**：做多需 `close > midPt`，做空需 `close < midPt`（即使分数达标，收盘位置不对也不入）

## 与相关概念的关系
- [[gravity-field]]：提供 `ctxScore` 环境分
- [[three-push-wedge|Three Push Wedge]]：提供 `structScoreL/S` 的主要来源
- [[h2-l2-state-machine|H2/L2 State Machine]]：纯 H2/L2 给固定结构分 0.55
- [[signal-grading-system]]：lFin/sFin → A/B/C 分级 + 可选等级过滤——评分合成是分级的输入
- [[cycle-strategy-gating]]：信号评分达标后仍需通过周期策略门控（allowLong/allowShort）才能触发
- [[bar-close-position]]：`close > midPt` 即收盘在上半部
- [[wedge-gravity-dual-core]]：lFin/sFin 是双核中软评分核的最终输出
- [[signal-reliability-pipeline]]：lFin/sFin 达标后进入 G7 6 层过滤管道，最下游才输出最终信号
- [[signal-scoring-synthesis]]：执行层设计提出的替代方案——将 lFin 拆分为 bgScore×0.55 + structScore×0.25 + sigBarScore×0.20，再映射为 A/B/C 等级
- [[execution-scoring]]：v3 执行引擎正式落地的三因子公式（本页五因子公式的简化替代）+ ABC 等级系统
- [[confirmation-bar]]：v3 可选确认K线——在评分完成之后的最终入场关口

## 实战应用
调试时若发现没有信号，先看 `lFin` vs `lThr` 是否达标，再看 `close > midPt` 是否满足，最后看 `allowLong`（FSM 许可）。

## V1.5.2 增强（来自 Pine Script 源码，2026-05-19 验证）

以下机制在之前的分析文档中未明确描述，源码揭示了完整实现：

- **结构优先级**：楔形 > H2/L2。当同一方向同时触发楔形和 H2/L2 时，优先标记为 "WEDGE>H2" 或 "WEDGE>L2"（第 639-643 行）
- **趋势/反转分离**：`longIsTrend = fsmDir==1`, `longIsRev = fsmDir==-1`。趋势信号侧重动量（`momScore×0.70 + posScore×0.30`），反转信号侧重位置（`posScore×0.60 + momScore×0.40`）
- **extraBonus 注入**：`extraBonusL = (longIsRev ? revExtraL : longIsTrend ? trendExtraL : 0.0) × 0.10`——最多贡献 0.10 分（第 673-674 行）
- **信号分级 ABC**：lFin≥0.80→A, ≥0.60→B, else C，可选 `i_gradeMin` 过滤
- **结构质量分**：楔形 = 对称×0.40+收口×0.35+跨度×0.25；纯 H2/L2 = 固定 0.55

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：lFin = bg×0.55 + struct×0.25 + signal×0.20 精确权重 + ABC 分级 + 确认K线可选机制）
- [[article-wg-v15-analysis]]
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码第610-695行——lFin/sFin 完整合成公式，含趋势/反转分离的 extraBonus 计算、结构质量分 f_clamp01、位置因子 posScore）
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — **Pine Script 源码**，首次揭示 V1.5.2 新机制（结构优先级、趋势反转分离、extraBonus 公式、信号分级）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 用三因子加权公式 [[execution-scoring]] 完全替换了 lFin/sFin——两套公式对同一场景可能给出不同结论）
- [[article-20260519-wedge-gravity-v41-flowchart]]（V4.1 执行分三权重：bg×0.55 + struct×0.25 + sig×0.20；信号棒阈值 i_sigThr=0.40；背景阈值 i_bgThr=0.58）
- [[article-20250519-brooks-context-4-pine]]（ctx评分体系是 lFin/sFin 的互补过滤器：ctx评「能不能做」，信号评「信号多好」；两者通过 i_useBrooks4 可独立开关）
- [[article-wedge-gravity-v14-source]]（V1.4 源码第485-510行——lScore/sScore 评分细则 + lFin/sFin 合成公式 `ctxScore*i_ctxW + *Score*sigW + gravBonus`）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 源码第622-644行——执行分精确公式：lFin=bgScoreL×0.55+structureScoreL×0.25+signalBarScoreL×0.20，权重可配置；ABC等级 + gradeOK过滤；longCandidate 需 struct≥0.45+sigBar≥0.40+close>midPt）

## 矛盾与待验证
- 各分量的权重（`i_ctxW` 等）是可调参数，不同品种/周期的最优权重需要回测确定。当前权重是作者经验值，非系统性优化结果。
- v3 的三因子公式（bg×0.55+struct×0.25+sig×0.20）是否优于本页的 lFin/sFin 五因子公式（ctxScore×ctxW + K线分×(1-ctxW) + gravBonus + structScore + extraBonus）？尚无对比回测数据。v3 砍掉了引力加成和趋势反转加成，更简洁但可能丢失信息。
- **V4.1 已出现三因子公式**：本页记录的 lFin/sFin 五因子公式来自 V1.5，但 V4.1 文档中的执行分已采用 bg×0.55+struct×0.25+sig×0.20 三因子——说明该公式可能并非 v3 首次引入，而是在 V4.1 阶段就已替代了五因子。两套公式的版本时间线需对照源码确认。
