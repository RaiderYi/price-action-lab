---
title: "FSM 市场周期"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, scalp, swing, failed-breakout]
tags: [fsm, 通道, 突破, breakout, 震荡]
difficulty: intermediate
related: [wedge-gravity-dual-core, cycle-strategy-gating, donchian-cycle-engine, gravity-field, emergency-exit, h2-l2-state-machine, playbook-engine, trend-strength-filter, playbook, article-20260520-wedge-gravity-brooks-context-v3, article-wg-v15-analysis, article-huangzongprice-wedge-gravity-v2-master, article-background-v3-upgrade, article-huangzongprice-v3-phase1, article-huangzongprice-context-engine-v2, article-20250519-brooks-context-4-pine, article-20250519-brooks-pa-execution-engine-v1, article-huangzongprice-context-engine-v1, article-huangzongprice-wedge-gravity-v5-cycle-structure, article-wedge-gravity-v14-source, article-huangzongprice-context-engine-v3-rebuild, fsm-strategy-constraints, fsm-market-cycle, channel-to-trading-range, market-structure, breakout-mechanics, eighty-percent-rule, always-in, buy-sell-zones, default-profit-targets, buy-vacuum-sell-vacuum, course-notes-12-18-market-cycle, course-37-42-trading-trends, encyclopedia-brooks-price-action-manual]
char_count: 6262
---
# FSM 市场周期

## 一句话定义
用有限状态机（FSM）将市场划分为四个周期状态，每根 K 线最多发生一次状态转移，并持续更新周期置信度。

## 核心要点
- **四状态编码**：`0=BREAKOUT`，`1=CHANNEL`，`2=TRADING_RANGE`，`3=NEW_BREAKOUT`
- **初始化**：从震荡(2)起步，BREAKOUT(0)在运行中通常不会出现
- **三条转移路径**（每根最多触发一条）：
  1. `rng2nbk`（震荡→新突破）：大实体+收盘越唐奇安 或 连续3根边界外
  2. `bo2ch`（突破→通道）：逆势回调K，振幅≥1×ATR20
  3. `ch2rng`（通道→震荡）：强实体+极强收盘+突破最近分型
- **CHANNEL→NEW_BREAKOUT 无直接路径**：须先经 `ch2rng` 回震荡，再 `rng2nbk`
- **无转移时**：按当前状态用 `avgOlp`、`emaSteep`、`emaFlat` 更新置信度 `fsmConf`

### v3 新增：过渡检测系统
- **5 种过渡信号**（每根 K 线独立评估）：
  1. `transitionByOverlap`：重叠度均值 > 0.32
  2. `transitionBySlopeLoss`：EMA3斜率不足 或 EMA10平坦
  3. `transitionByBroadChannel`：通道阶段 + 重叠度 > 0.24 + 置信度 < 0.72
  4. `transitionByWedge`：检测到上升楔形或下降楔形
  5. `transitionByFailedBreakout`：最近 3 根有突破分型但收盘失败(brkFail_EMG)
- **过渡判定**：`transitionCount ≥ 2` 或 通道+高重叠(olp>0.30) 或 新突破+假突破失败
- **阶段健康分类**（v3 新增）：
  - `phaseTrendHealthy`：趋势状态 + 置信度≥0.70 + EMA陡峭 + 低重叠 + 非过渡
  - `phaseTrendWeakening`：趋势状态 + ≥1个过渡信号 + (高重叠 或 非EMA陡峭)
  - `phaseTwoSided`：震荡 或 过渡 或 重叠度 > 0.35

## 与相关概念的关系
- [[wedge-gravity-dual-core]]：FSM 是双核架构中的硬规则核
- [[cycle-strategy-gating]]：FSM 状态 → allowLong/allowShort 三级门控——FSM 的下游消费者，V2 Master 首次完整实现
- [[donchian-cycle-engine]]：V5.0 中 FSM 的震荡→新突破转移由唐奇安通道引擎的 Path A/B 路径驱动
- [[gravity-field]]：引力场权重之一 `emaSteep`/`emaFlat` 由 FSM 传感器提供
- [[emergency-exit]]：紧急逃生与 FSM 方向许可共同构成信号否决层
- [[h2-l2-state-machine|H2/L2 State Machine]]：H2/L2 是独立于 FSM 的另一套状态机，在软评分层运作
- [[playbook-engine]]：背景层 v3 中 FSM 的 `phaseState` 是 Playbook 判断的核心输入——趋势/震荡/过渡/新突破直接决定 playbookState
- [[trend-strength-filter]]：趋势强度过滤独立于 FSM，但过渡检测的多信号触发可能预示趋势弱化
- [[playbook]]：Playbook 状态 1/2/3 以 FSM 阶段状态为核心判断依据

## 实战应用

### V1.4 策略约束（精确规则）
FSM 通过 `allowLong`/`allowShort` 控制各周期状态下的交易方向许可：

| 周期状态 | allowLong | allowShort | 条件 |
|---------|-----------|-----------|------|
| BREAKOUT (0) | `fsmDir == 1` | `fsmDir == -1` | 仅顺势，无例外 |
| NEW_BREAKOUT (3) | `fsmDir == 1` | `fsmDir == -1` | 仅顺势，无例外 |
| CHANNEL (1) | `true`（顺势） | `nearChanT ∧ sFin ≥ sigThr + 0.15`（逆势） | 通道顶才允许高分散空 |
| CHANNEL (1) 空头 | `nearChanB ∧ lFin ≥ sigThr + 0.15`（逆势） | `true`（顺势） | 通道底才允许高分做多 |
| TRADING_RANGE (2) | `nearDonchL` | `nearDonchH` | 仅在唐奇安上下轨反向入场 |

其中：
- `nearDonchH/L`：收盘距唐奇安上/下轨 ≤ 0.5×ATR14
- `nearChanT/B`：收盘距最近 ph0/pl0 ≤ 1.5×ATR14
- 通道逆势附加分：+0.15 阈值——意味着逆势信号需要比默认阈值高 0.15 才能通过

**与 fsml 概述的对应**：
- 突破/新突破：仅顺势 ✓
- 通道：顺势全开，逆势仅在顶/底 ✓（附加精确阈值）
- 震荡：仅唐奇安边界附近 ✓

## 来源支撑
- [[article-20260520-wedge-gravity-brooks-context-v3]]（V3 源码：FSM 完整实现含 3 条转移路径精确条件 + 置信度动态更新规则）
- [[article-wg-v15-analysis]]
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码第196-323行——FSM 的完整状态机实现：5个持久化变量、3条硬规则转移 + Path-A/B 双路突破 + 4种状态置信度更新公式）
- [[article-background-v3-upgrade]]（FSM 阶段状态是 Playbook 判断的核心输入）
- [[article-huangzongprice-v3-phase1]]（v3 过渡检测 + 阶段健康分类）
- [[article-huangzongprice-context-engine-v2]]（v2 保留 FSM 核心逻辑 + 5 信号过渡检测 + transitionCount 累计判定）
- [[article-20250519-brooks-context-4-pine]]（Step2 市场阶段：FSM → brooksPhaseStr + ctx2_score + 过渡检测 donchWiden）
- [[article-20250519-brooks-pa-execution-engine-v1]]（v1 执行引擎：FSM 内嵌，transition 由 avgOlp+emaSteep/Flat+phaseState 联合判定）
- [[article-huangzongprice-context-engine-v1]]（v1 standalone FSM：独立持久化变量，`fsm=0` 通过 bo2ch 可达，不同于 WG_V15 的死分支）
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]（V5.0 唐奇安通道周期引擎：Path A/B 双路径 + 重叠度置信度调节）
- [[article-huangzongprice-context-engine-v1]]（v1 standalone FSM：独立持久化变量，`fsm=0` 通过 bo2ch 可达，不同于 WG_V15 的死分支）
- [[article-wedge-gravity-v14-source]]（V1.4 源码第157-281行——FSM 的完整 Pine Script 实现，含硬规则转换 + 置信度评分 + Path-A/Path-B 双路径突破）
- [[article-huangzongprice-context-engine-v3-rebuild]]（V3 Clean Rebuild 源码第150-237行——FSM完整实现：bo2ch/ch2rng/rng2nbk转移+Path-A实体倍数Path-B连续计数+动态置信度调节）
- [[fsm-strategy-constraints]]：FSM 策略约束——FSM 的下游消费者，将状态翻译为允许的交易方向

## v1 Context Engine FSM 与 WG_V15 的差异
- **持久化方式**：v1 使用 `var int fsm`、`var int fsmDir`、`var float fsmConf`、`var int brkCnt`、`var bool brkUp` 五个持久化变量跨 Bar 维护状态；WG_V15 FSM 状态管理方式不同（需对照源码）
- **`fsm=0` 的存活性**：v1 中 `bo2ch` 将状态设为 0，故 `fsm=0` 是可达的；WG_V15 中 `fsm=0` 被标记为「死分支」
- **过渡检测**：v1 使用 5 信号计数（≥2 触发）+ 通道高重叠 + 新突破假突破失败；WG_V15 v3 也使用 5 信号但信号类型和逻辑不同（vk vs 是否同源）
- **阶段健康分类**：两版本逻辑相似（趋势健康/弱化/双向），但阈值和权重参数独立配置

## 与 Brooks 原始理论的对应
- 四状态映射：突破=Breakout，通道=Tight+Broad Channel 合并，震荡=Trading Range，新突破=新周期开始
- 简化取舍：Brooks 原始理论区分窄通道和宽通道（见 [[fsm-market-cycle]]），FSM 将其合并——因代码实现中两者通过信号评分间接区分
- [[channel-to-trading-range]]：FSM 未显式建模通道→区间的过渡信号（限价单/止损单逆势者盈利），这是原始理论中的重要机制

## 矛盾与待验证
- 四状态定义（0/1/2/3）中，脚本无任何语句设 `fsm=0`，BREAKOUT 为死分支。这是量化简化还是有意设计，需对照 V2 Master 版本确认。


---

## Merged Content (from market-cycle)

# 市场周期

## 一句话定义
市场永远在「突破 → 窄通道 → 宽通道 → 交易区间 → 突破」的无限循环中运行，每部分对应一种唯一正确的交易方式。

## 核心要点

### 多头一侧（四形态）
| 形态 | 特征 | 唯一交易方式 |
|------|------|------------|
| 多头突破 (Bull Breakout) | 无回调或仅1-2棒微型回调；止损远、风险大；概率高 | 只买，波段或刮头皮 |
| 窄多头通道 (Tight Bull Channel) | 回调仅1-3棒；高时间框架上看是突破；总在场内多头 | 只买，波段优先 |
| 宽多头通道 (Broad Bull Channel) | 有空头腿强到可反转；回调可达2/3幅度 | 主要买（回调买进），空头可在新高刮头皮 |
| 交易区间 (Trading Range) | 80%突破失败；多头低买、空头高卖 | 低买高卖刮头皮 (BLSHS) |

### 空头一侧（对称镜像）
完全对称——空头突破/窄空头通道/宽空头通道/交易区间，方向相反。

### 循环机制
```
突破（趋势开始，最强部分）
  └→ 出现回调 → 通道阶段开始
       └→ 逆势交易者开始赚钱（限价单 → 止损单）
            └→ 演变成交易区间
                 └→ 区间突破 → 新趋势开始（回到突破）
```

### 关键洞察
- **所有回调都是较小时间框架上的交易区间**，所有交易区间都是较高时间框架上的回调
- **通道 = 弱趋势**：突破是强趋势，通道是弱趋势，交易区间是无趋势
- **周期中每部分都有交易机会**——关键在于知道自己在周期中的位置，采取匹配的策略
- 小交易区间（<20棒）在趋势中 = 回调，趋势大概率恢复；大交易区间（≥20棒）= 先前趋势失去影响力，市场进入突破模式

## 与相关概念的关系
- [[market-structure]]：市场结构是趋势 vs 交易区间的粗分法；市场周期是对趋势内部的精细拆分（突破 → 窄通道 → 宽通道）
- [[fsm-market-cycle]]：FSM 四状态机是本概念的代码化实现，但将窄/宽通道合并为单一"通道"状态
- [[breakout-mechanics]]：突破是本周期中的第一种形态（趋势最强部分）
- [[eighty-percent-rule]]：80% 法则分别作用于趋势阶段（抑制反转）和区间阶段（抑制突破）
- [[channel-to-trading-range]]：周期中通道→区间的过渡机制
- [[always-in]]：窄通道中 Always In 方向明确；宽通道中开始模糊；区间中不明确
- [[buy-sell-zones]]：不同周期位置→不同的买卖区域规则
- [[default-profit-targets]]：不同周期位置→不同的利润目标预期
- [[buy-vacuum-sell-vacuum]]：S/R 的磁吸效应是推动周期中突破→区间演变的核心力学机制

## 实战应用
看任何一张图表时，先问：当前处于周期的哪个位置？如果是突破—只做顺势；如果是窄通道—顺势回调入场；如果是宽通道—顺势为主但允许对手刮头皮；如果是区间—只做边界反转。

## 来源支撑
- [[course-notes-12-18-market-cycle]]（Slide 2-27）
- [[course-37-42-trading-trends]]（视频37A/B：市场周期的"How to Trade"实操篇）
- [[encyclopedia-brooks-price-action-manual]]（完整市场周期章节，含真空效应和通道→区间演变机制）

## 矛盾与待验证
- Brooks 的四形态划分与 [[fsm-market-cycle]] 的三状态简化（突破/通道/震荡）之间的差异——合并窄/宽通道是否丢失了交易决策中的重要信息？
- 周期的"起点"是任意的——市场总是在循环中，任何突破同时也是上一个周期的终点
