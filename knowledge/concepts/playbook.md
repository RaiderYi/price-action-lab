---
title: "Playbook（玩法分类）"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry, failed-breakout]
tags: [playbook, 过渡期反, 三推背景, 顺势回调, 玩法]
difficulty: intermediate
related: [trend-strength-filter, fsm-market-cycle, three-push-wedge, background-scoring-engine, article-huangzongprice-v3-phase1]
char_count: 1284
---
# Playbook（玩法分类）

## 一句话定义
根据市场背景（阶段、位置、趋势强度、三推背景）自动匹配 5 种交易玩法，按优先级从「禁止交易」到「顺势回调」逐级判定。

## 核心要点
- **状态编码**（按优先级降序）：
  | 状态码 | 玩法 | 触发条件 | 颜色 |
  |--------|------|---------|------|
  | 5 | 强趋势禁逆势 | trendBlock 牛或熊触发 | 红色 |
  | 3 | 区间边缘反转 | 震荡+非区间中部+靠近边界 | 橙色 |
  | 4 | 过渡期反转 | 过渡信号≥2 或 三推背景权重≥0.7 | 紫色 |
  | 1 | 趋势突破延续 | 新突破(phase=3)+目标位未到 | 绿色 |
  | 2 | 顺势回调再入 | 通道(phase=1)+趋势健康 | 青色 |
  | 0 | 等待 | 以上均不满足 | 灰色 |
- **判定顺序严格**：一旦命中高优先级条件即返回，不检查低优先级
- **图形着色**：K 线背景色随 Playbook 状态变化，快速识别当前适用玩法

## 与相关概念的关系
- [[trend-strength-filter]]：Playbook 状态 5 完全由趋势强度屏蔽标志驱动
- [[fsm-market-cycle]]：Playbook 状态 1/2/3 以 FSM 阶段状态为核心判断依据
- [[three-push-wedge|Three Push Wedge]]：三推背景权重≥0.7 时触发 Playbook 状态 4（过渡期反转）
- [[background-scoring-engine]]：背景否决(bgVeto)触发时 Playbook 通常为 0（等待），但不直接互斥

## 实战应用
- **强趋势禁逆势(5)**：只顺势，不做反转。最保守的 Playbook，适合趋势交易日
- **区间边缘反转(3)**：在震荡区间边界以限价单思路博弈反弹，高胜率低盈亏比
- **过渡期反转(4)**：市场正在从趋势→震荡过渡，反转概率上升，需配合三推背景使用
- **趋势突破延续(1)**：新突破后顺势追入，盈亏比最高但需防假突破
- **顺势回调再入(2)**：趋势通道中等待回调到支撑/阻力再入场，Al Brooks 最推崇的玩法
- Playbook 是「建议」不是「信号」——具体入场仍需执行层的信号棒确认

## 来源支撑
- [[article-huangzongprice-v3-phase1]]

## 矛盾与待验证
- Playbook 的 5 种分类是 v3 首次引入的设计，尚未经 Phase-2 执行层验证其与具体入场策略的匹配度
- 「过渡期反转(4)」与「区间边缘反转(3)」的边界可能模糊——过渡期本身就可能表现为类似区间的行为，需观察实盘中两者的区分度
- Playbook 不等于入场信号——这是一个关键设计约束，但用户可能误将 Playbook 状态当作入场指令
