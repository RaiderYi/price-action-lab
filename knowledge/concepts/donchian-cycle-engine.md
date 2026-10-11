---
title: "唐奇安通道周期引擎"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, wedge, breakout-entry, pullback-entry]
tags: [path, atr, 突破, fsm, brkcnt]
difficulty: intermediate
related: [fsm-market-cycle, breakout-mechanics, gravity-field, trading-range-quality, article-huangzongprice-wedge-gravity-v5-cycle-structure]
char_count: 2687
---
# 唐奇安通道周期引擎

## 一句话定义
用 N 期唐奇安通道（Donchian Channel）作为震荡→新突破的边界，通过 Path A（大实体突破）和 Path B（连续收盘越界）两条路径触发周期状态转移，并用 K 线重叠度均值动态调节各状态置信度。

## 核心要点

### Path A：大实体突破（一次性触发）
- **条件**：实体 > `i_brkMul`（默认 1.5）×ATR20，收盘超越前唐奇安边界 + `i_brkOff`（默认 0.5）×ATR20 偏离，且高点/低点穿越当前唐奇安
- **多头方向**：`barBody > 1.5×ATR20 AND close > donchHPrev + 0.5×ATR20 AND high ≥ donchH`
- **空头方向**：`barBody > 1.5×ATR20 AND close < donchLPrev - 0.5×ATR20 AND low ≤ donchL`
- **触发后**：`fsm→3(NEW_BREAKOUT)`，`fsmDir→±1`，`fsmConf→0.90`

### Path B：连续收盘越界（累积触发）
- **机制**：震荡状态下，连续跟踪收盘价是否每次越过唐奇安前值
  - 每次同向越过：`brkCnt += 1`
  - 方向反转：`brkCnt = 1`（重新计数）
  - 未越过：`brkCnt = 0`（重置）
- **触发条件**：`brkCnt ≥ 3`（连续 3 根 K 线收盘越界）
- **退出震荡后**：`brkCnt` 清零，防止残留计数干扰

### 重叠度置信度调节
不用转移时，FSM 处于稳定状态——用 K 线重叠度均值和 EMA 斜率更新置信度：

| 当前状态 | 高置信条件 | 高置信值 | 默认值 |
|---------|-----------|---------|-------|
| 突破(0) / 新突破(3) | avgOlp < 0.20 + emaSteep | 0.90 | 0.65 |
| 通道(1) | emaSteep + not emaFlat | 0.75 | 0.50 |
| 震荡(2) | emaFlat | 0.80 | 0.50 |

重叠度计算：`olpRt = max(0, min(close[1], close) - max(open[1], open)) / barBody`，然后对 `i_olpLen`（默认 5）窗口取 SMA。

### 转移路径总结
```
      突破(0) ──bo2ch──→ 通道(1) ──ch2rng──→ 震荡(2)
        │                                          │
        └──────────bo2ch──────────→                │
                                                   │
              震荡(2) ──rng2nbk(Path A/B)──→ 新突破(3)
                                                   │
              新突破(3) ──bo2ch──→ 通道(1)          │
```

**通道→新突破 无直接路径**：须先经 `ch2rng` 回震荡(2)，再由震荡通过 Path A 或 Path B 进新突破(3)。

### EMA 斜率传感器
- `emaS3 = ema20 - ema20[3]`（3 期变化量）
- `emaS10 = ema20 - ema20[10]`（10 期变化量）
- `emaSteep = |emaS3| > 0.5 × ATR20`（短期变化显著）
- `emaFlat = |emaS10| < 0.5 × ATR20`（中期变化平缓）

## 与相关概念的关系
- [[fsm-market-cycle]]：唐奇安引擎是 FSM 状态转移的具体实现机制——定义了何时以及如何从震荡→新突破
- [[breakout-mechanics]]：Path A（大实体突破）对应 Brooks 理论中的"突破→回调→恢复"步骤中的"突破"阶段；Path B（连续收盘越界）对应"持续突破"的量化实现
- [[fsm-market-cycle]]：唐奇安通道替代了 Brooks 理论中"肉眼判断突破"的主观环节，用数值化边界使震荡→突破的判定可编程
- [[gravity-field]]：V5.0 中引力场独立于唐奇安引擎运行，两者是并行的位置评估维度——唐奇安判突破，引力场判值得交易
- [[trading-range-quality]]：唐奇安引擎的震荡状态(2)与区间质量概念互补——前者判断"是否在区间"，后者评估"区间的可交易性"

## 实战应用
- 在信息面板关注「市场周期」和「置信度/R²」两行——当周期=震荡(2)且置信度≥0.80 时，等待 Path A 或 Path B 触发新突破
- Path B 是更可靠的突破信号（三次收盘确认），但响应速度慢于 Path A（一次大实体突破）
- 重叠度均值 < 0.20 是强趋势的可靠指标——此时不应逆势

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]

## 矛盾与待验证
- Path B 的 3 根连续收盘阈值是经验参数（`brkCnt >= 3`），不同品种/周期可能需要调优。A 股 30min 周期上该值是否合适尚需回测验证。
- 重叠度置信度调节中，突破(0)和新突破(3)共用同一套条件——但两者的市场含义不同（0 是初始突破、3 是区间结束后再突破），是否应区分对待？
- `fsm=0`（BREAKOUT）在 V5.0 中只能在初始化时或通过 `bo2ch` 进入（且 `bo2ch` 的前置条件是 fsm in {0,3}），Path A/B 都要求 fsm==2。这意味着从初始化后首次进入突破/新突破状态后，fsm=0 确实变为"可访问但极少进入"的状态——与 V1.5 分析中的"死分支"结论存在微妙差异。
