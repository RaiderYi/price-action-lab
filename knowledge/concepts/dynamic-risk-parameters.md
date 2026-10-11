---
title: "动态风控参数（Dynamic Risk Parameters）"
phase: [range, breakout, transition]
signal_types: [h2-entry, l2-entry, pullback-entry, swing, failed-breakout]
tags: [atr, 入场, 止损, max, 风险]
difficulty: intermediate
related: [protective-stops, execution-scoring, trade-management-system, emergency-exit, atr-scaling, h2-l2-state-machine, article-huangzongprice-wg-brooks-context-v3]
char_count: 2515
---
# 动态风控参数（Dynamic Risk Parameters）

## 一句话定义
v3 执行引擎基于主要波段极点（majorSH/majorSL）和 ATR 自动计算止损、入场和止盈价格——将 Brooks「保护性止损应放在信号极值之外」的定性规则量化为精确公式。

## 核心要点
- **止损**：`majorSL - 0.5×ATR20`（多头）/ `majorSH + 0.5×ATR20`（空头）——放在波段极点之外
- **入场**：`high + 0.1×ATR14`（多头）/ `low - 0.1×ATR14`（空头）——在信号棒极值之外留缓冲
- **风险**：`max(入场 - 止损, 0.5×ATR14)`——最小风险为半倍 ATR，防止窄止损
- **止盈**：`入场 + 2.0×风险`（多头）/ `入场 - 2.0×风险`（空头）——固定 1:2 盈亏比
- 所有参数均为实时动态计算，随 K 线推进自动更新

## 完整公式

```
// 缓冲参数
stopBuf = max(mintick, 0.5 × ATR20)   // 止损缓冲
entBuf  = max(mintick, 0.1 × ATR14)   // 入场缓冲

// 多头侧
lSL  = majorSL - stopBuf               // 止损 = 主要低点 - 0.5×ATR20
lEnt = high + entBuf                   // 入场 = 当根高点 + 0.1×ATR14
lRsk = max(lEnt - lSL, 0.5×ATR14)     // 风险 = max(入场-止损, 半倍ATR)
lTP  = lEnt + 2.0 × lRsk              // 止盈 = 入场 + 2倍风险

// 空头侧
sSL  = majorSH + stopBuf               // 止损 = 主要高点 + 0.5×ATR20
sEnt = low - entBuf                    // 入场 = 当根低点 - 0.1×ATR14
sRsk = max(sSL - sEnt, 0.5×ATR14)     // 风险 = max(止损-入场, 半倍ATR)
sTP  = sEnt - 2.0 × sRsk              // 止盈 = 入场 - 2倍风险
```

## 参数选择意图

| 参数 | 值 | 意图 |
|------|---|------|
| 止损缓冲 | 0.5×ATR20 | 足够宽以避开噪音，但不至于过大——Brooks 的「放在极点之外刚好够远」 |
| 入场缓冲 | 0.1×ATR14 | 极小的确认缓冲——只在信号棒突破时才成交 |
| 最小风险 | 0.5×ATR14 | 防止波段极点和入场点过近导致的超窄止损——超窄止损会被随机噪音扫掉 |
| 盈亏比 | 1:2 | 经典固定比例，平衡胜率与盈亏比 |
| ATR 来源 | stopBuf 用 ATR20, entBuf 用 ATR14 | ATR20（长周期）提供更稳定的波动率估计用于止损，ATR14（短周期）提供更及时的入场缓冲 |

## 与信号等级的联动

信号标签中固定显示 ENT/SL/TP 三行参考价：
```
Ent : 入场价
SL  : 止损价
TP  : 止盈价
```
在 `i_shTP = true` 时还会在图表上绘制三条水平参考线（入场白色虚线、止损红色虚线、止盈绿色虚线），向右延伸 8 根 K 线。

## 与相关概念的关系
- [[protective-stops]]：Brooks 理论层——止损放在结构极值之外、以损定仓。本概念是此理论在 Pine Script 中的精确量化实现。
- [[execution-scoring]]：执行评分决定「是否入场」，动态风控决定「入场后怎么管理」
- [[trade-management-system]]：SPB（止损/盈亏平衡/追踪止损）是入场后的动态管理，本概念的 SL/TP 是入场时的静态预设
- [[emergency-exit]]：紧急逃生是风控的「意外层」——入场后发现衰竭/假突破，不等 SL 触发就主动退出
- [[atr-scaling]]：ATR 参数化的理论基础——所有缓冲量均以 ATR 为单位
- [[h2-l2-state-machine|H2/L2 State Machine]]：majorSH/majorSL（主要波段极点）来自最近的波段极值——H2/L2 状态机跟踪的就是这些极点的演化

## 实战应用
- 入场在信号棒高点 + 0.1×ATR 而非当根收盘——需等待价格突破确认，不能提前挂单
- 止损在主要低点之下 0.5×ATR 而非紧贴低点——Brooks 原则「给市场一个犯错的空间」
- 止盈固定 1:2 而非动态跟踪——策略假设固定盈亏比优于浮动目标（可能基于回测结论）
- 若 lRsk 被强制设为 0.5×ATR14（因入场和止损之差太小），意味着该信号在大框架下的风险空间不足——可能不适合入场

## 来源支撑
- [[article-huangzongprice-wg-brooks-context-v3]]（V3.0 源码——首次公开完整风控参数计算公式）

## 矛盾与待验证
- 盈亏比固定 1:2 与 Brooks 原著的「让利润奔跑」（部分平仓+追踪止损）策略不同——V3 采用了更机械化的方式
- 止损缓冲 0.5×ATR20 是否对所有品种/周期都适用？牛市中的 A 股波动率远高于 BTC 的区间期
- 最小风险 0.5×ATR14——当信号出现时机极好（入场近止损远），强制扩大风险是否合理？
- 止盈无部分平仓机制——与 [[trade-management-system]] 中描述的 SPB 部分止盈策略不兼容
