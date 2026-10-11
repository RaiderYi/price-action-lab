# 16 个 BTC PA 信号 — 完整验收计划

## 元信息
- 作者：huangzongprice（项目作者）
- 日期：2026-05-19（验收执行日期）
- 原始位置：`raw/articles/huangzongprice/VERIFICATION_PLAN_16_PA.md`

## 一句话摘要
BTC PA 信号系统的端到端验收方案：覆盖后端白名单、前端两套页面（multi_tf / fusion）、全链路一致性的四阶段验证。

## 核心论点
1. **白名单契约**：`BTCSignalType` 枚举共 16 个 PA 信号值（H1/H2/L1/L2/DB/DT/BTC/STC/TRF/PC/H3W/L3W/WFL 等），+ 缠论 `chan_buy`/`chan_sell`，后端和前端必须精确对齐。
2. **三层过滤**：后端枚举定义 → Web 层 `VALID_PA_SIGNAL_VALUES` 过滤 → 前端 `KNOWN_PA_SIGNAL_TYPES` 映射，三层中任一层不一致都会导致未知类型泄露。
3. **序列化契约**：`_annotation_to_dict()` 返回字段包含 `signal_type`、`signal_name`、`entry_price`、`stop_price`、`target_1r`、`target_2r`、`rs_score`、`regime`、`filter_reasons`、`quality_tags`。
4. **四阶段验收框架**：A（后端静态检查）→ B（multi_tf 前端）→ C（fusion 前端）→ D（端到端动态），每阶段有编号验收项、方法和明确的通过标准。
5. **防御性设计**：前端在遇到未知信号类型时回退为可读字符串（不崩溃），并在控制台输出 `[PA校验] 未知信号类型` 告警。

## 提取出的新概念
- [[signal-whitelist-filter]] — 信号白名单过滤机制（枚举→Web→前端三层一致性）
- [[end-to-end-verification]] — 端到端验收框架（四阶段、验收项清单、通过标准）
- [[signal-serialization-contract]] — 信号序列化契约（_annotation_to_dict 字段规范）

## 与现有知识的冲突
- 无。本文是 BTC 系统的验收文档，与已有 Brooks 理论概念（[[brooks-signal-catalog]]）无冲突。16 信号类型在 [[brooks-signal-catalog]] 中已有定义，本文聚焦于验证这些类型在代码链中的传递一致性。
