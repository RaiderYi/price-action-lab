---
title: "PA 形态：书本定义 vs 代码实现对照（已过时）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, flag]
tags: [major, bear, bull, wedge, ema]
difficulty: intermediate
related: [book-impl-divergence, brooks-signal-catalog, h2-l2-state-machine, three-push-wedge, climax, tbtl, trading-range-quality, double-top-bottom, article-huangzongprice-pa-shape-audit]
char_count: 3351
---
> ⚠️ **已过时** — 本页已被 [[book-impl-divergence]] 取代。新页面修正了信号计数（20 个而非 16 个）并提供了更完整的 5 维度差异分析。请使用新页面。

# PA 形态：书本定义 vs 代码实现对照（已过时）

## 一句话定义
对 Brooks 16 种价格行为信号形态进行"书本定义 vs 代码实现"的 5 维度逐项对照审计，揭示量化实现中所有系统性偏离。

## 核心要点

### 审计框架：5 维度
1. **趋势前提**：入场前市场必须处于的趋势状态
2. **腿计数**：回撤/反弹的腿数判定规则
3. **市场背景**：更广泛的价格环境条件
4. **价位/形态关系**：信号 K 线在整体形态中的位置要求
5. **信号棒要求**：触发信号的具体 K 线特征

### 差异等级
- **major_diff**：≥3 个维度存在不一致（14/16 形态）
- **minor_diff**：仅细节表述差异，核心逻辑一致（2/16 形态）

### 16 形态对照速查表

| # | 形态 | 方向 | 等级 | 5维一致性 | 关键差异 |
|---|------|------|------|----------|---------|
| 1 | bear_double_top | 空 | major | 0/5 | 趋势前提 TR_high 表述简化；腿计数改为 15 根内双高点 |
| 2 | bear_l1 | 空 | major | 0/5 | 趋势改为 EMA20 下方；腿计数增加 low break 条件 |
| 3 | bear_l2 | 空 | major | 0/5 | 允许 TR 但下半区禁止；信号棒增 min_rs 过滤 |
| 4 | bear_l3_wedge | 空 | major | 0/5 | 三推用斜率判定（高点斜率<0）；楔形末端阴线 |
| 5 | bear_post_climax | 空 | major | 1/5 | 趋势前提一致(post_bull_climax)；TBTL 自动否决 |
| 6 | bear_stc | 空 | major | 0/5 | AIS_like 量化替代；需≥3 根最近阴线 |
| 7 | bear_tr_fade | 空 | major | 0/5 | TR 需范围≥2ATR+20 根≥8 根在内；测试次数≥2 |
| 8 | **bear_wedge_flag** | 空 | **minor** | 2/5 | 仅市场背景/价位/信号棒细节差异 |
| 9 | bull_btc | 多 | major | 0/5 | AIL_like 量化替代；需≥3 根最近阳线 |
| 10 | bull_double_bottom | 多 | major | 0/5 | 趋势前提简化；双底不深于 EMA20-3ATR |
| 11 | bull_h1 | 多 | major | 0/5 | EMA 上方 bias 量化；回调深度 0.3~5 ATR |
| 12 | bull_h2 | 多 | major | 0/5 | TR 上半区禁止做多；腿计数精确量化 |
| 13 | bull_h3_wedge | 多 | major | 0/5 | 低点斜率>0 量化；实体中等以上要求 |
| 14 | bull_post_climax | 多 | major | 1/5 | 趋势前提一致(post_bear_climax)；TBTL 自动否决 |
| 15 | bull_tr_fade | 多 | major | 0/5 | 同上 bear_tr_fade；非强阴线作为信号棒 |
| 16 | **bull_wedge_flag** | 多 | **minor** | 2/5 | 仅市场背景/价位/信号棒细节差异 |

### 系统性差异模式

**模式 1：趋势前提的量化解耦**（12/16 形态）
- 书本：`bear_trend`、`bull_trend`、`always_in_short`、`trading_range`
- 实现：`ema_below_20_bear_bias`、`ema_above_20_bull_bias`、`AIS_like`、`TR_mature`
- 本质：自然语言 → 可计算条件，必然丢失部分主观判断

**模式 2：腿计数的精确化**（16/16 形态）
- 书本：`first_pullback`、`two_legs_pullback`、`three_push_up`
- 实现：`first_pullback_low_break`、`two_local_highs_H2_lt_H1`、`three_local_highs_wedge`
- 本质：Brooks 的主观"腿"概念 → 可编程的局部极值+条件链

**模式 3：实现独有的额外过滤**（实现有，书本无）
- RS 评分阈值（`min_rs`）：所有趋势信号均有最低分要求
- regime_penalty：高潮背景信号大幅降分
- TBTL 自动否决：`ann.tbtl_active=True → is_valid=False`
- 风险限制：L3/H3 wedge `rs≈58`，风险<5%

**模式 4：TR 规则的空间量化**（TR fade + L2/H2）
- 书本：TR 顶部/底部区域
- 实现：TR 顶部/底部 20% 区域精确计算，需范围≥2 ATR
- L2 允许在 TR 内但在下半区禁止；H2 允许在 TR 但在上半区禁止

### 差异并非错误

这些差异的本质是 **Brooks 主观交易体系 → 可编程量化规则的工程取舍**：
- 书本用人类可理解的语言描述"感觉"和"判断"
- 实现必须用精确的布尔条件替代，否则无法编程
- wedge_flag 的两个 minor_diff 是最接近原著的形态——因为它们本身就有清晰的几何定义

## 与相关概念的关系
- [[brooks-signal-catalog]]：本审计覆盖的 16 种信号即 catalog 的全部白名单信号
- [[h2-l2-state-machine|H2/L2 State Machine]]：L1/L2/H1/H2 的实现差异直接影响状态机输出
- [[three-push-wedge|Three Push Wedge]]：L3/H3 wedge + wedge_flag 的实现差异影响楔形检测
- [[climax]]：post_climax 的实现差异影响高潮后信号的触发条件
- [[tbtl]]：post_climax 中 TBTL 自动否决是书本无对应的工程创新
- [[trading-range-quality]]：TR fade 的 2ATR+8根 量化门槛是最大的书本-实现分歧
- [[double-top-bottom]]：双顶/双底的实现使用 15 根内双高点，与 Brooks 的 L2 等价说一致但量化方式不同

## 实战应用
使用 huangzongprice 的量化交易系统时，理解每个信号的触发条件与 Brooks 原著并不完全相同。例如：
- 趋势判断用 EMA20 而非 Brooks 的主观趋势判断
- 高潮后信号在 TBTL 完成前会被自动否决——即使"看起来"是个好信号
- TR Fade 需要严格的量化 TR 确认——主观感觉是 TR 但未满足 8根+2ATR 条件时不会触发

## 来源支撑
- [[article-huangzongprice-pa-shape-audit]]

## 矛盾与待验证
- 所有 16 形态的 Samples=0——本审计纯属定义层面对照，未经回测统计验证实现偏离对实际交易结果的影响
- 部分"差异"可能是合理的工程简化（如 EMA20 替代主观趋势判断），部分可能需要修正——需逐形态回测对比才能判断
