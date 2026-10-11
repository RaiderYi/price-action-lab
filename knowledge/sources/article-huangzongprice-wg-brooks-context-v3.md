# Wedge-Gravity Brooks Context Engine V3.0

## 元信息
- 作者：huangzongprice
- 日期：未标注（V3.0 Pine Script v6 完整源码，推断为 V3 系列最新版）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_brooks_context_v3.txt`
- 类型：Pine Script v6 源码（1139 行，TradingView 指标）
- 与前版关系：V1.5（单指标双核）→ v1（单体内嵌背景）→ v3 Context/Execution 两层分离 → **本 V3.0（单指标集成版，完整流水线）**

## 一句话摘要
WG Brooks V3.0 是将背景裁决（Location/Phase/Momentum 三层加权）与结构识别（楔形/H2L2）和执行评分（三因子）集成在单一 Pine Script 指标中的完整实现——从 OHLC 到最终入场信号的全流水线。

## 核心论点

### 1. 背景裁决三层引擎（Background Decision Layer）
```
bgScore = locScore × 0.40 + phaseScore × 0.35 + momScore × 0.25
```
- **Location Context**：9 个位置判定变量（at/near 支撑阻力、区间中部、追价突破、目标临近）→ `locScoreL/S`（0-1）
- **Phase Context**：5 种过渡证据叠加检测 → `transitionCount` → 阶段健康分类（TrendHealthy / TrendWeakening / TwoSided）→ `phaseScoreL/S`
- **Momentum Health**：冲动评分 + 趋势健康 + 摆动对比 − 成熟度 − 衰竭风险 − 腿弱化 → `momScoreL/S`
- **裁决输出**：`bgSupportLong/Short`（背景支持）、`bgConflict`（冲突）、`bgVeto`（一票否决）、`bgState`（6 状态：VETO/BULL_STRONG/BULL_OK/BEAR_STRONG/BEAR_OK/NEUTRAL）

### 2. 否决条件增强（相对于 V1.5/V2）
V3 新增复合否决条件：`(trendMaturity≥0.65 或 exhaustRisk≥0.60)` **且** `currentLegWeakening≥0.50` **且** `lateBreakout`——要求三个条件同时满足才否决，比早期版本更精确。

### 3. 过渡检测系统
5 种独立过渡证据，计数 ≥ 2 判定为过渡态：
1. 重叠度 > 0.32
2. EMA 斜率丧失或走平
3. 宽通道 + 重叠 ≥ 0.24 + 置信 < 0.72
4. 楔形形态出现
5. 突破失败 / 紧急逃生

### 4. 结构分来源
- H2/L2 候选：默认结构分 0.55
- 楔形候选：对称度×0.40 + 收敛度×0.35 + 跨度×0.25
- 共振（WEDGE>H2 或 WEDGE>L2）：同时满足时取两者较好

### 5. 紧急逃生增强
V3 在 V1.5 的 emergExit 基础上新增两种检测：
- **exhBars**：连续两对 K 线实体极度重叠（ol/mb > 0.7）
- **exhCdl**：耗尽 K 线——实体 ≥ 20 周期均实体×1.5 且波幅 > ATR14×1.2

### 6. 动态风控参数
基于主要波段极点（majorSH/majorSL）和 ATR 动态计算入场/止损/止盈：
- `lSL = majorSL - 0.5×ATR20`（多头止损在主要低点之下）
- `lEnt = high + 0.1×ATR14`（多头入场在信号棒高点之上）
- `lTP = lEnt + 2.0×lRsk`（1:2 盈亏比）

### 7. 30 行信息面板
实时展示：市场周期、背景结论、三层分项分、结构优先级、信号棒分、执行分与等级、多空背景许可、紧急逃生状态、引力场、候选信号、综合信号等 30 项指标。

### 8. 12 种警报条件
覆盖：做多/做空入场、新突破、突破转通道、震荡区间、H2/L2 触发、紧急逃生、背景转强/否决、背景+候选。

## 与已有文献的关系

### 已覆盖（无需新增概念页）
以下概念已在 Wiki 中有完整页面，V3 源码与其公式一致：

| V3 模块 | 已有页面 | 匹配度 |
|---------|---------|--------|
| Location Context (`locScoreL/S`) | [[position-layer-scoring]] / [[atr-position-scoring]] | 100% — 相同公式 |
| Momentum Health (`momScoreL/S`) | [[momentum-health]] | 100% — 相同四维分解 |
| 趋势成熟度 | [[trend-maturity]] | 已覆盖 |
| 衰竭风险 | [[exhaustion-risk]] | 已覆盖 |
| 背景否决/冲突/支持 | [[background-permission]] | 90% — V3 新增复合否决条件 |
| 三层引擎架构 | [[wedge-gravity-dual-core]] | 已覆盖 |
| FSM 状态机 | [[fsm-market-cycle]] | 已覆盖 |
| 三推楔形 | [[three-push-wedge|Three Push Wedge]] | 已覆盖 |
| H2/L2 状态机 | [[h2-l2-state-machine|H2/L2 State Machine]] | 已覆盖 |
| 引力场 | [[gravity-field]] | 已覆盖 |
| 紧急逃生 | [[emergency-exit]] | 70% — V3 新增 exhBars/exhCdl 子类型 |
| 执行评分（三因子） | [[execution-scoring]] | 85% — V3 具体信号棒评分细节新增 |
| 确认 K 线 | [[confirmation-bar]] | 已覆盖 |
| 背景许可门控 | [[background-permission]] | 已覆盖 |

### 本次新增概念（3）
- [[phase-context-scoring]] — 阶段评分系统：transitionCount + 趋势健康分类 + phaseScoreL/S
- [[dynamic-risk-parameters]] — 动态风控参数：基于波段极点和 ATR 的 SL/TP/ENT 计算
- [[transition-detection-system]] — 过渡检测系统：5 证据 → 计数聚合 → 阶段过渡判定

## 提取出的新概念
1. [[phase-context-scoring]]：阶段评分公式——过渡检测 + 健康分类 + 加权打分
2. [[dynamic-risk-parameters]]：从 Swing 高/低点 + ATR 推导的完整风控参数链
3. [[transition-detection-system]]：5 种过渡证据的独立检测与聚合逻辑

## 与现有知识的冲突
- **否决条件更严格**：V3 的 bgVetoLong/Short 第四项要求 `(成熟度≥0.65 或 衰竭≥0.60)` **且** `腿弱化≥0.50` **且** `追价`——而 [[background-permission]] 记录的条件是 `(成熟度≥0.65 或 衰竭≥0.60) & 目标接近`。V3 用腿弱化和追价替代了目标接近，增加了复合条件的精确性。
- **紧急逃生子类型**：V3 新增 exhBars（实体重叠）和 exhCdl（耗尽 K 线）两个独立触发条件。[[emergency-exit]] 页面未记录这两种类型。
- **相位评分权重**：V3 的 phaseScoreL/S 在逆势方向的让步（+0.22 当 phaseDir 反向且出现楔形/H2/接近支撑）比早期版本的设计稿更精确地量化了逆势许可条件。
