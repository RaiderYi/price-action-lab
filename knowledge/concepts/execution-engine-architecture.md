---
title: "执行引擎分离架构（Context → Execution 两层分离）"
phase: [trend, range, transition]
signal_types: [h2-entry, l2-entry, wedge]
tags: [engine, context, 执行引擎, execution, api]
difficulty: intermediate
related: [wedge-gravity-dual-core, pine-source-binding, linkage-failure-safety, fsm-market-cycle, execution-scoring, confirmation-bar, article-huangzongprice-execution-engine-v2-linked, article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked, article-wg-v15-analysis]
char_count: 1696
---
# 执行引擎分离架构（Context → Execution 两层分离）

## 一句话定义
v3 将 V1.5 的单指标双核架构拆分为 Context Engine（背景引擎）和 Execution Engine（执行引擎）两个独立 Pine Script 指标，通过 20+ `input.source` API 绑定传递背景数据。

## 核心要点
- **两层分离**：Context Engine（背景引擎）→ API 绑定层 → Execution Engine（执行引擎）。v2 是 huangzongprice 系统中**首个实现这一分离的版本**（此前 V1.5 是单指标内嵌双核）。
- **API 绑定机制**：使用 Pine Script v6 `input.source` 将外部指标的 plot 输出绑定为执行引擎的输入变量
- **绑定信号三组**：
  - 背景许可组（`bgSupport/Conflict/Veto/Score/State`）→ 决定 `allowLong/Short`
  - 阶段信息组（`phaseState/Dir/IsRange/IsTransition` 等）→ 区分顺势/反转场景
  - 动能评估组（`trendMaturity/ExhaustRisk`）→ 楔形反转候选的触发条件
- **联动安全**：`linkOk` 校验 API 版本号（==2.0）和 Ready 信号，未联动时所有信号禁用——防止静默回退
- **面板降级**：决策面板从 V1.5 详细信息面板精简为 7 行：联动状态/背景/阶段/结构/等级/候选/信号
- **结构独立性**：H2/L2 状态机和楔形检测均在 Execution Engine 内部重新实现（简化版），不依赖 Context Engine 的结构数据

## 与相关概念的关系
- [[wedge-gravity-dual-core]]：V1.5 单指标双核架构的前身——v3 将其拆分为两层分离
- [[pine-source-binding]]：两层分离的核心技术——`input.source` API 绑定机制
- [[linkage-failure-safety]]：联动失败时的安全兜底——版本校验 + Ready 信号双重确认
- [[fsm-market-cycle]]：Context Engine 中的硬规则层，其阶段状态通过 `phaseState/phaseDir` 传入执行层
- [[execution-scoring]]：执行引擎的评分核心——三因子加权公式
- [[confirmation-bar]]：执行引擎的可选确认机制

## 实战应用
决策面板右上角显示"已联动"（绿色）/ "未联动"（红色），是交易前第一眼必看项。执行引擎本身不计算背景——如果 Context Engine 未加载或版本不匹配，所有信号静默禁用。

## 来源支撑
- [[article-huangzongprice-execution-engine-v2-linked]]（v2 是两层分离的第一个实现——25 个 API 字段绑定 + 18 行信息面板）
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（v3 在 v2 基础上精简面板为 7 行、合并信号路线）
- [[article-wg-v15-analysis]]（V1.5 单指标双核架构——v2/v3 的演进前身）

## 矛盾与待验证
- 两层架构的可维护性 vs 单指标便利性：分开后每个指标职责清晰，但用户需要在图表上同时加载两个指标并正确配对绑定——操作复杂度显著上升
- 当前 Context Engine 和 Execution Engine 的版本号硬编码为 2.0——未来升级 Context Engine 时需同步更新 Execution Engine 的版本校验，否则会静默断联
