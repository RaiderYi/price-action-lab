---
title: "信号序列化契约"
phase: [trend, range]
signal_types: []
tags: [price, target, annotation, dict, web]
difficulty: intermediate
related: [signal-whitelist-filter, rs-scoring, end-to-end-verification, trade-management-system, article-huangzongprice-pa-16-verification-plan]
char_count: 1044
---
# 信号序列化契约

## 一句话定义
PA 信号从后端到前端传递时的字段规范——`_annotation_to_dict()` 返回值的完整字段定义。

## 核心要点
- **来源**：`btc_multi_tf_web.py` 和 `btc_fusion_web.py` 中的 `_annotation_to_dict()` 方法。
- **必含字段**：
  - `signal_type`：信号类型枚举值（16 PA 之一 + NO_SIGNAL）
  - `signal_name`：信号的可读名称
  - `entry_price`：入场价格
  - `stop_price`：止损价格
  - `target_1r`：1R 目标价（第一目标）
  - `target_2r`：2R 目标价（第二目标）
  - `rs_score`：RS 综合质量评分（0-100）
  - `regime`：当前市场状态（趋势/震荡等）
- **可选/附加字段**：
  - `filter_reasons`：过滤/否决原因列表（如信号被否决时）
  - `quality_tags`：信号质量标签
- **前端绑定**：multi_tf 与 fusion 两套前端均按上述字段名绑定数据，无硬编码占位。

## 与相关概念的关系
- [[signal-whitelist-filter]]：序列化之前必须先通过白名单过滤——非 16 PA 类型不会进入序列化流程。
- [[rs-scoring]]：`rs_score` 字段的值来自 RS 评分系统。
- [[end-to-end-verification]]：验收项 A3 专门检查序列化字段完整性。
- [[trade-management-system]]：`entry_price`、`stop_price`、`target_1r`/`target_2r` 构成交易管理的价格输入。

## 实战应用
当信号系统新增字段（如新增质量标签维度）时，必须同步更新：(1) 后端 `_annotation_to_dict()` 返回值；(2) 前端数据绑定代码；(3) 验收计划中的 A3 验收项通过标准。

## 来源支撑
- [[article-huangzongprice-pa-16-verification-plan]]

## 矛盾与待验证
- 无。当前序列化契约已在 two Web 文件中一致实现，A3 验收通过。
