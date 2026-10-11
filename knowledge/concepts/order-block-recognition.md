---
title: "订单块识别（Order Block Recognition）"
phase: [trend, range, breakout, transition]
signal_types: [wedge]
tags: [收盘, color, avgbody, 实体, 开盘]
difficulty: intermediate
related: [supply-demand-zone, v5-integrated-architecture, support-resistance, breakout-mechanics, climax, article-huangzongprice-wedge-gravity-v5]
char_count: 2094
---
# 订单块识别（Order Block Recognition）

## 一句话定义
基于 SMC 理论的订单块自动识别——定位强势突破前最后一根反向 K 线（机构订单聚集区），与供需区形成"点—区域"互补关系。

## 核心要点
- **起源**：V5.0 新增的 G7 参数组模块
- **核心思想**：强势突破前必有一根反向 K 线——那是 Smart Money 吸筹/派发的最终位置
- **与供需区的区别**：OB 是**单根 K 线范围**的精确价格区域，供需区是 3 根 K 线的**区域范围**——OB 更精确但寿命更短
- **确认机制**：孤立的强 K 线不能成为 OB——必须有反向确认 K 线才算有效

## 识别规则

### 多头 OB（Bullish OB）— 潜在支撑
```
「最后一根阴线」模式：
1. 当前 K 线是强势下跌阴线（实体 > avgBody5 × 1.5 + 收盘 < 开盘 + 收盘 < 前低）
2. 下一根必须是反向强上涨阳线（实体 > avgBody5 × 0.8 + 收盘 > 开盘 + 收盘 > OB 的 high）
→ 标记当前阴线为多头 OB（机构在此吸筹后发力拉升）
```

### 空头 OB（Bearish OB）— 潜在阻力
```
「最后一根阳线」模式：
1. 当前 K 线是强势上涨阳线（实体 > avgBody5 × 1.5 + 收盘 > 开盘 + 收盘 > 前高）
2. 下一根必须是反向强下跌阴线（实体 > avgBody5 × 0.8 + 收盘 < 开盘 + 收盘 < OB 的 low）
→ 标记当前阳线为空头 OB（机构在此派发后发力砸盘）
```

### 确认机制的意图
无确认的强 K 线可能是：
- 散户冲动交易（非机构行为）
- 趋势中的正常加速（非转折点）
- 流动性扫荡（无后续订单支撑）

确认 K 线确保了 OB 的「转折」属性——机构在此处确实采取了反向操作。

## OB 管理机制

### 强度评分
`ob.strength = barBody / avgBody5`（OB K 线实体相对平均实体的倍数，默认阈值为 1.5）

### 生命周期
- 最大寿命：`i_obMaxBars`（默认 80 bar），比供需区（100 bar）短——因为单 K 线级别的支撑/阻力衰减更快
- 每根 K 线末尾倒序遍历删除过期 OB

### 回测标记
设定了 `isRetested` 字段，V5 初始化但未动态更新（预留功能）

## V5 可视化
- 多头 OB：绿色半透明框（`color.new(color.green, 80)`，边框 `color.new(color.green, 40)`）
- 空头 OB：深红色半透明框（`color.new(color.maroon, 80)`，边框 `color.new(color.maroon, 40)`）
- 从 ob.barIndex 延伸到当前 bar_index
- 最多显示最近 3 个 OB

## 与相关概念的关系
- [[supply-demand-zone]]：OB 是供需区的「点状」补充——供需区 = 区域，OB = 单一 K 线精确位置
- [[v5-integrated-architecture]]：OB 是 V5 单体架构的 G7 模块
- [[support-resistance|Support/Resistance]]：Brooks 的 S/R 基于市场结构，OB 基于机构行为模式
- [[breakout-mechanics]]：OB 的确认机制本质是「突破后不回踩原区域」的验证
- [[climax]]：强 K 线+反向确认的模式与高潮反转有相似之处，但 OB 强调的是「机构订单」而非「情绪极端」

## 实战应用
- 当价格回测多头 OB（下跌至绿色框范围内）→ 观察是否有做多信号棒 → OB 下沿可作为止损参考
- 当价格回测空头 OB（上涨至深红色框范围内）→ 观察是否有做空信号棒 → OB 上沿可作为止损参考
- OB + 供需区 + Brooks S/R 三者在同一位置共振时信号最强
- 信息面板第 29 行显示供需区和 OB 总计数量

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v5]]（G7 参数组，行 622-665）

## 矛盾与待验证
- OB 的「1.5 倍平均实体」强度阈值对波动率不同的品种（BTC vs A股）是否通用？
- `isRetested` 字段已定义但 V5 未实现回测检测——无法区分「已测试过（弱）的 OB」和「未被测试（强）的 OB」
- OB 寿命 80 bar 默认值偏短——SMC 原理论中 OB 在更高时间框架可能有效数周
- 确认 K 线的「反向强波动」条件（实体 > avgBody5 × 0.8）可能过滤掉「慢速但持续」的反转——假阴性风险
