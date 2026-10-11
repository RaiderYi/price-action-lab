---
title: "V5 全栈整合架构（Wedge-Gravity 架构演进全景）"
phase: [range]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry]
tags: [engine, context, execution, api, 两层分离]
difficulty: intermediate
related: [wedge-gravity-dual-core, execution-engine-architecture, ctx-scoring, supply-demand-zone, order-block-recognition, momentum-health, three-push-wedge, brooks-four-step-context, article-huangzongprice-wedge-gravity-v5, article-wg-v15-analysis, article-huangzongprice-context-engine-v1, article-huangzongprice-execution-engine-v2-linked, article-background-v3-upgrade]
char_count: 3867
---
# V5 全栈整合架构（Wedge-Gravity 架构演进全景）

## 一句话定义
huangzongprice Wedge-Gravity 系统的四个版本演进——从 V1.5 单指标双核、v1 单体内嵌背景、v3 两层分离（Context↔Execution API绑定）、到 V5.0 单体全栈回归——每阶段在模块化与自包含之间做不同取舍。

## 核心要点

### 四版架构对比

| 维度 | V1.5 | v1 (Context Engine standalone) | v3 (两层分离) | V5.0 (单体全栈) |
|------|------|------|------|------|
| **架构** | 单指标双核（硬规则FSM+软评分五因子） | 独立Context Engine（内嵌背景+精简执行） | Context Engine + Execution Engine 两个独立指标 | 单文件1520行全栈引擎 |
| **模块间通信** | 内部变量 | 无外部依赖 | `input.source` API 绑定 20+ 字段 | 内部变量 |
| **背景评分** | 无显式背景层 | 三层加权(0.40/0.35/0.25) + 四类否决 | 同v1（通过API传入执行层） | 同v1（内嵌） |
| **楔形检测** | 几何规则+对称性评分 | 简化三枢轴检测 | v3独立枢轴数组+回撤分析+质量评分 | 类型化WedgeData+三维修正 |
| **H2/L2** | 状态机 | 复用 | 执行层独立重建（简化版） | 状态机（完整版） |
| **供需区/OB** | ❌ | ❌ | ❌ | ✅ V5新增 |
| **部署复杂度** | 低（1个指标） | 极低（1个指标，无外部依赖） | 高（2个指标必须同时加载+版本校验） | 低（1个指标） |
| **可维护性** | 中 | 高 | 最高（模块独立） | 中（1520行单文件） |

### 架构决策的权衡

**为什么 v3 从单体走向两层分离？**
- 背景分析是**通用能力**——同一背景可供不同的执行策略消费
- 解耦后可以独立升级 Context Engine 而不影响 Execution Engine
- API 版本号校验提供联动安全保障

**为什么 V5 又从分离回归单体？**
- 零依赖部署——用户只需添加一个指标，无需担心版本匹配
- Pine Script 的 `input.source` 绑定有性能开销和字段数量限制
- V5 新增的供需区/OB 模块需要与背景决策层紧耦合（供需区位置影响背景分）
- SMC 供需区在 Execution Engine 中无法独立决策——需要知道背景状态才能判断是否"回到需求区"

### V5 的模块拓扑

```
                    ┌─────────────┐
                    │  基础数据层   │ ← OHLC
                    │ ATR/EMA/     │
                    │ Donch/Pivot  │
                    └──────┬──────┘
           ┌───────┬───────┼───────┬───────┬───────┐
           ▼       ▼       ▼       ▼       ▼       ▼
        ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌───────┐
        │ FSM │ │楔形  │ │引力场│ │H2/L2│ │逃命  │ │供需区  │
        │四状态│ │三推  │ │6引力│ │状态机│ │3触发│ │+OB    │
        └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └───┬───┘
           │       │       │       │       │         │
           └───────┴───┬───┴───────┴───────┘         │
                       ▼                             │
              ┌────────────────┐                     │
              │  背景决策层      │◄────────────────────┘
              │  L40%+P35%+M25% │  (供需区位置影响locScore)
              │  四类否决闸     │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │  执行评分层      │
              │  B55%+S25%+K20% │
              │  ABC分级       │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │  信号裁决        │
              │  确认K线/分级过滤│
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │  渲染+警报       │
              │  32行面板+10警报 │
              └────────────────┘
```

## 与相关概念的关系
- [[wedge-gravity-dual-core]]：V1.5 是起点，V5 是最新全栈整合——四版演进的出发点和终点
- [[execution-engine-architecture]]：v3 的两层分离架构，V5 反向合并但保留了完整的三因子评分公式
- [[ctx-scoring]]：V5 完整内嵌了 ctx-scoring 的三层背景评分（位置/阶段/动能），无需 API 绑定
- [[supply-demand-zone]]：V5 全新模块，SMC 理论与 Brooks 体系的首次融合
- [[order-block-recognition]]：V5 全新模块，OB 是供需区的点状精确版
- [[momentum-health]]：V5 动量层使用的五因子公式与此完全一致
- [[three-push-wedge|Three Push Wedge]]：V5 使用类型化 WedgeData 封装楔形——从散变量到结构化数据
- [[brooks-four-step-context]]：V5 的背景决策层就是 Brooks 四步法（价位→阶段→动能→否决）的工程化实现

## 版本兼容提示
- V5.0 是独立 overlay 指标——**不需要 Context Engine 或其他指标**同时加载
- V5.0 与 V4.1 在图表上可共存但会重复显示大量标签/面板——建议只使用一个
- 从 v3（两层分离）迁移到 V5 的用户可以移除 Context Engine + Execution Engine 两个指标，只保留 V5
- V5 的信号评分公式（55/25/20）与 v1/v3 完全一致——策略参数可以复用

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v5]]（V5.0 完整源码 + 更新日志）
- [[article-wg-v15-analysis]]（V1.5 双核架构起点）
- [[article-huangzongprice-context-engine-v1]]（v1 standalone Context Engine）
- [[article-huangzongprice-execution-engine-v2-linked]]（v2/v3 两层分离架构）
- [[article-background-v3-upgrade]]（v3 三层加权背景引擎）

## 矛盾与待验证
- V5 的「单体回归」是否意味着 huangzongprice 认为两层分离架构在实践中成本高于收益？还是 V5 只是「快速发布版」，模块化版本后续仍会维护？
- 供需区和 OB 模块的加入是否会让信息面板过于拥挤？32 行面板在移动端 TradingView 上可能不可读
- V5 没有实现 `input.source` 导出——无法被其他指标绑定消费。这是否意味着 V5 是「终端产品」而非「中间件」？
