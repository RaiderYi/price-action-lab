---
title: "三推背景识别"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry, reversal-entry]
tags: [playbook, 识别, 度证据, 切换依据, 三推]
difficulty: intermediate
related: [three-push-wedge, playbook-engine, trend-strength-filter, fsm-market-cycle, article-background-v3-upgrade, article-wg-v15-analysis]
char_count: 1121
---
# 三推背景识别

## 一句话定义
三推在背景层 v3 中的重新定位——不再仅仅是执行结构，而是作为**趋势成熟度证据、过渡证据、Playbook 切换依据**。

## 核心要点
- **角色重新定义**：三推 ≠ 入场信号，三推 = 背景成熟度证据
- **背景层保留三推的原因**：
  - 三推是 Brooks 体系中"趋势衰竭背景"的重要证据
  - 帮助背景层判断当前应看延续还是反转
  - 提供 Playbook 从"顺势"切换至"过渡反转"的依据
- **背景层保留什么**：三推动作、回撤验证（PB2<PB1）、趋势惩罚、概率评分、屏蔽判断
- **背景层不放什么**：入场线、止损线、T1/T2 目标位、磁铁线、具体交易触发条件（留在执行/管理层）
- **三推对背景的核心贡献**：
  - A. 提供过渡证据：三推出现+回撤有效+PB2浅于PB1+趋势惩罚下降 → 趋势从健康→成熟衰竭
  - B. 提供玩法切换依据：原本顺势→出现三推→切换为过渡反转观察

## 与相关概念的关系
- [[three-push-wedge|Three Push Wedge]]：执行层的三推楔形检测——关注形态结构与入场评分。背景识别版关注成熟度与玩法切换
- [[playbook-engine]]：三推是 playbook 从"顺势回调再进入"切换到"过渡期反转"的核心触发条件
- [[trend-strength-filter]]：若趋势仍极强（`trendBlock=true`），即便三推出现也只记为衰竭预警，不允许执行反转
- [[fsm-market-cycle]]：三推出现叠加 `phaseIsTransition` 时，反转信号权重最高

## 实战应用
背景层三推识别的实战意义：
- 看跌三推：趋势极强时→仅衰竭预警；趋势弱化/过渡中→提升"过渡反转"权重；区间上沿→提升"边缘反转"权重
- 看涨三推：镜像处理
- 核心问题不是"三推是否出现"，而是"在当前背景下，三推被允许执行还是仅作观察"

## 来源支撑
- [[article-background-v3-upgrade]]
- [[article-wg-v15-analysis]]（三推楔形检测的原始实现）

## 矛盾与待验证
- 背景层与执行层都保留三推识别：如何避免重复计算？设计稿建议背景层输出 `triPushBackgroundWeight` 和 `triPushBlocked` 给执行层消费，但两层的边界仍需代码实现时验证。
- 三推的"回撤有效性"判断标准（PB2 必须浅于 PB1 多少比例？）在设计稿中未量化。
