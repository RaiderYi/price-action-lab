---
title: "背景玩法引擎（Playbook Engine）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, reversal-entry]
tags: [playbook, engine, 背景层, 极强趋势, fsm]
difficulty: intermediate
related: [playbook-states, trend-strength-filter, tri-push-background, fsm-market-cycle, wedge-gravity-dual-core, range-zone-positioning, article-background-v3-upgrade]
char_count: 1130
---
# 背景玩法引擎（Playbook Engine）

## 一句话定义
背景层 v3 的核心升级——将背景从"能不能做"的过滤器升级为"当前应优先寻找哪类信号"的交易机会分类器。

## 核心要点
- **定位升级**：v1/v2 是风险过滤器（veto/support/conflict），v3 变成**机会分发器**
- **核心输出**：不仅输出多强/空强/中性/否决，更输出 `playbookState`（0-5 枚举）和 `playbookText`
- **三层架构**：
  - 背景层：决定应看什么玩法（Playbook Engine）
  - 执行层：决定结构是否触发（入场确认）
  - 管理层：决定如何表达风险与目标（止损/目标/追踪）
- **优先级固定**：极强趋势拦截 → 区间 → 过渡 → 新突破 → 通道 → 等待

## 与相关概念的关系
- [[playbook-states]]：6 种玩法状态的详细定义与使用条件
- [[trend-strength-filter]]：极强趋势时触发 playbook=5 禁逆势
- [[tri-push-background]]：三推出现触发 playbook 从"顺势"切换至"过渡反转"
- [[fsm-market-cycle]]：FSM 的 `phaseState` 是 Playbook 判断的核心输入
- [[wedge-gravity-dual-core]]：Playbook Engine 是 WG 双核架构中硬规则层的升级
- [[range-zone-positioning]]：区间定位直接决定 playbook 是否进入"边缘反转"

## 实战应用
在图表上，Playbook Engine 告诉你**当前应该看什么**：
- 如果 playbook=5（强趋势禁逆势）→ 所有反转信号忽略，只看顺势 BTC/STC
- 如果 playbook=2（顺势回调再进入）→ 专注 H2/L2，过滤楔形反转
- 如果 playbook=4（过渡期反转）→ 专注楔形/三推衰竭，屏蔽突破追随

## 来源支撑
- [[article-background-v3-upgrade]]

## 矛盾与待验证
- 本文为**设计稿，尚未实现**。所有输出变量名和枚举值为设计建议。
- Playbook 与 FSM allowLong/allowShort 的关系：Playbook 是比 allow 更细粒度的"玩法分类"，两者是层叠关系还是替代关系，设计稿未最终定论。
- 6 种状态在实际运行中的互斥性有待验证——趋势突破延续和顺势回调再进入是否有重叠区间。
