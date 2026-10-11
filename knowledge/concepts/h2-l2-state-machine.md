---
title: "H2/L2 状态机"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, flag]
tags: [bear, phase, bull, ema, 入场规则]
difficulty: intermediate
related: [three-push-wedge, signal-scoring-synthesis, fsm-market-cycle, wedge-gravity-dual-core, execution-layer, background-permission, confluence-trading, execution-scoring, execution-engine-architecture, article-20260520-wedge-gravity-brooks-context-v3, article-20200818-brooks-10-best-pa-patterns, article-wg-v15-analysis, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-execution-layer-v1, course-notes-8-11-chart-analysis, encyclopedia-al-10-best-setups, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked, article-huangzongprice-wedge-gravity-v5-cycle-structure, structure-composite-signal, article-wedge-gravity-v14-source, article-huangzongprice-pa-shape-audit]
char_count: 4783
---
# H2/L2 状态机

## 一句话定义
两套有限状态机追踪趋势结构——多头链从 Pivot Low 起步经 H1 到 H2，空头链对称地从 Pivot High 经 L1 到 L2，是纯 Brooks 量化的核心结构来源。

## 核心要点
- **两套独立状态机**：`bPh`（多头链）和 `sPh`（空头链），各自独立运行
- **孕线规则**：`insideBar` 不推进计数——盘整不破坏趋势结构
- **超时机制**：`i_timeout` 超时后状态机重置
- **多头链**：`isPL` 起步 → 破高得 H1 → 回撤后上破 H1 高 → **H2**
- **空头链**：`isPH` 起步 → 对称得 **L2**
- **输出**：布尔 `h2` / `l2`，作为做多/做空结构来源之一

## 与相关概念的关系
- [[three-push-wedge|Three Push Wedge]]：H2/L2 与楔形共同构成 `longStruct`/`shortStruct`
- [[signal-scoring-synthesis]]：纯 H2/L2 给固定 0.55 结构分（低于楔形加权分）
- [[fsm-market-cycle]]：H2/L2 在软评分层运作，FSM 在硬规则层运作，两者独立
- [[wedge-gravity-dual-core]]：H2/L2 是双核架构中软评分层的结构来源
- [[execution-layer]]：执行层设计中 H2/L2 是主打路线（模块 B），优先级高于楔形
- [[background-permission]]：H2 候选 = h2 AND allowTrendLong（顺势许可，非通用 allowLong）；v2 首次实现此门控
- [[confluence-trading]]：H2 + 下降楔形同时触发 = 多头共振，各结构分 +0.10
- [[signal-scoring-synthesis]]：H2/L2 结构分建议改为四维度加权（背景适配0.30+位置适配0.30+阶段适配0.20+清晰度0.20），区别于 WG V1.5 的固定 0.55
- [[execution-scoring]]：v3 执行引擎的 H2 结构分由 allowLong/allowTrend/bgScore/veto/conflict 五布尔项累加而成（非固定 0.55），详见 v3 三因子公式
- [[execution-engine-architecture]]：v3 中 H2/L2 在 Execution Engine 内独立重新实现，不再依赖 Context Engine 的结构数据

## 实战应用
H2 做多信号最可靠的情景：FSM 处于通道或突破状态，`h2=true`，K 线收盘在上半部，引力场环境分高。单有 H2 而无 FSM 许可，不会出信号。

### v1 执行引擎实现（4 阶段快速版）
- **Phase 0**：等 Pivot（做多等 `isPL`，做空等 `isPH`）
- **Phase 1**：等突破（上破前高→H1 / 下破前低→L1）
- **Phase 2**：等回调/扩展（更新极值或触发 Phase 3）
- **Phase 3**：等二次突破（破 Phase 2 极值→H2/L2 信号）
- **内含棒跳过**：`insideBar` 时不推进状态，但也不退出（与 V1.5 的"不推进计数"一致）
- **超时复位**：25 根 K 线（`i_timeoutH2L2`）未完成→全部状态清零
- **结构分**（v1 四维度）：背景适配 0.30 + 趋势适配 0.20 + 位置适配 0.20 + 非中性区 0.15 + 非目标区 0.15
- **v1 vs V1.5 vs v3**：v1 最快（4 阶段+超时），V1.5 最复杂（5 阶段），v3 最简（无内含棒跳过）

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：完整 H1/H2/L1/L2 状态机含 25 根超时保护 + 内包棒暂停规则）
- [[article-20200818-brooks-10-best-pa-patterns]]（架构 #4：H2/L2——市场制造混乱→两次反转失败→趋势恢复→逆势方退出+顺势加速的完整逻辑链；模式嵌套说明——小版本在大两级走势中形成）
- [[article-wg-v15-analysis]]（V1.5 的 `bPh`/`sPh` 双变量状态追踪）
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 的 4-phase FSM：Phase 0→1→2→3→0，含超时重置和趋势过滤）
- [[article-huangzongprice-execution-layer-v1]]
- [[course-notes-8-11-chart-analysis]]（Video 9B：双顶/双底 = H2/L2；H4/L4 连续反转；Video 9C：逆势交易者在 H2/L2 退出）
- [[encyclopedia-al-10-best-setups]]（架构 #4：H2/L2——H1/L1 定义、H2 入场规则、L2 入场规则）
- [[encyclopedia-al-10-best-setups]]（架构 #4：H2/L2——H1/L1 定义、H2 入场规则、L2 入场规则）
- [[encyclopedia-al-10-best-setups]]（架构 #4：H2/L2——H1/L1 定义、H2 入场规则、L2 入场规则）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 执行引擎中的简化 H2/L2 状态机——4 阶段、超时机制、孕线跳过、结构分四维度累加）
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]（V5.0 中 H2/L2 固定给 0.55 结构分，与楔形加权分（40/35/25）共同汇入 [[structure-composite-signal]]；信息面板显示当前 bPh/sPh 阶段）
- [[article-wedge-gravity-v14-source]]（V1.4 源码第390-482行——H1/H2/L1/L2 的完整 Pine Script 实现，含孕线免疫 `insideBar` + 超时重置 `i_timeout=25 bars`）

### Al Brooks 原文补充（来自 Al 10 架构）
- **H1 定义**：在强多头趋势里或区间强多头腿型里，如果第一根棒的高点**平齐或低于**前一根棒的高点，且被下一根棒触发该高点 → H1 牛旗
- **L1 定义**：在强空头趋势里或区间强空头腿型里，反抽低点**高于**前一根棒低点，且被下一根棒低点触发 → L1 熊旗
- **H2 入场**：在收线在自己高点附近的 H2 棒上方买入，成功率非常高
- **L2 入场**：如果 L2 带尾巴，找跟随棒不带尾巴的；在收线在自己低点附近的 bear bar 下方进场
- **H3 三角形**：三角形盘整往往是 H3 的买入机会
- **H2/L2 模糊性是市场本质**：市场存在的目的是制造不确定性，H2/L2 往往镶嵌在更大框架里。只要止损合理，有足够时间参与或调整

## 矛盾与待验证
- H2/L2 固定给 0.55 分，楔形用对称/收口/跨度的加权分（可能更高）。这意味着脚本对楔形的结构评分权重高于纯 H2/L2——是否符合 Brooks 原意（H2 是非常可靠的入场信号）可进一步讨论。
- 执行层设计稿提出 H2/L2 改用四维度加权评分（背景适配+位置适配+阶段适配+清晰度），若实施将改变 H2/L2 的结构分来源——需与旧 0.55 固定分对比回测。同时，H2 候选应使用 `allowTrendLong`（顺势许可）而非通用 `allowLong`——WG V1.5 代码中未做此拆分。
- v3 执行引擎的 H2/L2 状态机（4 阶段：PL/PH→破极值→回撤→再破出信号）与 V1.5 的 `bPh`/`sPh` 状态机实现方式不同。v3 版本更简洁，不含孕线规则和孕线穿透处理。两个版本的 H2/L2 信号可能不完全一致。
- **书本 vs 实现差异（L1/L2/H1/H2: 均为 major_diff）**： 发现这 4 种趋势回撤信号的 5/5 维度均与 Brooks 原著不一致。核心差异：① 趋势前提从 `bear_trend`/`bull_trend` 量化为 `ema_below_20_bear_bias`/`ema_above_20_bull_bias`；② L1/H1 的腿计数增加了 `low_break`/`high_break` 条件；③ L2/H2 允许在 TR 内但禁止在 TR 下半区/上半区操作——这是书本无对应的工程创新；④ 所有信号均增加了 `min_rs` 和 `regime_penalty` 额外过滤。具体的反弹/回调深度量化（0.3~5 ATR）和实体比例要求（≥0.10）均为纯实现层决策。

### 书-码差异（来源：[[article-huangzongprice-pa-shape-audit]]）
**bear_l1（L1 反弹做空，major_diff，12 samples）**：趋势前提 `bear_trend`→`ema_below_20_bear_bias`；腿计数 `first_pullback`→`first_pullback_low_break`；市场背景增加「非 TR 底部」约束；信号棒实体比例量化 `>=0.10`

**bear_l2（L2 反弹做空，major_diff，52 samples）**：趋势前提 `bear_trend`→`ema_below_20_bear_bias`；市场背景允许 TR 但「TR 下半区禁止做空」（书本未明确禁止）；增加了 `min_rs` + `regime_penalty` 过滤

**bull_h1（H1 回调做多，major_diff，8 samples）**：趋势前提 `bull_trend`→`ema_above_20_bull_bias`；腿计数 `first_pullback`→`first_pullback_high_break`；市场背景增加「非 TR 顶部」约束

**bull_h2（H2 回调做多，major_diff，20 samples）**：趋势前提 `bull_trend`→`ema_above_20_bull_bias`；市场背景「TR 上半区禁止做多」；增加了 `min_rs` + `regime_penalty`

**关键问题**：L1/L2/H1/H2 四个信号的书本趋势前提均为「趋势中」，但代码统一改为 EMA20 位置判断——在强 TR 中 EMA20 可能平走但书本仍认为可能存在趋势信号。此外，「TR 下半区禁止做空/上半区禁止做多」是代码独有的区域过滤，书本仅建议谨慎而非禁止。
