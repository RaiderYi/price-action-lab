---
title: "Pine Script input.source 跨指标绑定"
phase: [range, breakout]
signal_types: [wedge, flag]
tags: [source, input, data, window, display]
difficulty: intermediate
related: [linkage-failure-safety, wedge-gravity-dual-core, execution-engine-architecture, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-context-execution-linkage-setup, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked, article-huangzongprice-context-engine-v2]
char_count: 1882
---
# Pine Script input.source 跨指标绑定

## 一句话定义
通过 `input.source` 参数将执行引擎绑定到背景引擎的 invisible plot 导出，实现 Pine Script 中两个独立指标的深度联动。

## 核心要点
- Pine Script 没有脚本间变量直接导入机制，`input.source` 是唯一的跨指标数据传递方式
- 背景引擎将计算结果导出为 invisible plot（不会在图表上画线，仅存在于 data window）
- 执行引擎通过 `input.source` 参数接收这些 invisible plot 的值
- 绑定是**一对一的**：执行引擎的每个 source 参数必须手动指向背景引擎 data window 的对应导出字段
- 从 V2 到 V3，需要绑定的字段数从 25 个升级到更多（新增 Playbook、S/R 环境、三推背景等字段），但机制不变

## 与相关概念的关系
- [[linkage-failure-safety]]：`input.source` 绑定是否完整直接决定联动安全机制是否触发——绑定不完整 → API Ready=false → 执行层关闭信号输出
- [[wedge-gravity-dual-core]]：双核架构是 WG V1.5 的实现方式（FSM/楔形/引力场在同一脚本内），而 `input.source` 联动是 V2/V3 的实现方式（背景/执行分离为两个独立脚本）——前者是「内核分离」，后者是「进程分离」
- [[execution-engine-architecture]]：两层分离架构的上层是「为什么分」，`input.source` 绑定是「怎么连」

## 实战应用
在 TradingView 中，加载 Context Engine → 加载 Execution Engine → 在执行引擎设置面板中，将每个 `绑定 API xxx` 下拉框选为 Context Engine 的 data window 对应字段。确认面板显示「已联动」即成功。

## 来源支撑
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 执行引擎是 `input.source` API 绑定的最大规模应用——25 个字段从 Context Engine 导入，是该技术的标志性案例）
- [[article-huangzongprice-context-execution-linkage-setup]]（联动设置手册——完整的 25 字段绑定对照表）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]
- [[article-huangzongprice-context-engine-v2]]（v2 Context Engine 引入 `display.data_window` 导出——一种更简洁但互斥的替代绑定模式）

## v2 的 display.data_window 替代方案
v2 Context Engine（本 Wiki 新 ingest）使用 Pine Script v6 的 `display.data_window` 替代了传统的 invisible plot 导出：
- 30+ 变量通过 `plot(..., display=display.data_window)` 暴露到 TradingView 的 Data Window
- 下游执行层可直接从 Data Window 读取，无需手动配置 `input.source` 参数
- 同时发布 `apiVersion`（2.0）和 `apiReadyFlag`（数据就绪标志）供执行层验证联动完整性
- **与 `input.source` 互斥**：`display.data_window` 模式更简洁（无需手动对 20+ 个参数），但失去了关闭单指标时自动断开的能力
- 两种模式的选择取决于下游执行层的实现方式——v3 执行引擎使用 `input.source`，v2 背景引擎使用 `display.data_window`

## 矛盾与待验证
无。该技术是 Pine Script v5/v6 的标准特性，所有 huangzongprice 资料对此描述一致。
