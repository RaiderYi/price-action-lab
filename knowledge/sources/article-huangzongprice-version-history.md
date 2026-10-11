# Wedge-Gravity Brooks Context Engine — 版本历史与Bug修复

## 元信息
- 作者：huangzongprice
- 日期：未标注（对应 V3 → V4.1 → V4.2 版本演进过程）
- 原始位置：`raw/articles/huangzongprice/VERSION_HISTORY.md`
- 文件类型：版本变更日志 / 技术修复文档

## 一句话摘要
WG Brooks Context Engine 从 V3（编译失败）到 V4.2（生产就绪）的完整演进记录，包含 3 类 Pine Script v5 bug 修复与系统化视觉优化方案。

## 核心论点

### 1. 三个关键 Bug 修复

| Bug 类型 | 位置 | 根因 | 修复方式 |
|----------|------|------|----------|
| 未定义变量 | V3 第808-810行 | `bgEventColor` / `bgEventTextColor` 在使用前未声明 | V4 新增条件赋值定义 |
| `line.set_xy1` 参数错误 | V3 第838行 | `set_xy1` 仅接受3个参数（line, x, y），误传5个 | 拆分为 `set_xy1` + `set_xy2` 两次调用 |
| `plotchar` 参数顺序错误 | V3 第796-819行 | Pine Script 要求位置参数在前、命名参数在后 | 重排参数顺序，`title=` 移到最后 |

### 2. V4.2 视觉优化体系

建立了三层信号显示分级（见 [[indicator-visual-optimization]]）：
- **核心信号**（默认开启）：H2/L2、入场信号、假破/衰竭/竭尽 — 使用 large/normal 符号
- **辅助信号**（默认关闭）：H1/L1、波段极点 — 使用 tiny 灰色符号
- **背景信息**（默认关闭）：周期状态、背景状态标签

### 3. 代码质量评估框架

提出了 5 维度评分体系：编译通过率 / 逻辑完整性 / 代码结构 / 视觉体验 / 生产就绪度。V4.2 在 5 个维度上均达到最高评级。

## 提取出的新概念

- [[indicator-visual-optimization]] — TradingView 指标的显示分层设计方法论（新增）
- 其余核心概念（FSM 周期、三推楔形、引力场、H2/L2、信号评分、紧急逃生）已在 [[article-wg-v15-analysis]] 中完整覆盖

## 与现有知识的冲突

无冲突。本文是纯版本管理文档，不涉及交易逻辑变更——V3/V4/V4.2 的功能模块（市场周期FSM/三推楔形/Brooks H/L计数/引力场/背景决策层/执行系统）在所有版本中完全一致，变化仅限于渲染层和编译正确性。

## 与已有来源的关系

- [[article-wg-v15-analysis]]：本文档分析的是同一指标（WG V1.5）的渲染层代码演进，是 WG_V15 分析文档的补充
- [[README-summary]]：README 描述的是策略功能，VERSION_HISTORY 描述的是代码质量和版本管理
