---
title: "Buy The Close / Sell The Close (BTC/STC)（已过时）"
phase: [trend, range, breakout, transition]
signal_types: [pullback-entry]
tags: [btc, stc, ail, ema, ais]
difficulty: intermediate
related: [btc-stc, always-in, climax, tbtl, brooks-signal-catalog, article-huangzongprice-pa-shape-audit, article-brooks-pa-verification, course-19-29-sr-basic-patterns]
char_count: 2142
---
> ⚠️ **已过时** — 本页已被 [[btc-stc]] 取代。请使用新页面。

# Buy The Close / Sell The Close (BTC/STC)（已过时）

## 一句话定义
强趋势中收盘价持续接近端点时的顺势追加入场信号——BTC 追多、STC 追空，不等待回调。

## 核心要点

### Brooks 原著定义
- **BTC (Buy The Close)**：市场进入 AIL（Always In Long）状态，多条连续强阳线，价格明显在 EMA20 上方，回调极浅。强阳线收盘接近最高点，直接市价买入。
- **STC (Sell The Close)**：市场进入 AIS（Always In Short）状态，多条连续强阴线，价格明显在 EMA20 下方，反弹极浅。强阴线收盘接近最低点，直接市价卖出。
- **核心思想**：趋势强劲到不需要等回调——"失望交易者"不断追入，推动价格持续单向运动。

### 实现规则（量化版本）
- **趋势前提**：`AIS_like` / `AIL_like`（量化替代 `always_in_short` / `always_in_long`）
- **腿计数**：`multi_strong_bear_bars` / `multi_strong_bull_bars`（≥3 根最近 K 线均为同向强 K）
- **市场背景**：价格在 EMA20 下方(空)/上方(多)，排除高潮 K
- **价位/形态关系**：收盘接近最低点/最高点，Bar range 不超过 2 ATR（防止高潮追入）
- **信号棒要求**：强阴线/强阳线，最近 ≥3 根 K 线为同向
- **额外过滤**：regime_penalty 在 climax_bear/climax_bull 中大幅降分——高潮附近禁止 BTC/STC

### 书本 vs 实现差异（major_diff）
| 维度 | 书本 | 实现 |
|------|------|------|
| 趋势前提 | always_in_short/long | AIS_like/AIL_like（量化近似） |
| 腿计数 | spike_or_SPB | multi_strong_bear/bull_bars（需≥3根） |
| 市场背景 | 多条连续强K线 | EMA20 方向 + 非高潮 |
| 价位/形态 | 明显在 EMA 一侧 | 收盘近端点 + range≤2ATR |
| 信号棒 | 收盘近端点即入场 | 需≥3 根最近同向K线确认 |

### 高风险信号——高潮附近禁用
- Brooks 原著明确警告：高潮附近应避免 BTC 追高 / STC 追空
- 实现通过 `regime_penalty` 在 `climax_bear` / `climax_bull` 中大幅降分来执行此规则
- 极端情况下（高潮实体 >1.8 ATR），TBTL 机制接管——需等待至少 10 根两腿冷却

## 与相关概念的关系
- [[always-in]]：BTC/STC 是 AIL/AIS 状态下的具体入场执行信号
- [[climax]]：高潮附近禁止 BTC/STC——这是 BTC/STC 最重要的风险管理规则
- [[tbtl]]：高潮后 TBTL 接管，BTC/STC 降级
- [[brooks-signal-catalog]]：BTC/STC 是 16 种白名单信号中的趋势延续类信号
- [[btc-stc]]：已有概念页，覆盖 BTC/STC 的突破测试与失望交易者机制

## 实战应用
- **适用场景**：强趋势确立（EMA20 斜率大、连续同向实体棒），回调极浅甚至无回调
- **禁止场景**：高潮末期（超大实体棒出现后）、TR 区间内
- **入场技巧**：信号棒收盘确认后立即市价入场，不设限价单——BTC/STC 的核心理念是"不等"
- **止损**：信号棒反向端点外 1 tick；趋势惯性大时可用更紧止损

## 来源支撑
- [[article-huangzongprice-pa-shape-audit]]（bear_stc / bull_btc 的书本-vs-实现对照）
- [[article-brooks-pa-verification]]（16 信号白名单中的 BTC/STC 定义）
- [[course-19-29-sr-basic-patterns]]（BTC/STC 与突破测试/失望交易者的关联）

## 矛盾与待验证
- 书本定义中 BTC/STC 只需"收盘接近端点"即可入场，实现增加了"≥3 根最近同向 K 线"的额外过滤——这是更保守的工程选择，可能过滤掉有效的早期趋势信号
- 实现的 `AIS_like`/`AIL_like` 量化规则能否准确替代 Brooks 的 AIS/AIL 主观判断，需回测验证
- `regime_penalty` 在高潮背景下降分幅度是否合适——过于保守可能错失强趋势中的 BTC/STC，过于激进可能在高潮末端追入
