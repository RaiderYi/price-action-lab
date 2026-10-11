# Wedge-Gravity V1.5（Brooks）分析逻辑全梳理

## 元信息
- 作者：huangzongprice
- 日期：未标注（与 V1.5.2 源码对齐）
- 原始位置：`raw/articles/huangzongprice/WG_V15_分析逻辑全梳理.md`
- 对应源码：`wedge_gravity_tradingview_brooks_v1.pine` / `wedge_gravity_tradingview_master_v2.pine`

## 一句话摘要
完整拆解 Wedge-Gravity V1.5 TradingView 脚本的逐根 K 线计算流水线，阐明硬规则（FSM 市场周期）与软评分（结构+K线+引力场）双核如何协同产出最终入场信号。

## 核心论点

### 1. 双核架构
- **A. 硬规则 FSM**：判定突破/通道/震荡/新突破四状态，给出 `allowLong`/`allowShort` 方向许可。优先级最高，不直接给入场价。
- **B. 软评分**：楔形/H2/L2 提供形态结构，引力场提供位置环境，K 线提供当根强弱，汇总为 `lFin`/`sFin`。

### 2. 计算流水线（自上而下）
```
基础 OHLC → FSM 传感器 → N-Bar 分型 → 市场周期 FSM →
三推楔形 → 引力场 → Brooks Step1-2 → H1/H2/L1/L2 状态机 →
信号 K 线分 → lFin/sFin → emergExit → FSM 许可 →
longBase/shortBase → Brooks Step4 否决 → 风控/绘图
```

### 3. FSM 状态转移
- 状态编码：`0=BREAKOUT`，`1=CHANNEL`，`2=TRADING_RANGE`，`3=NEW_BREAKOUT`
- 脚本从震荡(2)起步，`BREAKOUT(0)` 在运行中通常不会出现（代码无设 0 语句）
- 转移路径：rng2nbk → bo2ch → ch2rng → rng2nbk（循环）

### 4. 信号过滤链
结构成立 → 分数够 → FSM 允许 → 可选过滤（fail/olp/key/grade）→ Brooks Step4 否决 → 最终信号

### 5. 与纯 Brooks 手工分析的对应
| Brooks 四步 | 脚本中的对应 |
|------------|------------|
| 支撑/阻力 | 分型 ph/pl、唐奇安、EMA20、fib50、引力场、Step1 |
| 市场阶段 | FSM + brooksPhaseStr / 过渡 |
| 动能与健康 | avgOlp、emaSteep/Flat、K线分、楔形、emergExit、Step3 |
| 一票否决 | FSM 方向许可 + 可选过滤 + Brooks Step4 |

## 提取出的新概念
- [[wedge-gravity-dual-core]] — 双核架构（硬规则 + 软评分）
- [[fsm-market-cycle]] — FSM 市场周期四状态机
- [[three-push-wedge|Three Push Wedge]] — 三推楔形形态检测
- [[gravity-field]] — 高斯型引力场
- [[h2-l2-state-machine|H2/L2 State Machine]] — H2/L2 趋势结构状态机
- [[signal-scoring-synthesis]] — lFin/sFin 信号评分合成
- [[emergency-exit]] — 紧急逃生机制

## 关联已有概念
- [[atr-scaling]]：脚本中所有距离阈值均用 ATR 归一化
- [[al-brooks]]：Brooks 四步方法论在量化脚本中的实现
- [[bar-close-position]]：`longBase` 要求 `close > midPt`，即收盘在上半部
- [[brooks-signal-catalog]]：脚本实现了 Brooks 信号体系中的可计算子集

## 与现有知识的冲突
- 无直接冲突。本文是 Brooks 方法的具体量化实现，与已有纯理论概念页互补。需注意脚本并非价格行为课程的完整复刻，而是可计算子集 + 量化权重。
