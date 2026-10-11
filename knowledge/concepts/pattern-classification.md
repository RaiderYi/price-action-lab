---
title: 模式分类法 (Pattern Classification)
created: 2026-05-19
updated: 2026-05-19
type: concept
tags: [meta, taxonomy, pattern, reference, framework]
sources: [sources/encyclopedia-brooks-chart-patterns.md]
confidence: high
---

# 模式分类法 (Pattern Classification)

## 一句话定义
Brooks 将约 100 种图表模式按市场状态驱动+字母顺序分类为 13 个 Part，每模式有 4 个方向变体，形成约 400 个可查阅条目的百科全书架构。

## 核心要点

### 分类的底层逻辑
- Brooks 的目标：**"如果交易者识别出市场在做什么，他可以查看该模式的示例来了解可能发生什么"**
- 分类不是纯理论框架——它是**实用查阅系统**
- 按市场状态分级：Always In → 缺口 → 反转 → 通道 → 区间 → 高潮 → 楔形
- 在每个状态下手动查找对应字母范围

### 分类的全谱（13 Part）

| Part | 字母范围 | 主导市场状态 | 代表模式 |
|------|---------|-------------|---------|
| 1 | A-B | 方向确立 | Always In Long/Short、连续棒、Surprise Bar |
| 2 | C | 持续/衰竭 | 通道（Channel）、高潮（Climax）、崩溃（Crash）、杯柄 |
| 3 | D-F | 反转/失败 | 双顶底、失败突破、最终旗形 |
| 5 | GD-GDM | 缺口下行 A-M | Gap Down 突破/反转/延续模式 |
| 6 | GDN-GT | 缺口下行 N-Z | Gap Down 进阶 + Gap 到 Trading Range |
| 7 | GU-GUM | 缺口上行 A-M | Gap Up 突破/反转/延续模式 |
| 8 | GUN-GUZ | 缺口上行 N-Z | Gap Up 进阶 + 缺口趋势日 |
| 9 | H-L | 高低点博弈 | 关键高低点测试、水平 S/R 模式 |
| 10 | M | 重大反转 | MTR 全部四变体（HH/HL/LL/LH）+ 失败 MTR |
| 11 | N-P | 中段形态 | 嵌套、开盘驱动、回调、突破模式（BOM） |
| 12 | Q-SM | 交易管理 | 加仓（Scale In）、区间刮头皮策略 |
| 13 | SN-SZ | 衰竭极值 | 连续卖出高潮、尖刺+通道熊趋势 |
| 16 | W-Z | 终极楔形 | 复杂楔形 + 多时间框架共振 |

### 每个模式的 4 种变体

Brooks 为每个基本模式创建 4 个版本：

1. **Buy 版本**：多头入场信号
2. **Sell 版本**：空头入场信号
3. **Failed Buy 版本**：多头信号失败 → 空头入场机会
4. **Failed Sell 版本**：空头信号失败 → 多头入场机会

这 4 种变体体现了 Brooks 的核心哲学：**每个信号的反面也是一个信号**。失败的买入信号 = 空头的卖出信号。

### 递归分类规则

在单个字母范围内，组织方式为：

```
字母范围 → 买入模式（Buy Setups）
         → 卖出模式（Sell Setups）
         → 失败买入（Failed Buys → Bear Setups）
         → 失败卖出（Failed Sells → Bull Setups）
         → 混合/切换模式（Swings Between Buy/Sell）
```

### 百科全书的规模

- 约 100 个基本模式 × 4 方向变体 = 约 400 个条目
- 4777 页 PDF → 每个条目平均约 12 页实例图表
- 目标用户：已有 Brooks 理论基础、需要查询具体模式表现的波段交易者

## 与相关概念的关系

- [[al-brooks]]：分类法是 Brooks 教学体系的"查阅层"——三部曲是理论层，Trading Course 是教学层，百科全书是参考层
- [[fsm-market-cycle]]：分类法的主要维度就是市场周期——Always In 对应趋势、C/D-F/M 对应反转/通道、H-L 对应区间
- [[binary-decisions]]：分类法帮助二元决策——确定了是哪种市场状态后，直接去对应 Part 查找
- [[always-in]]：Part 1（A-B）的核心组织概念——先确定 Always In 方向，再决定操作
- [[best-trades]]：分类法中的不同 Part 对应 Brooks 最佳交易层级的不同级别

## 实战应用

当在实盘或复盘时看到一种模式但不确定其含义时：
1. 先判断当前市场状态（趋势/区间/反转/缺口？）
2. 找到对应的字母范围 Part
3. 在百科全书中浏览该 Part 下的实例图表
4. 对照实例判断当前模式的可靠性和后续可能性

这是 Brooks 设计百科全书的原意——**不是用来记住所有模式的，而是用来查询的**。

## 来源支撑
- [[brooks-signal-catalog]] — 全书 4777 页
- Brooks Trading Course Slide 8："About 100 basic patterns × 4 = 400 total sections"

## 矛盾与待验证
- Part 4/14/15 缺失——可能是 OCR 遗漏，也可能是空白/合并。需核对原始 PDF 确认
- OCR 转换导致部分模式名称有拼写错误，精确模式名称需要参考原始 PDF
