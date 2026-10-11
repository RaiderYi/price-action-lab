---
title: "双核架构 → 三层引擎（Wedge-Gravity → V2 Master → Context Engine v3）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry]
tags: [fsm, 双核架构, engine, 两层分离, 执行引擎]
difficulty: intermediate
related: [trend-maturity, exhaustion-risk, fsm-market-cycle, cycle-strategy-gating, signal-scoring-synthesis, signal-grading-system, brooks-signal-catalog, h2-l2-state-machine, indicator-visual-optimization, playbook-engine, playbook, three-push-wedge, article-20260520-wedge-gravity-brooks-context-v3, article-wg-v15-analysis, article-huangzongprice-wedge-gravity-v2-master, article-20250519-brooks-pa-execution-engine-v1, article-background-v3-upgrade, article-huangzongprice-v3-phase1, article-20250519-brooks-context-4-pine, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked, article-huangzongprice-wedge-gravity-v5-cycle-structure, article-wedge-gravity-v14-source, article-huangzongprice-context-engine-v3-rebuild, fsm-strategy-constraints, article-huangzongprice-context-engine-v6, execution-engine-architecture]
char_count: 3982
---
# 双核架构 → 三层引擎（Wedge-Gravity → V2 Master → Context Engine v3）

## 一句话定义
四版本演进：V1.5 硬规则 FSM + 软评分五因子；V2 Master 新增 Brooks 四步背景层 + Path-A/B 双路突破 + 趋势/反转分离评分 + 周期策略门控 + ABC 信号分级 + 7 层信号可靠性管道；v1 单体执行引擎（内嵌背景+三因子评分）；v3 Context/Execution 两层分离（input.source 绑定）。

## 核心要点
- **核 A — 硬规则 FSM**（V1.5 / v3 共用）：根据市场周期给出方向许可，优先级最高，一票否决层
- **核 B — 软评分**（V1.5）：楔形/H2/L2 提供形态结构分，引力场提供位置环境分，K 线提供当根强弱分 → lFin/sFin
- **v3 升级**：双核进化为三层加权引擎：

### v1 执行引擎：单体内嵌背景（中间态）
- **架构**：单文件自包含，精简背景层（位置/FSM/动量）直接内嵌在同一指标中
- **背景评分**：`bgScore = locScore×0.40 + phaseScore×0.35 + momScore×0.25`
- **动量评分**（v1 独有）：`momScore = impulseHealth + trendHealth - trendMaturity - exhaustRisk`
- **执行评分**：`execScore = bgScore×0.55 + structScore×0.25 + sigBarScore×0.20`
- **关键新增**：趋势成熟度（[[trend-maturity]]）和衰竭风险（[[exhaustion-risk]]）——在 V1.5 和 v3 中均不存在
- **背景许可过滤**：三层过滤（硬否决→软冲突→净许可），六种背景状态（否决/多强/多可/空强/空可/中性）
- **定位**：介于 V1.5（单指标双核五因子）和 v3（两层分离三因子）之间的过渡版本

### v3 升级：三层加权背景评分引擎
  - 位置层 (40%) — ATR归一化距离评分，替代 V1.5 引力场
  - 阶段层 (35%) — FSM + 5种过渡检测 + 阶段健康分类
  - 动能层 (25%) — 脉冲/健康/成熟度/衰竭/弱化五维评分
- **v3 新增配套**：趋势强度过滤（惩罚逆势）、三推回撤识别（替换 V1.5 楔形）、Playbook 玩法分类
- **v3 定位**：不再直接产出"能不能入场"——产出的是背景状态码(9级)、Playbook(5种)、各层分项分，供下游执行层（Phase-2）消费

## 与相关概念的关系
- [[fsm-market-cycle]]：双核架构中的硬规则层就是 FSM
- [[cycle-strategy-gating]]：V2 Master 硬规则核的精确落地——FSM 状态 → allowLong/allowShort 三级门控
- [[signal-scoring-synthesis]]：双核架构中的软评分层最终汇入 lFin/sFin
- [[signal-grading-system]]：V2 Master 软评分核的输出后处理——lFin/sFin → A/B/C 分级 + 可选等级过滤
- [[brooks-signal-catalog]]：双核架构是对 Brooks 信号体系的量化实现
- [[h2-l2-state-machine|H2/L2 State Machine]]：软评分层中形态结构分的来源之一
- [[indicator-visual-optimization]]：双核架构的最终输出按视觉分层体系渲染到图表
- [[playbook-engine]]：背景层 v3 的 Playbook Engine 是双核架构中硬规则层的升级方向——从 allowLong/Short 升级为 6 种玩法状态分发
- [[playbook]]：v3 新增的玩法分类，基于背景评分输出交易策略建议
- [[three-push-wedge|Three Push Wedge]]：v3 三推回撤识别替代 V1.5 楔形检测
- [[indicator-visual-optimization]]：v3 信息面板和背景色按视觉分层体系渲染

## 实战应用
在图表上，FSM 状态变更时标签会变色提示；当 FSM 方向与结构方向一致且分数达标时，信号可靠性最高。

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 完整 Pine Script 源码——双核→三层引擎的代码级实现，1139 行全部模块）
- [[article-wg-v15-analysis]]（V1.5 双核架构）
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master——Brooks 四步法完整集成、周期策略门控、ABC 分级、7 层可靠性管道）
- [[article-20250519-brooks-pa-execution-engine-v1]]（v1 执行引擎：单体内嵌背景，趋势成熟度+衰竭风险首次出现，三层背景许可过滤）
- [[article-background-v3-upgrade]]（Playbook Engine 是 WG 架构的升级方向）
- [[article-huangzongprice-v3-phase1]]（v3 三层引擎）
- [[article-20250519-brooks-context-4-pine]]（Brooks 四步上下文引擎是 WG 双核架构中「核B软评分」的 Brooks 理论源头）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 执行引擎两层分离的落地实现）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 执行引擎两层分离的落地实现——Context Engine + Execution Engine 通过 20+ API 绑定）
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]（V5.0 是 V1.5 的直接升级——保留双核结构但新增唐奇安通道周期引擎、结构综合信号系统、9 字段数据输出层）
- [[article-wedge-gravity-v14-source]]（V1.4 Pine Script 源码——双核架构的唯一可运行实现）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 1201行源码——三层引擎的纯净参考实现 + 防缩放渲染 + 动量健康四子评分）
- [[fsm-strategy-constraints]]：FSM 策略约束——硬规则核的代码落地：每周期状态→allowLong/allowShort

## V6 减法分支：回归纯背景

V6 PA背景分析引擎（[[article-huangzongprice-context-engine-v6]]，251行）是双核架构演进的「减法分支」：
- 砍掉楔形/FSM/H2L2/供需区/订单块/执行评分/警报——仅保留核心背景分析
- 用（无状态机）替代 FSM
- 用替代单维动能分
- 用统一所有否决条件
- V5(1520行)→V6(251行)：代码量减少 83%，证明背景分析的核心逻辑可高度浓缩

## 矛盾与待验证
- 脚本中 `BREAKOUT(0)` 状态在运行中通常不出现（无代码设 0），但 `allowLong` 等分支仍包含该状态，属于死分支或预留。纯 Brooks 理论中突破是核心周期，此处是量化实现的选择性简化。
- v3 执行引擎将该架构从「单指标内双核」演进为「两层分离」——Context Engine（背景引擎）+ Execution Engine（执行引擎）通过 Pine Script `input.source` API 绑定。详见 [[execution-engine-architecture]]。
- **V4.1 vs v3 时序**：V4.1 文档已包含完整的三层评分系统（40/35/25），而 wedge-gravity-dual-core 将三层评分归为 v3 升级。可能三层评分在 V4.1 就已实现，v3 是对其的进一步重构（增加过渡检测、趋势强度过滤等），而非首次引入。两版时序关系需对照源码确认。
- **V5.0 vs v3 架构差异**：V5.0 放弃 v3 的 Context/Execution 两层分离（`input.source` 跨指标绑定），回退为单指标自给自足——`getIndicatorData()` 返回全零，所有数据在指标 B 内部本地重算。同时新增供需区和订单块两个独立 S/R 可视化模块，结构分从四维度累加简化为固定值（楔形=0.70/H2=0.55），引力场从独立评分维度降为位置层辅助加成。
