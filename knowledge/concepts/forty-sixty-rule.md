---
title: "40-60 规则（Forty-Sixty Rule）"
phase: [trend, range, breakout, transition]
signal_types: [scalp, swing]
tags: [规则, 胜率, 回报, brooks, tick]
difficulty: intermediate
related: [trader-equation, swing-vs-scalp, eighty-percent-rule, momentum-vs-value-traders, encyclopedia-brooks-price-action-manual, book-brooks-trends, atr-scaling]
char_count: 1157
---
# 40-60 规则（Forty-Sixty Rule）

## 一句话定义
Brooks 的核心概率假设：90% 的时间里市场价格向某方向移动 N 点再反向移动 N 点的概率在 40%~60% 之间。

## 核心要点
- **规则内容**：90% 的交易日（市场处于通道或交易区间时），价格先涨 N 点再跌 N 点的概率在 40%~60%；反之亦然
- **数字 N 不敏感**：无论是 10 tick、20 tick、17 点、1%，规则都成立——关键是概率区间而非具体幅度
- **来源逻辑**：必须有机构在对立面——任何一方都不会让概率变得非常确定而不伴随风险大增
- **10% 的例外**：市场处于强势突破时，顺势交易胜率可达 70%+，但止损通常很远
- **核心推论**：只要回报 ≥ 2× 风险，交易者方程就是正的
  - 最差情况：40% × 2R − 60% × 1R = 0.8R − 0.6R = +0.2R（正期望值）
  - 理论上 40% 胜率 + 2:1 回报比就能盈利

## 与相关概念的关系
- [[trader-equation]]：40-60 规则是交易者方程中「概率」变量的经验取值依据
- [[swing-vs-scalp]]：波段交易依赖 40-60 规则（40% 胜率 + ≥2R 回报 = 盈利）；刮头皮需要 60%+ 胜率
- [[eighty-percent-rule]]：趋势中 80% 反转失败、区间中 80% 突破失败——10% 的例外时间对应 80% 法则的另一面
- [[momentum-vs-value-traders]]：动量交易者利用 10% 突破时间的高胜率；价值交易者依赖 90% 时间的 40-60 规则+大回报比

## 实战应用
每笔交易前默念：胜率大概率 40-60%。如果止损=回报，需要 60%+ 胜率才盈利（太难）→ 必须确保回报 ≥ 2× 风险。波段交易是最合理的入门策略。

## 来源支撑
- [[encyclopedia-brooks-price-action-manual]]（Al Brooks 命名并反复引用）
- [[trader-equation]]（数学基础）
- [[book-brooks-trends]]（Brooks 趋势篇原著中含此规则的详细讨论）

## 矛盾与待验证
- 「90% 时间」是一个经验估计而非精确统计——真实比例可能因市场/时间框架而异
- 在极端低波动（如 A 股某些时段）中，N tick 可能永远到不了——规则隐含了「在正常波动下」的前提
- 量化实现中，已有 ATR 归一化体系的动态阈值（[[atr-scaling]]）可以部分验证此规则在不同波动率下的表现
