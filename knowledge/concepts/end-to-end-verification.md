---
title: "端到端验收框架"
phase: [range]
signal_types: []
tags: [阶段, web, marker, signal, 前端检查]
difficulty: intermediate
related: [signal-whitelist-filter, signal-serialization-contract, live-trading-monitor, rs-scoring, article-huangzongprice-pa-16-verification-plan]
char_count: 1085
---
# 端到端验收框架

## 一句话定义
交易信号系统的四阶段验收方法：从后端静态检查到前端动态运行的全链路一致性验证。

## 核心要点
- **四阶段结构**：A（后端与数据源静态检查）→ B（multi_tf 前端检查）→ C（fusion 前端检查）→ D（端到端动态运行）。
- **验收项格式**：每个验收项包含编号、验收项名称、检查方法（grep/read/目视/API调用）、明确的通过标准。
- **阶段 A — 后端静态**：白名单定义与数量（A1）、Web 层过滤逻辑（A2）、序列化字段完整性（A3）、回测统计写入（A4）。
- **阶段 B — multi_tf 前端**：白名单与短标签定义（B1）、K 线 marker 文案（B2）、PA 卡片类型显示（B3）、PA 卡片价格与 RS（B4）。
- **阶段 C — fusion 前端**：与 B 对应，另加历史 PA 恢复的容错性（C4）。
- **阶段 D — 端到端动态**：API 返回 PA 类型校验（D1）、前端无未知类型告警（D2）、卡片与 marker 一致性目视核对（D3）。
- **汇总产出**：各阶段汇总为「通过/不通过」+ 问题与修复建议。

## 与相关概念的关系
- [[signal-whitelist-filter]]：验收框架的 A1/A2/B1/C1/D1 项直接验证白名单过滤机制。
- [[signal-serialization-contract]]：A3/B4/C3 项验证序列化字段的完整性。
- [[live-trading-monitor]]：阶段 D 要求实际启动 Web 服务进行动态验收。
- [[rs-scoring]]：验收项中 RS 评分在卡片与 marker 上的展示一致性。

## 实战应用
在信号系统升级后，按 A→B→C→D 顺序执行验收：先 grep 代码做静态确认（零成本），再检查前端 HTML 文件（零成本），最后启动服务做端到端动态验收（需环境）。每个阶段的通过标准都明确、可复现。

## 来源支撑
- [[article-huangzongprice-pa-16-verification-plan]]

## 矛盾与待验证
- 阶段 D 在本轮验收中跳过（需本地启动 Web 服务）。后端过滤逻辑已确认，前端仅展示白名单内类型，但实际推送的 `pa_signal` / `active_pa_signal` 中 `signal_type` 是否均在 16 个 value 内，仍需一次动态运行确认。
