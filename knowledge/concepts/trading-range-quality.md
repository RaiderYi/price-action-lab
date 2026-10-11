---
title: "交易区间质量"
phase: [trend, range, breakout, transition]
signal_types: []
tags: [fade, test, third, 书本, brooks]
difficulty: intermediate
related: [tr-fade, barb-wire, trading-range-quality, brooks-signal-catalog, atr-scaling, eighty-percent-rule, buy-vacuum-sell-vacuum, article-brooks-pa-verification, README-summary, book-brooks-trading-ranges, encyclopedia-brooks-price-action-manual, article-20250519-brooks-context-4-pine, article-huangzongprice-pa-shape-audit]
char_count: 2423
---
# 交易区间质量

## 一句话定义
TR Fade 入场的前置条件：交易区间须包含 ≥8 根区间内K线，且边界须被测试 ≥2 次。

## 核心要点
- 两个硬性指标：`n_in_tr >= 8`（区间内K线数）和 `test_count >= 2`（边界测试次数）
- 只用于 [[tr-fade|TR Fade]] 信号，其他 14 种信号不依赖此规则
- 体现 Brooks 的"区间质量影响逆势交易胜率"理念——质量不够的区间不逆势

## 与相关概念的关系
- [[barb-wire]]：交易区间质量最差的形态——极度重叠的十字星铁丝网，应完全避免交易
- [[trading-range-quality]]：TR Fade 的唯一前置过滤器，不满足则不触发信号
- [[brooks-signal-catalog]]：TR Fade 是 16 种信号中唯一完全在区间内操作的信号
- [[atr-scaling]]：区间识别本身可能需要 ATR 辅助（代码实现细节待确认）
- [[eighty-percent-rule]]：区间质量判断是对 80% 法则（80% 突破失败）的量化落地
- [[buy-vacuum-sell-vacuum]]：区间顶部=买入真空测试阻力、底部=卖出真空测试支撑——这是 BLSHS 策略的力学基础

## 实战应用
当市场进入横盘震荡时，不要急于在区间边界逆势入场。先观察区间内是否积累了足够的 K 线（≥8 根）且边界被反复触及（≥2 次），确认区间有效性后再考虑第 3–4 次测试时入场。

## 来源支撑
## 来源支撑
- [[article-brooks-pa-verification]] §2.5
- [[README-summary]]（80/20 规则，即第4次反转做 TR Fade）
- [[book-brooks-trading-ranges]] — Brooks 原著中区间质量用「足够长到失去短期预测力」定性描述，本页的两个硬性数字是 huangzongprice 的量化实现
- [[encyclopedia-brooks-price-action-manual]]（BLSHS 策略、紧/宽 TR 分类、紧 TR = 突破模式）
- [[article-20250519-brooks-context-4-pine]]（Step4 TR否决：trPosBrooks 区间位置判定 → vetoTRlong/vetoTRshort）

## 矛盾与待验证
- `n_in_tr >= 8` 和 `test_count >= 2` 是最低门槛还是最优参数？不同品种/周期是否需要调整？验证文档未讨论
- Brooks 原著的 TR 入场规则中，"第3–4次"的计数起点是否为区间内的第一次边界触及？与 `test_count` 的对齐关系待确认
- **量化 vs 原著分歧**：Brooks 原著不使用硬性数字阈值，而是通过定性判断区间是否成熟。huangzongprice 的 8K+2测是简化版实现，可能牺牲了原著中的和区间多维度特征判断
- **书本 vs 实现差异（TR fade: major_diff）**： 发现 bear_tr_fade 和 bull_tr_fade 的 5/5 维度均与 Brooks 原著不一致。核心差异：① 趋势前提从 `trading_range` 量化为 `TR_mature`（需范围≥2 ATR + 20根中≥8根在 TR 内）；② 腿计数从 `third_or_fourth_test` 精确化为 `third_or_more_test_top/bottom`（测试次数≥2 才触发，rs 随次数增加）；③ 信号棒从 Brooks 的"阴线/阳线+second-entry"简化为"非强阳线/非强阴线+second-entry 反转棒"；④ 目标从"TR 中线或对侧"量化为"TR 中线"。`TR_mature` 的 ≥2 ATR 和 ≥8/20 根硬性数字阈值是 Brooks 原著中完全不存在的最激进量化简化。

### 书-码差异（来源：[[article-huangzongprice-pa-shape-audit]]）
**bear_tr_fade（TR 顶部 Fade Short，major_diff，0 samples）**：
- 趋势前提：书本 `trading_range` → 代码 `TR_mature`（增加了量化条件：范围>=2 ATR + 最近20根中>=8根在TR内）
- 腿计数：书本 `third_or_fourth_test` → 代码 `third_or_more_test_top`（>=3 次而非精确的 3~4 次）
- 信号棒：书本「顶部区域阴线或小阴线」→ 代码「非强阳线，通常为 second-entry 反转棒」
- 额外过滤：测试次数>=2 才触发，rs 随测试次数增加

**bull_tr_fade（TR 底部 Fade Long，major_diff，0 samples）**：
- 趋势前提：书本 `trading_range` → 代码 `TR_mature`
- 腿计数：书本 `third_or_fourth_test` → 代码 `third_or_more_test_bottom`
- 信号棒：书本「底部区域阳线或小阳线」→ 代码「非强阴线，通常为 second-entry 反转棒」

**关键问题**：两个 TR Fade 信号的样本数均为 0——差异结论基于纯理论对比，未经实际信号验证。代码的 `third_or_more_test` 放宽了书本的 `third_or_fourth` 限制（允许第5+次测试），是否会导致过度交易？
