---
title: "三推楔形 / 三推背景识别"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, reversal-entry, flag]
tags: [wedge, 跨度, 楔形, 抛物线楔, 三推背景]
difficulty: intermediate
related: [fsm-market-cycle, trend-strength-filter, playbook-engine, tri-push-background, h2-l2-state-machine, gravity-field, execution-layer, execution-engine-architecture, execution-scoring, background-permission, confluence-trading, expanding-triangle, parabolic-wedge, article-20260520-wedge-gravity-brooks-context-v3, article-20200818-brooks-10-best-pa-patterns, article-wedge-gravity-v14-source, article-wg-v15-analysis, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-execution-layer-v1, article-background-v3-upgrade, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked, encyclopedia-al-10-best-setups, article-huangzongprice-wedge-gravity-v2-master, article-20260519-wedge-gravity-v41-flowchart, article-huangzongprice-wedge-gravity-v5-cycle-structure, article-huangzongprice-pa-shape-audit]
char_count: 5408
---
# 三推楔形 / 三推背景识别

## 一句话定义
V1.5：在 Pivot 确认柱上，用最近三组高/低点构造楔形并评分。v3：升级为独立枢轴数组 + 回撤分析 + 质量评分 + 背景权重的完整三推引擎。

## 核心要点

### V1.5 / V5.0 楔形检测
- **上升楔形 `risingWedge`**（偏空结构）：在 `isPH` 且 ph0..2、pl0/pl1 齐全时判定，检查时间序、跨度、`f_wedgeOK`（空间/时间对称比）、上下界斜率收口
- **下降楔形 `fallingWedge`**（偏多结构）：在 `isPL` 上对称判定
- **V5.0 评分权重（明确化）**：symScore×0.40 + convScore×0.35 + spanScore×0.25 → 汇入 `structScoreL/S`
- **V5.0 `WedgeData` 类型**：barA-E、priceA-E、三项评分 + isValid 标记完整保存到一个对象中
- 与 H2/L2 可同时为真，分数上不互斥

### v1 执行引擎楔形（最简检测）
- **上升楔形**：`ph2b < pl1b < ph1b` 且 `ph1 > ph2` 且 `pl0 > pl1` → 偏空
- **下降楔形**：`pl2b < ph1b < pl1b` 且 `pl1 < pl2` 且 `ph0 < ph1` → 偏多
- **无回撤分析**：不检查两推之间回撤深度，纯三枢轴位置+时间序
- **无 TBTL**：仅三推结构，不需要十棒两腿确认
- **评分**：楔形质量分 = 0.55（基础） + 位置适配 0.20 + 过渡期 0.15 + 衰竭风险 0.10
- **可选过渡优先**：`i_wedgeNeedTransition` 开启后仅过渡期/趋势弱化通过

### v3 三推背景识别（重大升级）
- **独立枢轴**：使用专用 pivot 数组（tpLeft=8, tpRight=4），与 V1.5 的 `isPH`/`isPL`(swN=5) 完全解耦
- **回撤分析**：两推之间调用 `findPullback()` 搜索最低/最高点，计算回撤深度 = (push2 - pb) / legRange
  - 最小深度：默认 25%（`i_pbMinDepth`）
  - 理想深度：默认 38%（`i_pbIdealDepth`），达标各得 50 分
- **回撤评分** `scorePullbacks()`：基础分(深度达标0-100) + 收敛加分(回撤递减时额外0-5分)
- **质量评分**（替代 V1.5 的对称/收口/跨度）：
  - 对称性 35%：两段 K 线间距比
  - 收敛性 35%：腿长度递减程度（d2 < d1）
  - 动量衰减 30%：第三推实体 vs 第一推实体
- **背景权重**：过渡期=1.0、区间边缘=0.8、趋势弱化=0.7、其他=0.3
- **严格模式** (`i_pbStrict`)：两段回撤均不达标→直接丢弃；关闭后按平均深度降级评分
- **趋势惩罚**：三推方向若与趋势强度同向，施加趋势惩罚分降低概率分

## 与相关概念的关系
- [[fsm-market-cycle]]：三推背景权重根据 FSM 阶段和过渡状态动态分配
- [[trend-strength-filter]]：趋势强度施加惩罚分压制同向三推，极强趋势可屏蔽三推
- [[playbook-engine]]：三推背景权重≥0.7 时触发 Playbook=4（过渡期反转）
- [[tri-push-background]]：背景层 v3 中三推作为成熟度/过渡证据的完整定位——与执行层三推检测是分层关系
- [[h2-l2-state-machine|H2/L2 State Machine]]：在 V1.5 中楔形与 H2/L2 共同构成结构来源，v3 中三推独立运作
- [[gravity-field]]：引力场为楔形提供位置环境验证（V1.5 特有，v3 用位置层替代）
- [[execution-layer]]：执行层设计中楔形是辅助路线（模块 C），优先级低于 H2/L2
- [[execution-engine-architecture]]：v3 执行引擎中楔形检测仅在 Execution Engine 内部运行（简化布尔判定），与 Context Engine 的三推回撤分析是不同模块
- [[execution-scoring]]：v3 楔形结构分的计算方式——fallingWedge/risingWedge + allowReversal + phaseIsTransition + exhaustRisk 累加
- [[background-permission]]：做多楔形候选 = fallingWedge AND allowReversalLong（反转许可，非 allowLong）；v2 首次实现此门控
- [[confluence-trading]]：下降楔形 + H2 同时触发 = 多头共振，各 +0.10 结构分

## 实战应用
- V1.5：楔形形成后不会立即入场，需分数达标、FSM 许可、收盘确认
- v3：三推背景不在 Pivot 确认柱才触发，而在每根 K 线实时扫描。关注信息面板「三推背景」行的顶部/底部提示和「三推回撤」的深度百分比——两段回撤均≥25%且第二段更深(收敛)是最可靠的三推信号
- [[expanding-triangle]]：扩散三角形可视为三推的"扩展版"——区别在于回撤更深（每次都超前一极值），而楔形是收敛的
- [[parabolic-wedge]]：抛物线楔形是 Brooks 最高频的楔形变体——与三推楔形（收敛）相反，抛物线楔形是"发散加速"型，趋势末端的恐慌性追涨/杀跌形成。代码中两者使用不同的检测逻辑

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：楔形三推检测 + 3 维质量评分（对称/收口/跨度）+ 5 项过渡证据之一 + 否决条件因子）
- [[article-20200818-brooks-10-best-pa-patterns]]（架构 #5：楔形——广义定义"任何 3-5 推倾斜模式"不必收敛；紧牛通道 3 次上涨=抛物线楔形=买入高潮→TR 或趋势反转；任何牛通道=熊旗 75% 跌破趋势线）
- [[article-wedge-gravity-v14-source]]（V1.4 Pine Script 第 287-401 行——三推楔形识别的原始实现：`f_wedgeOK` 校验函数、三维修正评分（对称40%+收敛35%+跨度25%）、5极点精确排序条件）
- [[article-wg-v15-analysis]]（V1.5 楔形——多维加权评分：对称性+收口+跨度）
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 楔形——纯 pivot 布尔判定 + 跨度约束，不做加权评分，是 V1.5 和 v3 之间的过渡实现）
- [[article-huangzongprice-execution-layer-v1]]（执行层 v1 中楔形的反转许可联动 + 评分模型）
- [[article-background-v3-upgrade]]（三推在背景层 v3 中的重新定位）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 采用简化检测）
- [[encyclopedia-al-10-best-setups]]（架构 #5：楔形——非规范变体、4-5推、抛物线楔形/高潮、连线规则）
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码第327-395行——三因子评分的完整 Pine Script 实现：`rw_symScore/rw_convScore/rw_spanScore` + `f_ratioScore` 归一化 + `f_clamp01` 钳位）
- [[article-20260519-wedge-gravity-v41-flowchart]]（V4.1 5点模式图 + 4项校验条件：时间交叉序列/空间对称(0.25-2.5)/时间对称(≤3倍)/收口斜率）
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]（V5.0 明确了三项评分权重：对称40%+收敛35%+跨度25%；`WedgeData` 类型定义）
- [[encyclopedia-al-10-best-setups]]（架构 #5：楔形——非规范变体、4-5推、抛物线楔形/高潮、连线规则）

### Brooks 原文的楔形变体补充（来自 Al 10 架构）
- **非教科书楔形**：空头通道往下推三次，即使没有楔形形态也算楔形——三推反转向市场发出反转信号
- **4-5 推变体**：楔形不限于严格三推，有时 4-5 推
- **抛物线楔形 = 买盘高潮**：飞升的抛物线楔形可能带来数小时的区间行情，也可能直接反转
- **关键反转信号**：抛物线楔形后出现突发的阴线（多头放弃棒）→ 反转概率大增
- **连线规则**：连接第一推低点和第三推低点，忽略第二推对楔形下沿的过冲
- **不必严格划线**：理解楔形的价格行为本质，就能找到更多变体

## 矛盾与待验证
- 楔形与 H2/L2 同时为真时，名称串显示 `WEDGE>H2` 等，但分数上并不「压掉」另一方——两者同时贡献 `structScore`。这种设计是否合理（是否应取 max 而非叠加）值得讨论。
- v3 的楔形检测比 V1.5 大幅简化：V1.5 有三项加权评分（对称/收口/跨度），v3 仅用布尔判定（三 pivot 位置+时间序+跨度范围）。简化版可能遗漏 V1.5 中得分较低但实际有效的楔形。
- v3 三推检测与 V1.5 楔形检测使用不同的枢轴参数（swN=5 vs tpLeft=8/tpRight=4），两者在同一图表上的检测结果可能不完全一致，需验证差异程度。
- 回撤评分的理想深度 38% 接近 Fibonacci 38.2% 回调位，但并非严格等于——将理想深度设为可调参数的设计优于硬编码 Fib。
- **书本 vs 实现差异（L3/H3 wedge: major_diff, wedge_flag: minor_diff）**： 发现 L3/H3 楔形的 5/5 维度均与 Brooks 原著不一致——趋势前提简化为 bear_or_TR_high/bull_or_TR_low、腿计数改为 `three_local_highs_wedge`（用斜率判定：高点斜率<0）、信号棒简化为"楔形末端阴/阳线"。而 wedge_flag 是仅有的 minor_diff 形态（2 个），趋势前提和腿计数与书本完全一致——仅市场背景/价位/信号棒有细节差异，说明旗形+楔形的量化实现最接近 Brooks 原著。L3/H3 wedge 的 `rs≈58` 风险限制在 5% 以内是纯实现层的工程决策，书本无对应。

### 书-码差异（来源：[[article-huangzongprice-pa-shape-audit]]）
**bear_l3_wedge（L3 楔形顶，major_diff，5 samples）**：
- 趋势前提：书本 `bear_trend_or_TR_high` → 代码 `bear_or_TR_high`
- 腿计数：书本 `three_push_up`（三推上涨）→ 代码 `three_local_highs_wedge`（多了斜率收敛条件：高点斜率<0，低点斜率>高点斜率）
- 市场背景：书本描述三高点处于同一阻力区域 → 代码限制「最高点不远离 EMA20，旗杆长度有限」

**bull_h3_wedge（H3 楔形底，major_diff，3 samples）**：
- 趋势前提：书本 `bull_trend_or_TR_low` → 代码 `bull_or_TR_low`
- 腿计数：书本 `three_push_down` → 代码 `three_local_lows_wedge`（低点斜率>0，高点斜率<低点斜率）
- 信号棒：书本「强阳线或向上突破楔形上轨」→ 代码仅「楔形末端阳线，实体中等以上」

**关键问题**：代码的楔形检测增加了斜率收敛条件，书本未提——是否导致部分 Brooks 认可的楔形未被代码识别？
