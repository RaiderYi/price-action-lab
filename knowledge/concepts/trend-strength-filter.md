---
title: "趋势强度过滤"
phase: [trend, range, breakout, transition]
signal_types: [wedge, pullback-entry]
tags: [紧密通道, 测量缺口, trendblock, true, 趋势强度]
difficulty: intermediate
related: [playbook-engine, channel, gaps, eighty-percent-rule, article-background-v3-upgrade]
char_count: 1024
---
# 趋势强度过滤

## 一句话定义
判断趋势是否强到"不适合做反转"——强趋势中反转玩法应降权或直接否决。

## 核心要点
- **来源函数**：`trendBarRatio`（趋势棒占比）、`consecutiveBars`（连续同向K线）、`emaSideRatio`（均线单侧占比）、`detectTightChannel`（紧密通道）、`detectMeasuredGap`（测量缺口）、`assessTrendStrength`
- **核心输出**：`trendBlockBull`/`trendBlockBear`（趋势屏蔽）、`tightChannelBull`/`tightChannelBear`（紧密通道）、`gapImpulseBull`/`gapImpulseBear`（缺口驱动）
- **强趋势的三层程度**：
  - 普通趋势 → 降低反转背景评分（`trendPenalty`）
  - 极强趋势 → 直接否决反转玩法（`trendBlock`）
  - 紧密通道 → 不鼓励楔形逆势执行
  - 测量缺口 → 提高趋势延续倾向

## 与相关概念的关系
- [[playbook-engine]]：`trendBlock` 触发 playbook=5 强趋势禁逆势
- [[channel]]：紧密通道检测直接基于通道识别，但加入了"窄到不能做反转"的阈值
- [[gaps]]：测量缺口是该模块的输入之一
- [[eighty-percent-rule]]：方法论根源——趋势中 80% 反转尝试失败

## 实战应用
- 当 `trendBlockBull=true` 时，所有做空信号（哪怕三推楔形）都应被屏蔽或降权至不可执行
- 当 `tightChannelBull=true` 时，上升楔形做空即使信号棒合格也应放弃——紧密通道中逆势入场极易被扫止损
- 当 `gapImpulseBull=true` 且未封闭时，优先寻找顺势 BTC/STC 而非等待回调

## 来源支撑
- [[article-background-v3-upgrade]]

## 矛盾与待验证
- 趋势强度的阈值（多少根连续同向棒=强趋势？ATR 倍数多大=紧密通道？）在设计稿中未给出具体数值，需实现时标定。
- `trendBlock` 与 `bgVeto` 的关系：两者都是一票否决，是否应合并或保持独立层级？
