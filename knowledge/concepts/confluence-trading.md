---
title: "共振交易（Confluence / 结构共振）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, reversal-entry]
tags: [楔形, 执行引擎, 共振, 显示, 共振信号]
difficulty: intermediate
related: [h2-l2-state-machine, three-push-wedge, background-permission, execution-scoring, signal-scoring-synthesis, article-huangzongprice-execution-engine-v2-linked]
char_count: 1475
---
# 共振交易（Confluence / 结构共振）

## 一句话定义
当两个或多个独立的 Brooks 价格行为结构在同一根 K 线上同时触发同方向信号时，两结构的评分各获 +0.10 加分——这是 v2 执行引擎独有的信号增强机制。

## 核心要点
- **v2 识别两种共振**：
  - **多头共振**：H2（顺势） + 下降楔形（反转）在同一 bar 同时形成 → `confluenceLong = true`
  - **空头共振**：L2（顺势） + 上升楔形（反转）在同一 bar 同时形成 → `confluenceShort = true`
- **加分机制**：共振触发时，H2/L2 结构分和楔形结构分各 +0.10（clamp 到 1.0）
- **信息面板显示**：面板最后一行「共振」显示「多共振」「空共振」或「-」
- **报警支持**：`confluenceLong` 和 `confluenceShort` 各有独立的 `alertcondition`
- **结构名称**：共振触发时，信号标签显示 `H2+楔形` / `L2+楔形`（而非单独的 H2/L2/楔形）

## 为什么共振有意义
- **H2/L2 是顺势结构**：依赖趋势方向（`allowTrend*`），本质是「趋势中的回调入场」
- **楔形是反转结构**：依赖反转条件（`allowReversal*`），本质是「趋势末端的反转入场」
- 两者在同 bar 同时触发意味着：**趋势方向的结构（H2/L2）和趋势衰竭的结构（楔形）达成一致**——这是 Brooks 理论中最高质量的交易情景之一

## 与相关概念的关系
- [[h2-l2-state-machine|H2/L2 State Machine]]：共振的多头来源
- [[three-push-wedge|Three Push Wedge]]：共振的空头/多头来源（上升楔形偏空，下降楔形偏多）
- [[background-permission]]：共振信号需同时通过顺势许可和反转许可——两个不同方向的门控同时开启
- [[execution-scoring]]：共振加分 +0.10 汇入结构分，最终提升执行分
- [[signal-scoring-synthesis]]：V1.5 的 lFin/sFin 评分中有「趋势反转加成」和「引力场加成」，可以视为广义共振——v2 的 H2+Wedge 是特定结构的精确共振

## 实战应用
共振信号是 v2 系统中质量最高的信号类型——它既满足趋势延续（H2/L2）又满足趋势衰竭反转（楔形），代表市场在关键转折点的双重确认。实际使用中可考虑：共振信号降低 `i_gradeMin` 门槛（如 B→C 级），或单独设置更宽的止损。

## 来源支撑
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 执行引擎源码第 335-342 行实现共振检测和加分）

## 矛盾与待验证
- v2 只检测「H2+楔形」和「L2+楔形」的共振。Brooks 原著中提及的其他共振形式（如 H2+支撑位、楔形+趋势线突破、多种 S/R 汇合）在 v2 实现中未被覆盖。
- v3 执行引擎是否保留共振机制待确认——v3 的简化架构可能移除了这一加分项。
- 共振加分 +0.10 的量级是否合理（相对于结构分本身 0.45-0.55 的范围）未经回测验证。
