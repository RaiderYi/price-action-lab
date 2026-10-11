---
title: "趋势成熟度（Trend Maturity）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, wedge, pullback-entry, swing, flag]
tags: [衰竭棒, 衰竭风险, 追价突破, 目标位临, trendmaturityl]
difficulty: intermediate
related: [late-breakout, exhaustion-risk, three-push-wedge, final-flag, climax, article-huangzongprice-context-engine-v2, article-huangzongprice-context-engine-v1, article-20260520-wedge-gravity-brooks-context-v3, article-huangzongprice-context-engine-v3-rebuild, momentum-health]
char_count: 2066
---
# 趋势成熟度（Trend Maturity）

## 一句话定义
通过楔形形态、追价突破、衰竭棒、目标位临近四个信号综合评估当前趋势段已运行到什么阶段——成熟度越高，反转风险越大，做顺势交易的安全性越低。

## 核心要点
- **四因子加权**（多方 `trendMaturityL`）：楔形×0.35 + 追价突破×0.25 + 衰竭棒×0.20 + 目标位临近×0.20
- **与衰竭风险的区别**：成熟度评估「趋势走了多远」（偏时间/阶段维度），衰竭风险评估「趋势内部出现多少危险信号」（偏动能/质量维度）
- **在动能层中的角色**：成熟度是扣分项（-0.20 权重），直接压低 `momScore`
- **与否决系统的联动**：当成熟度 ≥ 0.65 或衰竭风险 ≥ 0.60 且目标位临近时，触发背景否决
- **空方镜像**：`trendMaturityS` 使用下降楔形 + 空方向追价 + 衰竭棒 + 空方目标位临近

## 各因子详解

### 1. 楔形形态（+0.35）
- `risingWedge`：连续三个波段的 HH 逐步抬高但 LH 也逐步抬高（上升楔形=多头动能衰减）
- `fallingWedge`：连续三个波段的 LL 逐步降低但 HL 也逐步降低（下降楔形=空头动能衰减）
- 要求波段间最少 8 根 K 线（`(ph0b - ph2b) >= 8`），最多 200 根

### 2. 追价突破（+0.25）
参见 [[late-breakout]]。当价格已突破旧 Donchian 边界、远离支撑且贴近对向阻力时判定为追价——此时入场属于「追在末端」。

### 3. 衰竭棒（+0.20）
条件：实体 ≥ avgBody20 × 1.50 且 波幅 > ATR14 × 1.20。出现超大实体的异常波动棒，往往标志趋势已进入高潮阶段——可能是衰竭而非启动。

### 4. 目标位临近（+0.20）
多方目标位（最近波段高点或 Donchian High）≤ 0.80 ATR 距离时，盈利空间急剧压缩。更多做趋势延续的交易者会在此获利了结，增加反转概率。

## 与相关概念的关系
- [[exhaustion-risk]]：姐妹概念——成熟度回答「走了多远」，衰竭风险回答「还能走吗」
- [[three-push-wedge|Three Push Wedge]]：楔形检测是成熟度的最大权重因子（0.35）
- [[late-breakout]]：追价判定是成熟度的第二权重因子（0.25）
- [[final-flag]]：最终旗形是趋势末端的另一种表现——与高成熟度场景高度重叠
- [[climax]]：高潮（Climax）概念——衰竭棒（大实体+大波幅）就是 Brooks 的高潮棒

## 实战应用
在 Context Engine 信息面板中查看「成熟度 L/S」行。当 `trendMaturityL` > 0.60 时，即使背景支持做多（bgSupportLong），顺势追入的风险已显著升高——应考虑等待回调而非追价。当成熟度 + 衰竭风险均高且目标临近时，背景可能被直接否决。

## 来源支撑
- [[article-huangzongprice-context-engine-v2]]（v2 Context Engine 实现 trendMaturity 四因子评分完整源码）
- [[article-huangzongprice-context-engine-v1]]（v1 首次引入趋势成熟度评分）
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：成熟度四因子权重 0.35/0.25/0.20/0.20 精确值 + 在 momScore 中 -0.20 扣分 + 在否决条件中 ≥0.65 阈值）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 源码第547-548行——trendMaturityL/S 精确四因子加权，含 exhaustRiskL/S 互补公式第550-551行）
- [[momentum-health]]：成熟度是动量健康框架四子评分的扣分项之一（−0.20），与 exhaustRisk/legWeakening 形成互锁

## 矛盾与待验证
- 四因子的权重配比（0.35/0.25/0.20/0.20）是否经过回测优化？文档未说明
- `maturityThr`（成熟度高阈值）默认为 0.65——与 `exhaustRiskThr` 默认 0.60 不同，似乎认为成熟度比衰竭风险更容忍
- 成熟度仅在动能层扣分和否决条件中使用，未在位置层或阶段层中体现——可能低估了成熟度对阶段判断的影响（高成熟度趋势本质上是「准过渡」状态）
