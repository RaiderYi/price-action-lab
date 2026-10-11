---
title: "开盘交易（Trading the Open）"
phase: [trend, range, breakout, transition]
signal_types: [wedge, breakout-entry, pullback-entry, scalp, swing, flag]
tags: [brooks, 开盘反转, 分钟, 开盘交易, 开盘初期]
difficulty: intermediate
related: [always-in, breakout-mechanics, double-top-bottom, swing-vs-scalp, gap-probability-chain, encyclopedia-brooks-price-action-manual, article-huangzongprice-probability]
char_count: 1551
---
# 开盘交易（Trading the Open）

## 一句话定义
Al Brooks 的开盘交易统计与策略：开盘初期是日内高低点和波段机会最集中的时间窗口。

## 核心要点
- **关键统计（5 分钟图 Emini）**：
  - 日内最高/最低点出现在第 1 根 K 线的概率：约 20%
  - 出现在前 7 根 K 线内的概率：约 50%
  - 出现在前 90 分钟内的概率：约 90%
- **前两小时是最佳交易时段**：开盘反转和趋势突破最容易形成波段交易机会
- **尾盘不交易也 OK**：最后 1 小时的反复反转主导市场，难以盈利
- **开盘反转模式**：
  - 开盘缺口后回补（gap close = exhaustion gap）
  - 拉回至均线后形成楔形看多旗形买点
  - 双底/双顶在开盘区间内形成 → 突破 → 测量走势
- **开盘不立即趋势的情况**：如果在最初几根 K 线中未快速测试 S/R 并反转进入趋势，通常形成某种双底/顶 → 区间突破 → 至少一个基于区间高度的测量走势
- **开盘突破方向**：如果开盘在均线下方 → 反弹至均线 → 回落 → 再次反弹至均线，交易者会在第二次测试转跌时做空（赌双顶 = 日高）

## 与相关概念的关系
- [[always-in]]：开盘后 Always In 方向的判断是开盘交易的核心决策
- [[breakout-mechanics]]：开盘双底/顶突破后的测量走势
- [[double-top-bottom]]：开盘区间中的双顶/底是最常见的反转形态
- [[swing-vs-scalp]]：开盘初期更有可能形成波段机会（开盘反转往往走出趋势）

## 实战应用
关注前 7 根 5 分钟 K 线（35 分钟）内的反转和突破信号。如果开盘第 1 根 K 线形成极端高/低 + 随后反转，这是高概率的波段入场窗口。尾盘不勉强交易。

### 大幅低开的概率链（来自 [[gap-probability-chain]]）

| 时段 | 概率 | 行为 |
|------|------|------|
| 第一小时 | 60% 下行 | 开盘延续下跌 |
| 上午10点后 | 70% 下行 | 早盘回调后再次下跌 |
| 首两小时 | 85% 回调 | 几乎必然出现回调 |
| 全天 | 75% 趋势型TR日 | 倾斜区间，非纯粹趋势 |
| 首K强势收高 (BLBCOH) | 40% 成为当日最低 | 极端信号→可能已是底部 |
| 收盘 | 仅 35% 回补缺口 | 缺口回补是低概率事件 |

### 开盘极值概率补充（来自 Brooks 概率表）
- **仅 20%** 首 K 高/低点成为当日极值（修正：此前说「首 K 约 20%」与此一致）
- **50%** 开盘强劲运动反转

## 来源支撑
- [[encyclopedia-brooks-price-action-manual]]（Al Brooks 开盘交易章节完整公开）
- [[article-huangzongprice-probability]]（Brooks 概率表——大幅低开概率链 + 首K极值 + 开盘反转）
- [[gap-probability-chain]]（缺口特化场景的完整概率时间线）

## 矛盾与待验证
- Brooks 的统计数据基于美股 Emini 期货——A 股 T+1 且开盘竞价机制不同，统计概率需要独立验证
- A 股 30 分钟 K 线的「前 7 根」= 3.5 小时，开盘统计意义需要本地化
- 「尾盘不交易」在 A 股可能不成立（尾盘集合竞价有时有大资金动作）
