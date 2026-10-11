---
title: "RS 评分系统"
phase: [trend, range, breakout]
signal_types: [h2-entry, pullback-entry]
tags: [阈值, python, btc, price, action]
difficulty: intermediate
related: [brooks-signal-catalog, rs-sensitivity-analysis, trade-management-system, live-trading-monitor, article-huangzongprice-live-system-guide, integration-summary-20260306, README-summary]
char_count: 1462
---
# RS 评分系统

## 一句话定义
RS 评分（Relative Strength Score）是对价格行为入场信号质量的综合量化过滤器，0-100 分制，低于阈值则信号被静默丢弃。

## 核心要点
- RS 评分是信号检测与交易执行之间的**中间层**——先检测信号类型（如 bull_h2），再 RS 打分，通过才执行
- 默认阈值为 **70%**，低于 70 分的信号不触发提醒/交易
- 命令行参数 `--rs` 可调整阈值（降低如 60 可获得更多信号但质量下降）
- 评分结果随信号面板一起输出：`【新信号】做多▲ @ 87480.50 (RS=75%)`

## 工作流程

```
信号检测（brooks-signal-catalog）
        ↓
    RS 评分计算
        ↓
   RS ≥ 阈值? ─── NO → 信号丢弃
        ↓ YES
   信号提醒 + 面板保存 + 回调触发
```

## 与相关概念的关系

- [[brooks-signal-catalog]]：RS 评分的评估对象——16 种信号类型通过检测后才进入 RS 评分环节。RS 评分不重复定义"什么是信号"，只回答"这个信号有多好"
- [[rs-sensitivity-analysis]]：RS 评分设定"门槛"（阈值），敏感性分析回答"门槛设多高最优"。两者配合使用：先理解 RS 评分的构成，再通过敏感性分析找到最优阈值
- [[trade-management-system]]：RS 评分决定「是否入场」，交易管理系统决定「入场后怎么做」。两者串联：RS 通过 → 入场价/止损/目标由交易管理体系计算
- [[live-trading-monitor]]：实时监控系统是 RS 评分的运行载体，信号面板中直接展示 RS 分值和入场三元组

## 实战应用

```bash
# 默认阈值 70%（保守）
python btc_price_action_live.py --symbol BTCUSDT

# 降低阈值到 60%（更多信号，可能更多假信号）
python btc_price_action_live.py --rs 60

# A股 30min，阈值 75%
python a_share_price_action.py --code sz.000001 --rs 75
```

## 来源支撑
- [[article-huangzongprice-live-system-guide]]（LIVE_SYSTEM_GUIDE.md — RS 评分的使用方式和阈值调优）
- [[integration-summary-20260306]]（Web 界面的信号面板展示 RS 评分）
- [[README-summary]]（原策略的信号评分概念）

## 矛盾与待验证
- **评分维度未公开**：当前所有资料只展示 RS 评分的使用方式（阈值过滤、分值展示），但**未说明内部计算维度**（考虑哪些 K 线特征、各维度权重如何）。这是关键知识缺口——如果自行实现 RS 评分系统，需要重新设计评分算法
- **无独立回测**：RS 评分尚未针对「阈值变化对绩效的影响」做过独立回测。65% vs 70% vs 75% 的最优阈值区间未知
- **跨品种泛化**：当前 RS 评分在 BTC 5m 上使用，不同品种/周期是否需要调整阈值尚无数据支撑
