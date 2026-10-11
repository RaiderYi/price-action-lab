# Brooks「分析背景」四步法 — Pine 脚本对照表

## 元信息
- 作者：huangzongprice
- 日期：未标注（与 WG V1.5.2 脚本对齐）
- 原始位置：`raw/articles/huangzongprice/BROOKS_CONTEXT_4_PINE.md`
- 关联脚本：
  - `wedge_gravity_tradingview_brooks_v1.pine`（由 `wedge_gravity_tradingview_fixed_v2.txt` V1.4 扩展）
  - `wedge_gravity_tradingview_master_v2.pine`（整理优化版）
- 完整分析逻辑参考：`WG_V15_分析逻辑全梳理.md`

## 一句话摘要
将 Brooks「分析背景」四步法（价位→阶段→动能→否决）量化为 Pine Script 可计算的 0-1 评分流水线，实现从定性理论到量化过滤的工程化落地。

## 核心论点

### 总开关设计
- `i_useBrooks4`：关闭时四步分数为 0、面板显示「关」，但 FSM/引力/原逻辑继续运行——可独立切换上下文过滤
- `i_brooksVetoHard`：控制 Step4 是否实际拦截信号，关闭时仅面板展示否决文案不拦截
- `i_alertOnClose`（仅 V2 Master）：警报条件与 `barstate.isconfirmed` 合取，减少盘中重复误报

### 四步流水线

| 步骤 | 教材问题 | Pine 实现 | 输出 |
|------|---------|-----------|------|
| Step1 支撑阻力 | "市场在什么价位？" | 显著高低点 ph0/pl0、ph1/pl1、唐奇安 donchH/donchL、EMA20、区间 50% fib50、测量移动 mmTargetBrooks、整数关口 nearestRound | `ctx1_score` (0-1), `ctx1_note` |
| Step2 市场阶段 | "趋势/震荡/过渡？" | FSM 状态机 `fsm` + `fsmDir`、过渡检测 `brooksTransition`（ema变平 + 唐奇安宽度扩张 donchWiden） | `ctx2_score`, `brooksPhaseStr` |
| Step3 动能健康 | "动能如何？" | 重叠度 avgOlp、均线斜率 emaSteep/emaFlat、紧急/衰竭 emergExit、实体强度、楔形标记 | `ctx3_score`, `ctx3_note` |
| Step4 一票否决 | "是否应放弃？" | TR 位置否决 vetoTRlong/vetoTRshort、紧急逃生顺势否决 vetoEmergL/vetoEmergS | `brooksVetoTxt` → 最终信号 `longSig`/`shortSig` |

### 入场标签增强（V1.5）
当 `i_useBrooks4` 开启且信号触发时，入场标签添加：`Brooks: {brooksPhaseStr} ·①{ctx1_score} ③{ctx3_score}`

### 缩放防错位方案（V1.5.2）
- `xloc.bar_time` 统一时间坐标
- `force_overlay=true` 所有绘制锚定主图
- 分型标记/FSM标签/入场标签改用 `yloc.abovebar`/`yloc.belowbar` 相对锚定

## 提取出的新概念
- [[brooks-four-step-context]] — Brooks 四步上下文分析框架（Step1-4 完整流水线）
- [[ctx-scoring]] — 上下文评分量化系统（ctx1/ctx2/ctx3 的 0-1 评分规则）

## 与已有概念的衔接
本文是 Brooks 上下文分析的 **Pine Script 工程化落地**，与以下已有概念形成理论→量化的映射链：
- [[support-resistance|Support/Resistance]] ← Step1 的 S/R 检测（显著高低点、唐奇安、50%回撤、整数关口、测量移动）
- [[fsm-market-cycle]] ← Step2 的市场阶段判定（FSM 四状态 + 过渡检测）
- [[wedge-gravity-dual-core]] ← 整体架构：FSM硬规则 + ctx评分软过滤的双核设计
- [[signal-scoring-synthesis]] ← ctx评分与信号评分的互补关系（上下文分 vs K线分）
- [[emergency-exit]] ← Step3 动能衰竭检测 + Step4 否决系统
- [[three-push-wedge|Three Push Wedge]] ← Step3 楔形标记（在 `ctx3_note` 中追加「·楔形」）
- [[h2-l2-state-machine|H2/L2 State Machine]] ← Step2 作为趋势结构的二级状态源

## 与现有知识的冲突
- 无直接冲突。本文的 ctx 评分体系与 [[signal-scoring-synthesis]] 的 lFin/sFin 信号评分是**互补关系**（上下文 vs 信号质量）而非替代关系。两套评分在 Pine Script 中可独立开关（`i_useBrooks4` vs 原信号评分），体现了双核架构的模块化设计意图。
- Step4 的 veto 系统与 [[emergency-exit]] 有功能重叠（都包含 emergExit 检测），但定位不同：emergency-exit 是动能层面的紧急信号，Step4 veto 是整合了 TR 位置 + 紧急逃生的最终拦截闸。
