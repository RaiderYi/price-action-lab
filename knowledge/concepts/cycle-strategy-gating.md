---
title: "周期策略门控（Cycle Strategy Gating）"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry, scalp, failed-breakout]
tags: [allowlong, fsm, allowshort, fsmdir, breakout]
difficulty: intermediate
related: [fsm-market-cycle, fsm-strategy-constraints, background-permission, wedge-gravity-dual-core, playbook, trend-strength-filter, emergency-exit, article-huangzongprice-wedge-gravity-v2-master, article-wg-v15-analysis, breakout-mechanics]
char_count: 2164
---
# 周期策略门控（Cycle Strategy Gating）

## 一句话定义
FSM 市场周期状态机直接控制交易方向许可——突破仅顺势、通道顺势+边界高分逆势、震荡仅唐奇安边界反向入场的三级门控规则。

## 核心要点
- 门控通过 `allowLong` / `allowShort` 两个布尔变量实现，位于信号评分之后、最终信号输出之前
- 三个周期状态各有独立的许可规则，阈值精确到代码级：

### BREAKOUT / NEW_BREAKOUT（突破/新突破阶段）
- `allowLong = (fsmDir == 1)` —— 仅多头方向
- `allowShort = (fsmDir == -1)` —— 仅空头方向
- **零例外**：突破阶段绝对禁止逆势交易

### CHANNEL（通道阶段）
- **顺势全开**：`fsmDir==1` 时 `allowLong=true`，`fsmDir==-1` 时 `allowShort=true`
- **逆势高门槛**：
  - 空头通道做多：需 `nearChanB`（close 距 pl0 ≤ 1.5×ATR14）且 `lFin ≥ i_sigThr + 0.15`
  - 多头通道做空：需 `nearChanT`（close 距 ph0 ≤ 1.5×ATR14）且 `sFin ≥ i_sigThr + 0.15`
- 逆势阈值比默认高 0.15——通道内逆势剥头皮需更强信号支撑

### TRADING_RANGE（震荡区间）
- `allowLong = nearDonchL`（close 距唐奇安下轨 ≤ 0.5×ATR14）
- `allowShort = nearDonchH`（close 距唐奇安上轨 ≤ 0.5×ATR14）
- **仅边界反向**：震荡区间中部不产生任何方向信号（假突破防御的核心机制）

## 与相关概念的关系
- [[fsm-market-cycle]]：门控是 FSM 的直接下游消费者——FSM 提供 `fsm` 状态和 `fsmDir` 方向，门控据此产出 allowLong/allowShort
- [[fsm-strategy-constraints]]：同一机制的姐妹页——从四状态许可矩阵+边界判断条件角度描述相同规则
- [[background-permission]]：v2 执行引擎的 6 状态背景许可门控是周期策略门控的升级版——从 2 个许可扩展为 6 个（通用/顺势/反转 × 多/空），增加了 bgVeto/bgConflict/linkOk 等额外维度
- [[wedge-gravity-dual-core]]：周期策略门控是双核架构中「硬规则核」的最终落地——FSM 决定能做哪个方向，与软评分核（信号好不好）完全解耦
- [[playbook]]：v3 的 Playbook 玩法分类继承了周期门控的思想，将 3 种周期许可升级为 5 种玩法状态分发（禁逆势→区间反转→过渡反转→突破延续→回调再入）
- [[trend-strength-filter]]：趋势强度过滤是周期门控的补充——门控决定「能不能做这个方向」，趋势过滤决定「这个方向的趋势有多强」
- [[emergency-exit]]：紧急逃生与周期门控并联——emergExit 不改变 allowLong/allowShort，但通过失败过滤 (`i_useFailFilter`) 和 Brooks Step4 否决 (`vetoEmergL/S`) 间接屏蔽信号

## 实战应用
在信息面板上检查「多头策略许可」和「空头策略许可」行——若显示「✗ 当前周期屏蔽」，即使信号评分满分也不会触发入场。调试时若信号不出现，按以下顺序排查：FSM状态 → allowLong/Short → 信号评分 → 失败过滤 → Brooks否决。

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码第740-774行——`allowLong/allowShort` 的完整 if-else 逻辑树，含精确距离阈值和逆势附加分）
- [[article-wg-v15-analysis]]（V1.5 中间接提及但未给出精确规则）
- [[background-permission]]（v2 执行引擎升级为 6 状态门控）

## 矛盾与待验证
- V2 Master 中 `fsm=0` (BREAKOUT) 是死分支（无代码设为此值），因此 `fsmBreakoutNow` 实际仅覆盖 `fsm=3` (NEW_BREAKOUT)——该分支的 allowLong/allowShort 规则在实战中是否充分覆盖「突破后立即回调」场景，需对照 Brooks 原著中的「突破失败」概念（如 [[breakout-mechanics]]）验证
- 震荡区间的「仅唐奇安边界反向」规则隐含假设：区间中部突破大概率是假突破。此假设的统计正确率未在源码中标注，不同品种/周期的假突破率差异可能影响规则有效性
