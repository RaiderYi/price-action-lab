> ⚠️ **已过时** — 本页已被 [[article-huangzongprice-pa-shape-audit]] 取代。新页面基于 pa_shape_audit_report_sample.md 提供了更完整的 20 信号对照。请使用新页面。

# PA 形态对照验证报告（已过时）

## 元信息
- 作者：huangzongprice
- 日期：未标注（推测与执行引擎 v3 同步，2026年）
- 原始位置：`raw/articles/huangzongprice/pa_shape_audit_report.md`

## 一句话摘要
对 Brooks 16 种 PA 信号形态逐项进行"书本定义 vs 代码实现"的 5 维度对照审计，发现所有 16 种形态均存在差异（14 major_diff + 2 minor_diff）。

## 核心论点

### 审计方法论
- **5 维度对照**：趋势前提、腿计数、市场背景、价位/形态关系、信号棒要求
- **差异等级**：`major_diff`（至少 3 个维度不一致）vs `minor_diff`（仅细节差异）
- **样本数**：所有形态 `Samples=0`——审计纯属定义层面对照，未经回测统计验证

### 审计结果总览

| 方向 | 形态 | 等级 | 核心差异字段 |
|------|------|------|------------|
| 空头 | bear_double_top | major_diff | 5/5 维度不一致 |
| 空头 | bear_l1 | major_diff | 5/5 维度不一致 |
| 空头 | bear_l2 | major_diff | 5/5 维度不一致 |
| 空头 | bear_l3_wedge | major_diff | 5/5 维度不一致 |
| 空头 | bear_post_climax | major_diff | 4/5 维度不一致（趋势前提一致） |
| 空头 | bear_stc | major_diff | 5/5 维度不一致 |
| 空头 | bear_tr_fade | major_diff | 5/5 维度不一致 |
| 空头 | bear_wedge_flag | **minor_diff** | 3 维度细节差异（趋势前提+腿计数一致） |
| 多头 | bull_btc | major_diff | 5/5 维度不一致 |
| 多头 | bull_double_bottom | major_diff | 5/5 维度不一致 |
| 多头 | bull_h1 | major_diff | 5/5 维度不一致 |
| 多头 | bull_h2 | major_diff | 5/5 维度不一致 |
| 多头 | bull_h3_wedge | major_diff | 5/5 维度不一致 |
| 多头 | bull_post_climax | major_diff | 4/5 维度不一致（趋势前提一致） |
| 多头 | bull_tr_fade | major_diff | 5/5 维度不一致 |
| 多头 | bull_wedge_flag | **minor_diff** | 3 维度细节差异（趋势前提+腿计数一致） |

### 系统性差异模式

**趋势前提的简化**（影响 12/16 形态）：
- 书本用自然语言描述（如 `bear_trend`、`trading_range`）
- 实现用可量化规则替代（如 `ema_below_20_bear_bias`、`TR_mature`）
- 典型：`always_in_short` → `AIS_like`，`trading_range` → `TR_mature`（需范围≥2ATR+≥8根）

**腿计数的工程化**（影响 16/16 形态）：
- 书本用 Brooks 术语（`first_pullback`、`two_legs_pullback`）
- 实现用精确条件（`first_pullback_low_break`、`two_local_highs_H2_lt_H1`）
- 本质是将 Brooks 的主观判断转化为可编程的布尔条件

**额外过滤机制**（实现独有，书本无对应）：
- RS 评分最低阈值（如 bear_l1/l2/h1/h2 的 `min_rs`）
- regime_penalty（高潮背景下大幅降分）
- TBTL 活动状态自动否决（`ann.tbtl_active=True → is_valid=False`）

### 两个 minor_diff 形态的特点

bear_wedge_flag 和 bull_wedge_flag 是仅有的 minor_diff 形态——趋势前提和腿计数与书本完全一致，仅在市场背景/价位关系/信号棒要求的细节表述上有差异。这说明旗形+楔形的量化实现与 Brooks 原著最为接近。

## 提取出的新概念
- [[pa-shape-book-vs-impl]] — 书本 vs 实现的系统性对照审计（方法论+16形态对照表+差异模式）
- [[stc-btc]] — Buy The Close / Sell The Close 强趋势信号（此前仅在 [[brooks-signal-catalog]] 中列为条目，无独立概念页）

## 与现有知识的冲突
- **所有 16 种形态的实现均与 Brooks 原著存在差异**，差异程度从细节表述（minor_diff）到核心逻辑替换（major_diff）不等
- 这并非"错误"——本质是 huangzongprice 将 Brooks 的主观判断体系量化为可编程规则时的必然取舍
- 已更新以下概念页的「矛盾与待验证」：
  - [[double-top-bottom]]（bear_double_top / bull_double_bottom）
  - [[three-push-wedge|Three Push Wedge]]（L3/H3 wedge + wedge_flag）
  - [[climax]]（post_climax）
  - [[tbtl]]（post_climax 实现差异）
  - [[brooks-signal-catalog]]（全局对照引用）
  - [[h2-l2-state-machine|H2/L2 State Machine]]（L1/L2/H1/H2）
  - [[trading-range-quality]]（TR fade）
