# huangzongprice

## 身份/定义
独立量化开发者，专注 Al Brooks 价格行为学（Price Action）的 Pine Script 实现。开发了一系列 Brooks PA 背景引擎、执行引擎、交易系统（BTC/A股双市场），项目持续从 V1 迭代至 V4.2。

## 核心贡献/观点

### 架构演进
- **V1.x（单脚本）**：WG Wedge-Gravity 双核（FSM 硬规则 + 引力场软评分），背景与执行在同一脚本内
- **V2.x（联动分离）**：Context Engine + Execution Engine 分离为两个独立 Pine Script 指标，通过 `input.source` API 绑定联动
- **V3.x（执行精简）**：Execution Engine 精简为 Lean Linked 版，三因子加权评分 + ABC 等级 + 可选确认 K 线
- **V3 背景升级**：背景层从「过滤器」升级为 Playbook Engine（交易机会分发器），新增趋势过滤/区间增强/SR 环境/三推背景 5 大模块
- **V4.x**：持续迭代修复 Pine Script 语法兼容性 bug
- **V5.x**：全栈单体引擎（1520行），合并 Context + Execution 回单指标，引入 Pine Script v6 类型系统，新增供需区/订单块模块
- **V6**：减法分支（251行），砍掉执行层回归纯背景分析——用替代 FSM、替代单维评分、统一否决——代码量减少 83%，huangzongprice 系列首个纯背景指标

### 双市场架构
- BTC 市场（主力）：完整回测系统 + 实时交易监控（CLI + Web Dashboard + WebSocket）
- A 股市场（扩展）：基于 baostock 的复权数据 + 同一策略逻辑跨市场部署

### 设计理念
- 背景先于执行：背景描述环境 → 识别玩法类型 → 决定哪类结构有资格进入执行候选池
- 背景层是唯一权威来源，执行层不维护背景副本
- 联动失败时宁可无信号也不静默回退

## 代表作品
- [[article-huangzongprice-context-execution-linkage-setup]] — 背景-执行联动设置手册
- [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]] — 执行引擎 v3 架构文档
- [[article-brooks-pa-verification]] — Brooks PA 策略代码验证
- [[article-wg-v15-analysis]] — Wedge-Gravity V1.5 全流水线分析
- [[guide-btc-backtest]] — BTC 回测系统操作手册
- [[article-huangzongprice-live-system-guide]] — 实时交易系统操作手册
- [[article-20260306-btc-web-system-guide]] — BTC Web Dashboard 手册
- [[article-huangzongprice-version-history]] — V3→V4.2 版本历史
- [[article-ashare-guide]] — A 股终端实操手册
- [[integration-summary-20260306]] — 多市场架构集成总结
- [[README-summary]] — 项目总览
- [[article-background-v3-upgrade]] — 背景层 v3 升级设计稿
- [[article-huangzongprice-v3-phase1]] — V3 第一阶段实施
- [[article-huangzongprice-context-steps]] — 上下文分析步骤设计稿
- [[article-20260520-wedge-gravity-brooks-context-v3]] — WG Brooks V3 完整 Pine Script 源码（1,139 行，从 OHLC 到入场信号的 12 层流水线）
- [[review-huangzongprice-mes-daily-reviews]] — MES 每日复盘合集（52篇，2025.09~2026.03）
- [[article-huangzongprice-context-engine-v6]] — PA背景分析引擎 V6（纯背景版，251行，效率/重叠分类+动能健康双评+一票否决）
- [[book-huangzongprice-trilogy-compiled]] — Brooks 三书合辑（区间元宵版+趋势修订版+反转党生版）工作参考汇编

### 实战复盘方法论
huangzongprice 在量化系统之外，保持了系统的每日手工复盘习惯。52 篇 MES 5min 复盘笔记展示了一套完整的盘后分析方法论：

### 底层理论参考
huangzongprice 将 Brooks 三部曲中译本（罗光海译/木羊策划）汇编为单一工作文件（[[book-huangzongprice-trilogy-compiled]]），含三个版本变体：区间篇（元宵版）、趋势篇（修订版）、反转篇（党生版）——便于量化开发时全文检索 Brooks 原著精确表述。
- **多周期逐级标注**：45min（高级别背景）→ 5min（交易周期）→ 1min（精细入场）
- **MC 评分实战标注**：每段行情标注 MC 评分（10+2 项目 + % 调节），将 Brooks 定性框架转化为可重复的量化标注
- **速记记号体系**：自创简洁英文字母缩写（STP/STC/STB/cxbar/PTM 等）实现在图表上的高效标注 → [[trade-review-notation]]
- **Gemini AI 辅助**：部分复盘引入 AI 对交易进行"演变判定"（Evolutionary Verdict），将人工标注与 Brooks 理论交叉验证
- **复盘框架**：从一句话日概→多周期标注→MC评分→执行回顾的完整方法论 → [[daily-trade-review-framework]]

## 与其他实体的关系
- [[al-brooks]]：huangzongprice 的所有工作基于 Al Brooks 的价格行为学理论体系，是 Brooks 理论在 Pine Script 量化领域的系统化实现者
