---
title: "联动失败安全机制"
phase: [range]
signal_types: [wedge]
tags: [api, 联动失败, 安全机制, ready, 绑定不完]
difficulty: intermediate
related: [pine-source-binding, execution-engine-architecture, wedge-gravity-dual-core, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-context-execution-linkage-setup, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]
char_count: 1018
---
# 联动失败安全机制

## 一句话定义
当 Context Engine ↔ Execution Engine 的 API 绑定不完整时，执行层自动关闭背景许可并停止输出最终交易信号，防止静默回退到旧逻辑。

## 核心要点
- **检测条件**：API 版本不匹配 / API Ready ≠ true / source 绑定错误导致关键字段无效
- **触发响应**：关闭背景许可 → 不输出做多/做空最终信号 → 面板显示「未联动」
- **设计意图**：防止执行引擎在联动失败时「静默回退」到内嵌的背景副本逻辑，导致背景-执行漂移
- **不是错误**：联动失败时无信号输出是设计行为，不是 bug
- **推荐严格模式**：`要求 API Ready 才运行=开` + `要求 API 版本匹配=开` + `启用背景许可过滤=开`

## 与相关概念的关系
- [[pine-source-binding]]：绑定是前提，安全机制是后果——绑定不完整触发安全机制
- [[execution-engine-architecture]]：安全机制是两层分离架构的「保险丝」——确保执行层真的在用背景层的输出，而非自己的副本
- [[wedge-gravity-dual-core]]：WG V1.5 的双核在同一脚本内，不存在「联动失败」问题——不需要此安全机制。V2/V3 分离架构**必须**有此机制

## 实战应用
在 TradingView 中，如果执行引擎面板显示「联动状态=未联动」「API Ready=未就绪」，逐一检查 25 个 source 绑定是否全部指向正确的背景引擎 data window 字段。全部修复后，面板自动变为「已联动」。

## 来源支撑
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 源码第 171-173 行：`linkOk = apiVersionOk and apiReadyOk` — 联动失败安全的首次实现）
- [[article-huangzongprice-context-execution-linkage-setup]]
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]

## 矛盾与待验证
无。
