---
title: "结构综合信号"
phase: [trend, range]
signal_types: [h2-entry, l2-entry, wedge]
tags: [structurescorel, wedge, 评分, 信号, 跨度]
difficulty: intermediate
related: [three-push-wedge, h2-l2-state-machine, fsm-market-cycle, signal-scoring-synthesis, execution-scoring, article-huangzongprice-wedge-gravity-v5-cycle-structure]
char_count: 2021
---
# 结构综合信号

## 一句话定义
将楔形信号（上升/下降楔形）与 H2/L2 计数信号合并为统一的多空结构信号，楔形使用加权评分（对称40%+收敛35%+跨度25%），纯 H2/L2 使用固定分（0.55），输出 `longStruct`/`shortStruct` 布尔 + `structureScoreL/S` 评分。

## 核心要点

### 信号来源（两个独立通道）
- **楔形通道**：`fallingWedge`（做多）/ `risingWedge`（做空），来自三推楔形识别模块
- **H2/L2 通道**：`h2`（做多）/ `l2`（做空），来自 H/L 计数状态机

### 合并逻辑
```
longStruct  = fallingWedge OR h2    （任一为真即激活多头结构）
shortStruct = risingWedge  OR l2    （任一为真即激活空头结构）
```

两通道独立运行、互不排斥——可同时为真。

### 评分公式

**多头结构分**：
- 楔形触发：`structureScoreL = symScore × 0.40 + convScore × 0.35 + spanScore × 0.25`
- 纯 H2：`structureScoreL = 0.55`
- 均未触发：`structureScoreL = 0.0`

**空头结构分**：完全对称，楔形用上升楔形三项分，纯 L2 = 0.55。

**评分含义**：
- 楔形评分 0~1，取决于三推的对称性、收敛程度和跨度
- H2/L2 不给动态评分——只要状态机输出 `h2=true` 就给固定基础分 0.55
- 楔形评分通常高于纯 H2/L2（因为评分体系更细粒度），表达「楔形结构比单纯 H2 更可靠」的判断

### 优先级显示
信息面板「结构优先级」行：
- 仅楔形：`WEDGE / -` 或 `- / WEDGE`
- 仅 H2/L2：`H2 / -` 或 `- / L2`
- 两者同时：`WEDGE>H2 / -` 或 `- / WEDGE>L2`

注意「>」表示优先级（楔形高于 H2/L2），并非分数相加——实际评分各算各的。

### 数据输出
两个结构分通过 invisible plot 输出给指标 B：
- `多头结构分`（plot 7）
- `空头结构分`（plot 8）

## 与相关概念的关系
- [[three-push-wedge|Three Push Wedge]]：楔形通道的具体实现——三项评分（对称/收敛/跨度）的数值来源
- [[h2-l2-state-machine|H2/L2 State Machine]]：H2/L2 信号来源——布尔 h2/l2 的生成机制
- [[fsm-market-cycle]]：FSM 方向决定结构信号是否能被执行（FSM 是硬规则否决层，结构是软评分输入）
- [[signal-scoring-synthesis]]：在 V1.5 中结构分是 lFin/sFin 的一部分；在 V5.0 中结构综合信号已从最终信号评分中独立出来，成为中介层
- [[execution-scoring]]：v3 执行引擎的 `structScore` 与此概念同名但计算方式完全不同（v3 用多布尔项累加，V5.0 用楔形加权/H2固定分）

## 实战应用
- 结构综合信号告诉交易者「当前是否存在值得关注的市场结构」——但不直接等于入场信号
- 楔形触发 + H2 触发（如 `WEDGE>H2`）= 多头共振，但需要 FSM 许可 + 引力场环境好 + 收盘确认
- 关注 `structureScoreL/S` 的数值——>0.7 是强结构信号，0.4-0.7 是弱结构，<0.4 说明结构不成熟
- 纯 H2 固定给 0.55 的设计偏向保守——即使是非常标准的 H2，也不会超过优质楔形

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v5-cycle-structure]]

## 矛盾与待验证
- 楔形和 H2/L2 同时为真时，结构分是否应该取 max 而非分别输出？当前设计（各算各的）允许下游指标 B 自行决策，但可能在信号合成时造成重复计数。
- 纯 H2/L2 固定 0.55 的设计与 v1 执行引擎的四维度加权 H2 评分（背景适配+趋势适配+位置适配+非中性区+非目标区）不同——v1 能区分「好 H2」和「差 H2」，V5.0 不能。这是有意简化还是待改进点？
- 楔形加权评分（40/35/25）的权重分配是否最优——对称性权重最高合理（结构完整性），但收敛性占比 35% vs 跨度 25% 的优先级关系需要回测验证。
