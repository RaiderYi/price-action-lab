---
title: "信号白名单过滤"
phase: [range]
signal_types: [h2-entry, l2-entry]
tags: [signal, 白名单过, web, btc, valid]
difficulty: intermediate
related: [brooks-signal-catalog, signal-serialization-contract, end-to-end-verification, article-huangzongprice-pa-16-verification-plan]
char_count: 1089
---
# 信号白名单过滤

## 一句话定义
在枚举、Web序列化、前端渲染三层使用一致的白名单集合，确保仅有16个PA信号类型能通过全链路。

## 核心要点
- **后端枚举层**：`BTCSignalType` 定义 16 个 PA 枚举值 + `NO_SIGNAL`；`VALID_PA_SIGNAL_VALUES` 为对应的 `frozenset`，两者一一对应。
- **Web 过滤层**：`btc_multi_tf_web.py` 和 `btc_fusion_web.py` 在历史信号写入与当前帧 `active_pa_signal` 写入前均有 `signal_type.value in VALID_PA_SIGNAL_VALUES` 判断。
- **前端映射层**：`KNOWN_PA_SIGNAL_TYPES` / `KNOWN_PA_SIGNAL_TYPES_FUSION` 各含 16 PA + `chan_buy`/`chan_sell`；`PA_SHORT_LABELS` 将每个 value 映射到短标签（H1/H2/L1/L2/DB/DT/BTC/STC/TRF/PC/H3W/L3W/WFL 等）。
- **防御性回退**：前端遇到未知信号类型时不崩溃，而是在控制台告警 `[PA校验] 未知信号类型` 并回退为可读字符串。
- **三层一致性**：任一层不一致都会导致未定义类型通过或已知类型被拒绝，验收时必须逐层校验。

## 与相关概念的关系
- [[brooks-signal-catalog]]：定义了 16 种信号类型本身——白名单过滤确保代码链中只有这些类型。
- [[signal-serialization-contract]]：白名单过滤的下一环节——通过过滤的信号按统一字段契约序列化。
- [[end-to-end-verification]]：白名单过滤是验收阶段 A1/A2/B1/C1 的核心检查对象。

## 实战应用
在 BTC/A股信号系统的开发迭代中，每次新增或修改信号类型时，必须同步更新三层白名单（枚举 → VALID_PA_SIGNAL_VALUES → 前端 KNOWN/PA_SHORT_LABELS），并用验收计划逐项验证。

## 来源支撑
- [[article-huangzongprice-pa-16-verification-plan]]

## 矛盾与待验证
- 无。白名单过滤逻辑已在 huangzongprice 项目中实现并通过静态检查（A1/A2/B1/C1 全部通过）。
