---
title: "动态风控参数（Dynamic Risk Control）"
phase: [trend, range, breakout]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, swing, failed-breakout]
tags: [atr, risk, ent, entbuf, stopbuf]
difficulty: intermediate
related: [trade-management-system, atr-scaling, h2-l2-state-machine, signal-priority-system, position-sizing, article-wedge-gravity-v14-source, article-20260519-wedge-gravity-v41-flowchart, trader-equation]
char_count: 2363
---
# 动态风控参数（Dynamic Risk Control）

## 一句话定义
WG Brooks V4.1 的入场前风控公式——用 ATR 缓冲 + 结构极值计算入场价(ENT)、止损价(SL)和止盈价(TP)，所有参数实时基于当前 K 线动态生成。

## 核心要点

### 缓冲参数
```
stopBuf = max(mintick, 0.5 × ATR20)    // 止损缓冲
entBuf  = max(mintick, 0.1 × ATR14)    // 入场缓冲
```

### 做多风控公式
```
SL  = majorSL - stopBuf          // 最近波段低点 - 止损缓冲
ENT = high + entBuf              // 当前K线高点 + 入场缓冲
Risk = max(ENT - SL, 0.5 × ATR14)  // 风险幅度（不低于0.5倍ATR保底）
TP  = ENT + 2.0 × Risk           // 止盈 = 入场 + 2倍风险
```

### 做空风控公式
```
SL  = majorSH + stopBuf          // 最近波段高点 + 止损缓冲
ENT = low - entBuf               // 当前K线低点 - 入场缓冲
Risk = max(SL - ENT, 0.5 × ATR14)  // 风险幅度（不低于0.5倍ATR保底）
TP  = ENT - 2.0 × Risk           // 止盈 = 入场 - 2倍风险
```

### 关键设计原则
- **止损基于结构极值**：做多取最近波段低点(majorSL)，做空取最近波段高点(majorSH)——而非固定点数或固定ATR倍数
- **入场缓冲**：entBuf 很小（0.1×ATR14），在突破确认的 K 线外微微偏移，避免滑点和假突破
- **1:2 盈亏比**：TP = ENT ± 2.0×Risk，目标盈亏比严格为 2:1
- **保底风险**：Risk 不低于 0.5×ATR14——防止极窄幅震荡中风险过低导致仓位过大

### 与交易管理的区别
| 维度 | 动态风控（本文） | 交易管理体系 |
|------|---------------|------------|
| **时机** | 入场前，信号生成时同步计算 | 入场后，持仓期间持续管理 |
| **内容** | ENT/SL/TP 初始参数 | BE移动/追踪止损/时间止损/失败出场 |
| **输入** | 当前K线 + 结构极值 + ATR | 持仓状态 + 价格走势 + 时间 |
| **对应概念** | ← 本文 → | [[trade-management-system]] |

## 与相关概念的关系
- [[trade-management-system]]：动态风控提供入场时的初始 SL/TP，交易管理系统在入场后接管——初始止损 → BE → 追踪止损的完整生命周期
- [[atr-scaling]]：stopBuf 和 entBuf 均以 ATR 倍数标定，是 ATR 归一化在风控维度的应用
- [[h2-l2-state-machine|H2/L2 State Machine]]：majorSL/majorSH 的取值来源——波段极值由 H/L 计数状态机追踪
- [[signal-priority-system]]：动态风控在 Level 5 信号确认后立即触发，是信号生成→执行的最后一步
- [[position-sizing]]：Risk = ENT - SL 是仓位计算公式的输入——仓位 = 账户风险金额 / Risk

## 实战应用
在图表上，信号触发时标签会同时显示三条参考线：
- 绿色虚线 = ENT（入场价）
- 红色虚线 = SL（止损价）
- 蓝色虚线 = TP（止盈价）

这三条线的位置直接告知交易者该信号的"性价比"——如果 SL 过宽（Risk 过大），则该信号即使分数达标，实际仓位会很小（仓位 = 风险金/Risk）。

## 来源支撑
- [[article-wedge-gravity-v14-source]]（V1.4 Pine Script 第 706-715 行——动态风控的原始实现：stopBuf(0.5×ATR20) + entBuf(0.1×ATR14) + 1:2 盈亏比 ENT/SL/TP 公式）
- [[article-20260519-wedge-gravity-v41-flowchart]]（V4.1 中相同公式的架构文档描述）

## 矛盾与待验证
- **1:2 盈亏比固定**：Brooks 原教旨主义不主张固定 R:R——他更关注"市场给你多少就拿多少"（见 [[trader-equation]]）。此处的 2.0×Risk 是量化系统的强制设定，可能与某些信号的"自然目标"不符（如量度目标只有 1.2×Risk）
- **entBuf 基于 ATR14 而非 ATR20**：stopBuf 用 ATR20，entBuf 用 ATR14——两个缓冲使用不同周期的 ATR，原因未在文档中说明（可能因为入场缓冲更关注近期波动，止损需要更长周期稳定性）
- **Risk 保底 0.5×ATR14**：在极窄幅震荡中，如果 ENT-SL < 0.5×ATR14，Risk 被强制拉高到 0.5×ATR14，这会使 TP 线也相应拉远——可能导致止盈目标在震荡区间中难以触及
