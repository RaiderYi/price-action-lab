---
title: "书本-实现差异体系"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry]
tags: [atr, book, impl, 码差异在, bear]
difficulty: intermediate
related: [brooks-signal-catalog, atr-scaling, wedge-gravity-dual-core, rs-scoring, h2-l2-state-machine, three-push-wedge, double-top-bottom, climax, btc-stc, trading-range-quality, article-huangzongprice-pa-shape-audit]
char_count: 1927
---
# 书本-实现差异体系

## 一句话定义
Brooks 原著定性描述与 Pine Script 量化实现之间的系统性偏差框架，覆盖 20 种信号形态的 5 个维度。

## 核心要点
- 所有 20 种信号形态的书本定义与代码实现均存在差异（18 个 major_diff + 2 个 minor_diff）
- 差异根源：Brooks 用定性语言（"不深"、"不太小"、"接近"），代码需量化（`0.3~5 ATR`、`实体>=0.10`）
- 差异分五维度：趋势前提、腿计数、市场背景、价位/形态关系、信号棒要求
- 差异不可消除——是连续世界离散化的必然代价

## 三类系统性偏差

### 1. 数值化替代（20/20 形态）
书本的模糊描述被替换为确定数值：
- "回调不深" → `0.3~5 ATR`
- "实体不太小" → `实体比例 >= 0.10`
- "价位接近" → `价差 <= 0.5 ATR`
- "强阴线" → `实体 >= 0.18`

### 2. 状态机简化（10/20 形态）
书本的多层市场状态被压缩为有限状态机：
- `bear_trend` / `bull_trend` → `ema_below_20_bear_bias` / `ema_above_20_bull_bias`
- `always_in_short` → `AIS_like`
- `trading_range` → `TR_mature`（增加了量化条件：范围>=2 ATR + ≥8根在TR内）
- TR 区域限制：下半区禁止做空 / 上半区禁止做多（书本仅提"不建议"）

### 3. 额外约束增加（6/20 形态）
代码新增了书本未提及的过滤：
- `min_rs` + `regime_penalty`（L2/H2、STC/BTC）
- `TBTL` 统一过滤潮后信号（post_climax、L1/H1）
- 测试次数下限 >=2（TR_fade）

## 与相关概念的关系
- [[brooks-signal-catalog]]：16 种信号类型的全览，本概念标注每类信号的「书-码」差异
- [[atr-scaling]]：ATR 归一化是数值化替代的核心工具——所有「深度/距离/实体」都通过 ATR 变为可比较值
- [[wedge-gravity-dual-core]]：硬规则 FSM 部分是状态机简化的直接体现
- [[rs-scoring]]：RS 评分中的 `regime_penalty` 是额外约束的主要载体
- [[h2-l2-state-machine|H2/L2 State Machine]]：H2/L2 状态机是 L1/L2/H1/H2 信号代码实现的差异来源
- [[three-push-wedge|Three Push Wedge]]：楔形形态的书-码差异主要在于腿计数（book=three_push_up/down, impl=三点聚敛+斜率条件）
- [[double-top-bottom]]：双顶/双底的书-码差异在于等价关系（book=本质是L2/H2, impl=独立形态）
- [[climax]]：高潮后反转的书-码差异在于腿计数精度（book=二腿, impl=近似二腿）和 TBTL≥10 量化
- [[btc-stc]]：BTC/STC 的书-码差异在于趋势前提量化（book=always_in, impl=多根连续同向K线计数）
- [[trading-range-quality]]：TR Fade 的书-码差异在于 TR 成熟度量化（book=第3~4次, impl=范围+根数+次数）

## 实战应用
在审查或维护量化交易系统时，对每个信号形态从 5 个维度逐项对照书本原文——如果差异存在，确认是「有意简化」还是「实现错误」。

## 来源支撑
- [[article-huangzongprice-pa-shape-audit]] — PA 形态对照验证报告（20 种信号的 5 维度全面对照）

## 矛盾与待验证
- 所有 18 个 major_diff 信号的书-码差异是否属于「有意设计取舍」或「实现 bug」——需要在 huangzongprice 的原始设计文档中寻找证据
- `bear_stc` 和 `bull_btc` 的 Samples=2/6，数据量极少，差异可能因样本不足而放大
- `bear_tr_fade` 和 `bull_tr_fade` 的 Samples=0，报告中的差异结论是纯理论对比，未经实际信号验证
