---
title: "Path-A / Path-B 双路突破检测"
phase: [range, breakout, transition]
signal_types: [failed-breakout]
tags: [path, 连续, 对应, atr, new]
difficulty: intermediate
related: [fsm-market-cycle, channel, breakout-mechanics, article-wg-v2-master]
char_count: 884
---
# Path-A / Path-B 双路突破检测

## 一句话定义
FSM 震荡→新突破转换的两条检测路径：Path-A 激进即时（单根突破K线即切换）vs Path-B 保守延迟（连续3根收盘在边界外才切换）。

## 核心要点
- **Path-A（激进即时）**：实体 > i_brkMul×ATR20（默认1.5×）+ 收盘超出唐奇安边界 > i_brkOff×ATR20（默认0.5×）+ 创周期新高/低 → 该根K线当即触发 NEW_BREAKOUT
- **Path-B（保守延迟）**：同一方向连续 3 根 K 线收盘价维持在唐奇安边界外侧 → 第3根触发 NEW_BREAKOUT
- Path-A 和 Path-B 并行独立运行，任一触发即可完成状态转换
- Path-B 计数器在震荡区间(TR)内维持和重置，切换方向时计数器重置为1

## 与相关概念的关系
- [[fsm-market-cycle]]：Path-A/B 是 FSM 中 TR→NEW_BREAKOUT 转换的具体实现，替代了 V1.5 的简单唐奇安穿破判断
- [[channel]]：Path-A 捕获的「实体突破」对应 Brooks 原著的强势突破棒；Path-B 的「连续3根」对应 Brooks 的突破确认逻辑
- [[breakout-mechanics]]：Path-A 对应 Brooks 的「突破进跟随」模式，Path-B 对应「耐心等确认」

## 实战应用
Path-A 信号出现时市场动能最强但假突破风险也最大；Path-B 更可靠但可能错过最佳入场点。两者同时触发时（连续3根+第3根为强突破棒）信号最可靠。

## 来源支撑
- [[article-wg-v2-master]]

## 矛盾与待验证
- V1.5 无此机制（仅唐奇安穿破判断），V3 Context Engine 是否保留了双路设计？待交叉验证
- Path-A 的「实体>1.5×ATR20 + 收盘超边界0.5×ATR20」阈值是否为最优？在 A 股不同板块是否需要调整？
