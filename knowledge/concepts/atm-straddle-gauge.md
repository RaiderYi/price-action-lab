---
title: "ATM 跨式期权波动率指标"
phase: [trend, range]
signal_types: [scalp, swing]
tags: [straddle, atm, min, 占比, 跨式期权]
difficulty: intermediate
related: [trending-trading-range-days, trading-range-quality, trend-from-the-open, atr-scaling, review-mes-huangzongprice-collection]
char_count: 1391
---
# ATM 跨式期权波动率指标

## 一句话定义
利用 ATM（平值）跨式期权价格反推日内隐含波动率，作为当日价格区间预期的参考指标。

## 核心要点

### 在 MES 复盘中的用法
在 huangzongprice 的每份复盘中，都会出现类似标注：
```
45min TR, 5min -42%, ATM Straddle ~0.63%
```
或
```
ATM Straddle ~0.55% (<0.4% = Chop, >0.65% = Trend Day)
```

### 三个关键数值
1. **45min TR**：45 分钟级别是否处于交易区间
2. **5min -42%**：5 分钟级别 TR 占比（如价格在区间内的时间占比 42%）
3. **ATM Straddle ~0.63%**：当前平值跨式期权价格占标的价格的百分比

### 解读规则
| ATM Straddle 值 | 市场预期 | 交易含义 |
|----------------|---------|---------|
| < 0.4% | 极低波动（Chop） | 刮头皮为主，宽止损无意义 |
| 0.4% ~ 0.55% | 低波动 | 波段利润空间受限 |
| 0.55% ~ 0.65% | 正常波动 | 标准交易环境 |
| > 0.65% | 高波动（Trend Day 可能） | 趋势日概率高，可放大目标 |

### 与 TR 占比的配合
- 高 Straddle + 低 TR 占比 → 趋势日（单向运动）
- 低 Straddle + 高 TR 占比 → 区间震荡日（双向刮头皮）
- 正常 Straddle + 中等 TR 占比 → 趋势交易区间日（[[trending-trading-range-days]]）

## 与相关概念的关系

- [[trading-range-quality]]：ATM Straddle + 5min TR% 提供了 TR 质量的量化验证手段
- [[trend-from-the-open]]：高 Straddle 值（>0.65%）是开盘趋势日的隐含波动率信号
- [[atr-scaling]]：ATM Straddle 是 ATR 的期权市场替代品——两者都是波动率度量但来源不同（期权市场定价 vs 历史统计）
- [[trending-trading-range-days]]：正常 Straddle + 中等 TR% 的典型场景

## 实战应用
开盘前查看 ATM Straddle 值，确定当日的波动率预期，调整止损宽度和利润目标。低于 0.4% 的日子缩小仓位、收紧止损；高于 0.65% 的日子可以使用更宽的止损并放大目标到 2R~3R。

## 来源支撑
- [[review-mes-huangzongprice-collection]]

## 矛盾与待验证
- ATM Straddle 的精确计算方式（是否使用前日收盘价？实时价格？哪个到期日？）未在文本中说明
- 阈值边界（0.4% / 0.65%）是否基于回测统计还是经验法则，待确认
- Brooks 原著中对期权隐含波动率持否定态度（"指标都是遮住图表的垃圾"），huangzongprice 的使用与此立场存在张力
