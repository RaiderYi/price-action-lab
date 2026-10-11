---
title: "FSM 策略约束（FSM Strategy Constraints）"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, scalp, failed-breakout]
tags: [fsm, allowlong, allowshort, fsmdir, close]
difficulty: intermediate
related: [fsm-market-cycle, wedge-gravity-dual-core, background-permission, signal-scoring-synthesis, signal-reliability-pipeline, playbook, article-wedge-gravity-v14-source, article-wg-v15-analysis, article-background-v3-upgrade, emergency-exit, trading-range-quality, article-20260519-wedge-gravity-brooks-v1-pine]
char_count: 3917
---
# FSM 策略约束（FSM Strategy Constraints）

## 一句话定义
将 FSM 市场周期的四个状态翻译为精确的多空方向许可规则——硬规则核的下游消费者，决定每个状态允许做多/做空的具体条件与附加阈值。

## 核心要点

### 四状态许可矩阵

| FSM 状态 | 编码 | allowLong | allowShort | 核心原则 |
|----------|------|-----------|-----------|---------|
| BREAKOUT | 0 | `fsmDir == 1` | `fsmDir == -1` | 仅顺势，绝对禁止逆势 |
| NEW_BREAKOUT | 3 | `fsmDir == 1` | `fsmDir == -1` | 仅顺势，绝对禁止逆势 |
| CHANNEL（多头趋势） | 1 | `true` | `nearChanT ∧ sFin ≥ sigThr + 0.15` | 顺势全开；通道顶边界允许高分逆势剥头皮 |
| CHANNEL（空头趋势） | 1 | `nearChanB ∧ lFin ≥ sigThr + 0.15` | `true` | 顺势全开；通道底边界允许高分做多 |
| TRADING_RANGE | 2 | `nearDonchL` | `nearDonchH` | 仅唐奇安边界反向入场（假突破防御激活） |

### 边界判断条件

- **唐奇安边界**：`nearDonchH = close ≥ donchH − 0.5×ATR14`，`nearDonchL = close ≤ donchL + 0.5×ATR14`
- **通道边界**：`nearChanT = |close − ph0| < 1.5×ATR14`（通道顶），`nearChanB = |close − pl0| < 1.5×ATR14`（通道底）
- **逆势附加分**：通道状态下的逆势信号需要分数比默认阈值 `i_sigThr` 高 0.15 才能通过——保证逆势剥头皮只在极强信号下执行

### 设计哲学

1. **突破/新突破 → 绝对顺势**：动能最强阶段，逆势入场等同自杀。无例外、无附加条件。
2. **通道 → 顺势为主 + 边界高分散空**：顺势方向无条件放行；仅在通道极值边界（顶/底）且信号极强（≥ 阈值+0.15）时允许逆势剥头皮。
3. **震荡 → 仅边界反向入场**：假突破防御机制的核心——不在区间中部做任何交易，只在唐奇安上下轨做反向入场。这是区间策略的标准逻辑：在支撑买、在阻力卖。
4. **中性方向自动补全**：当 FSM 处于趋势状态但方向待定（`fsmDir==0`）时，用 `emaS3`（EMA 3 根斜率）补全方向——高位取多头，低位取空头。

## 与相关概念的关系

- [[fsm-market-cycle]]：FSM 是本约束的上游数据源——周期状态和方向由此输入；本页是 FSM 的下游消费者，将状态翻译为可交易方向
- [[wedge-gravity-dual-core]]：本约束是双核架构中「硬规则核」的代码落地——FSM 给出状态，本约束将状态翻译为 allowLong/allowShort
- [[background-permission]]：V5.0 已从本页的四状态许可升级为六状态背景许可（否决/多强/多可/空强/空可/中性），并整合了更多过滤维度
- [[signal-scoring-synthesis]]：通道逆势剥头皮需要 lFin/sFin ≥ sigThr+0.15——信号评分是本约束的联动过滤器
- [[signal-reliability-pipeline]]：本约束的 `allowLong/allowShort` 是信号可靠性管道中最下游的闸门之一——即使信号通过了所有 7 层过滤，方向被 FSM 屏蔽则不入场
- [[playbook]]：v3 将本约束从二元许可升级为 6 种玩法状态分发——禁止逆势 / 区间反转 / 过渡反转 / 突破延续 / 回调再入 / 中继突破

## 实战应用

调试时若发现明明有信号但未触发入场：先检查 `allowLong`/`allowShort`——是否当前 FSM 周期状态屏蔽了该方向。常见原因：
- 震荡区间中段出现 H2/L2 信号 → 被 `nearDonchH/L` 过滤
- 突破阶段出现反转楔形 → 被 `breakout only with trend` 屏蔽
- 通道中部出现顺向信号 → 已通过（顺势无条件开放）

## 来源支撑
- [[article-wedge-gravity-v14-source]]（V1.4 Pine Script 第 643-678 行——FSM 策略约束的完整实现，含边界判断和逆势附加阈值）
- [[article-wg-v15-analysis]]（V1.5 分析中策略约束的首次描述）
- [[article-background-v3-upgrade]]（v3 过渡到 Playbook 6 状态分发的设计动机）

## 矛盾与待验证
- 通道逆势剥头皮 +0.15 阈值是作者经验值，未经过系统性回测优化。不同品种/周期的最优附加分可能不同。
- V5.0 中本约束的通道逆势规则被 `background-permission-gating` 的六状态系统替代，但两套系统对同一边界信号的判定结果是否一致，尚无对比验证。


---

## Merged Content (from fsm-strategy-constraint)

# FSM 策略方向约束

## 一句话定义
根据 FSM 市场周期四状态，动态决定 `allowLong`/`allowShort` 两个布尔许可——不同周期状态下允许的交易方向完全不同。

## 核心要点
- **突破/新突破阶段**（fsm == 0 or 3）：**仅允许顺势方向**。多头周期下 `allowShort = false`（绝对禁止逆势做空），空头反之。
- **通道阶段**（fsm == 1）：**顺势为主 + 边界高分逆势剥头皮**。多头通道中 `allowLong` 始终为 true；`allowShort` 仅在靠近通道顶（`nearChanT`）且空头评分 ≥ 阈值+0.15 时允许。
- **震荡区间**（fsm == 2）：**仅唐奇安边界反向入场**。`allowLong` 仅在下轨附近（`nearDonchL`），`allowShort` 仅在上轨附近（`nearDonchH`）——这是假突破防御的核心机制。
- **边界判定标准**：通道顶 = `|close - ph0| < 1.5×ATR14`，唐奇安上下轨 = `|close - donch| < 0.5×ATR14`
- **许可状态在面板可见**：右上角信息面板第 16/17 行实时显示 `✓ 允许做多/做空` 或 `✗ 当前周期屏蔽`
- **与信号评分独立**：即使 `lFin >= 0.80`（A 级信号），如果 `allowLong == false`（例如突破阶段做逆势多），信号仍不会触发

## 与相关概念的关系
- [[fsm-market-cycle]]：FSM 状态是方向约束的唯一输入——状态一变，许可立变
- [[signal-scoring-synthesis]]：`allowLong`/`allowShort` 是 `longBase`/`shortBase` 的必备条件之一（与结构触发 + 评分阈值 + 收盘位置并列）
- [[background-permission]]：Brooks Step4 否决是「背景层否决」，方向约束是「周期层否决」——两层独立叠加
- [[emergency-exit]]：紧急逃生触发不影响方向约束，但可通过 Step4 否决链拦截信号
- [[trading-range-quality]]：TR 中仅在边界交易的约束是实现 80% 法则（区间中突破失败 80%）的量化手段

## 实战应用
看右上角面板「多头/空头策略许可」行——绿色 ✓ 表示当前 K 线可以做该方向。TR 下轨出现 H2 信号 + allowLong = ✓ → 高概率做多；TR 中间出现 H2 但 allowLong = ✗ → 忽略。

## 来源支撑
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — Pine Script 源码，第 726–759 行定义完整的方向约束逻辑

## 矛盾与待验证
- **通道逆势剥头皮的门槛**：`lFin >= i_sigThr + 0.15` 的 0.15 额外分是经验值，未经回测优化
- **TR 仅边界交易 vs Brooks 原著**：Brooks 原著允许 TR 中间做 scalping，本系统完全禁止——这是「安全优先」的工程选择，可能牺牲部分交易机会
- **方向约束在路径 A（激进突破）时可能滞后**：Path-A 在当根 K 线立即转换到 NEW_BREAKOUT，但方向约束用的是转换后的 fsmDir——如果转换的瞬间 fsmDir 尚未稳定，可能导致短暂的方向误判
