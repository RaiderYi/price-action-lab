---
title: "执行层"
phase: [trend, range, transition]
signal_types: [h2-entry, l2-entry, wedge]
tags: [模块, 执行层的, layer, 执行层, 许可]
difficulty: intermediate
related: [background-permission, h2-l2-state-machine, three-push-wedge, execution-scoring, confirmation-bar, wedge-gravity-dual-core, fsm-market-cycle, article-huangzongprice-execution-layer-v1]
char_count: 1312
---
# 执行层

## 一句话定义
Brooks PA 系统三层架构中的中间层——消费背景层的方向许可，输出结构化执行候选信号给管理层，自身不重复做背景判断也不负责下单管理。

## 核心要点
- **三层架构**：背景层（Context Layer）→ **执行层（Execution Layer）** → 管理层（Trade Management Layer）
- **上游不越界**：背景层已回答方向/阶段/动能/否决，执行层只消费这些结果，不重新判断大局
- **下游不越界**：执行层不负责下单、止损止盈、仓位管理、出场逻辑——这些归管理层
- **核心职责**：在背景允许的前提下，识别 H2/L2 或楔形结构，评估质量，输出分级候选信号
- **四模块内部分工**：
  1. 模块 A（背景许可层）：翻译背景结果为 allow/trend/reversal 许可
  2. 模块 B（H2/L2 结构模块）：H0→H1→H2_WAIT→H2 状态机 + L2 镜像
  3. 模块 C（楔形结构模块）：上升/下降楔形检测 + 反转许可联动
  4. 模块 D（统一确认与评分）：信号棒质量 + 确认 K 线 + 执行分 + A/B/C 分级

## 与相关概念的关系
- [[background-permission]]：执行层的入口模块，所有结构必须先通过背景许可
- [[h2-l2-state-machine|H2/L2 State Machine]]：执行层的主执行路线（H2/L2 模块）
- [[three-push-wedge|Three Push Wedge]]：执行层的辅助执行路线（楔形模块）
- [[execution-scoring]]：执行层的统一输出——将背景+结构+信号棒合成为最终分数和等级
- [[confirmation-bar]]：执行层的可选延迟确认机制
- [[wedge-gravity-dual-core]]：WG V1.5 代码中执行层未独立，FSM + 信号评分直接合成；本文是对此的架构升级设计
- [[fsm-market-cycle]]：背景层——提供 `bgSupportLong/Short`、`bgVeto`、`phaseState` 等待执行层消费

## 实战应用
在编码实现时，执行层应作为一个独立模块（建议命名为 `ExecutionEngine` 或第二个 TradingView 指标），接收背景层输出的变量字典，处理 H2/L2 和楔形检测，输出 `longCandidate`/`shortCandidate` 给管理层。不建议将执行逻辑直接嵌在背景指标中——分层才能独立调试和版本演进。

## 来源支撑
- [[article-huangzongprice-execution-layer-v1]]

## 矛盾与待验证
- 当前 WG V1.5 代码中没有独立的执行层抽象——FSM 硬规则和 lFin/sFin 软评分直接决定信号输出。本文提出的四模块架构是「下一步编码对象」，尚未在实盘中验证分层是否确实优于一体式设计。
