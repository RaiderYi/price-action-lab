---
title: "Gemini AI 辅助交易复盘方法"
phase: [trend, range, breakout, transition]
signal_types: [l2-entry, failed-breakout]
tags: [gemini, 陷阱过滤, 线进化判, 高潮识别, 对比]
difficulty: intermediate
related: [mes-daily-review-workflow, brooks-signal-catalog, climax, setup-anatomy, prior-trading-memory, journal-mes-daily-review-collection]
char_count: 1151
---
# Gemini AI 辅助交易复盘方法

## 一句话定义
huangzongprice 使用 Google Gemini 对 MES 每日复盘进行 AI 辅助深度解读，聚焦高潮识别、陷阱过滤和 K 线进化判定。

## 核心要点
- **双版本制**：每个交易日同时生成"初版复盘"和"+gemini 深度版"
- **AI 角色**：不是替代人工判断，而是提供 Brooks 理论视角的"第二意见"
- **三大分析维度**：
  1. 高潮识别（Climax Identification）：Range vs ABR 对比 → 判断耗尽
  2. 陷阱过滤（Trap Detection）："The best looking bar late in a trend is usually a trap"
  3. K 线进化判定（Evolutionary Verdict）：Surprise Bar → L1 不可靠 → 升级到 L2
- **AI 输入**：K 线序列 + 背景上下文（通道/趋势/TR 阶段）+ Brooks 课程引用
- **AI 输出**：具体棒号的高潮/陷阱判定 + 入场建议 + 出场时机

## 与相关概念的关系
- [[mes-daily-review-workflow]]：Gemini AI 是复盘的第 6 步可选增强环节
- [[brooks-signal-catalog]]：AI 帮助判断当前信号属于目录中的哪个类型
- [[climax]]：高潮识别是 Gemini 最擅长的分析维度
- [[setup-anatomy]]：AI 帮助区分"强架构"和"陷阱架构"的外观差异
- [[prior-trading-memory]]：AI 目前不做 PTM 对照（这是人类独有的记忆索引）

## 实战应用
完成初版复盘标注后，将同一份图表发给 Gemini，要求它：①识别所有高潮棒 ②标注可能的陷阱架构 ③给出进化的入场建议（L1→L2升级）。对比 AI 判断与自己的判断，标注差异点。

## 来源支撑
- [[journal-mes-daily-review-collection]]（+gemini 版本约 80 天）
- Gemini 注释最早出现：2025-12-30 复盘
- SC2（Best Loser Wins）参考：2026-02 之后的复盘

## 矛盾与待验证
- Gemini 的判定精确度（尤其是假突破 vs 真陷阱的区分）尚未经统计验证
- AI 的分析深度受 OCR 质量限制（pdftotext 提取导致 K 线编号和中文注释混叠）
- 是否可推广到其他 AI（如 Claude/GPT-4）进行同类辅助？尚未测试
