---
title: "10+2 实时交易评分网格"
phase: [trend, range, breakout]
signal_types: [l2-entry]
tags: [leg, scoring, ctx, 项加减分, 腿型标签]
difficulty: intermediate
related: [signal-scoring-synthesis, execution-scoring, ctx-scoring, rs-scoring, trade-management-system, trader-equation, journal-huangzongprice-mes-review-collection]
char_count: 2084
---
# 10+2 实时交易评分网格

## 一句话定义
huangzongprice 的 12 项手动交易决策校验清单——入场前逐项加减分，总分决定是否执行交易。

## 核心要点
- 纯手动评分系统：交易员在入场前逐项检查并计分，不同于任何自动化信号评分
- 12 个固定维度：K线质量/前高前低位置/doji/tick gap/BO风险/腿末期风险/价格控制/ATR位置/时间控制/腿完成度/腿型标签
- 减分项为主：12 项中 7 项为减分（-5% 至 -20%），3 项为加分（+5%），2 项为中性参考
- 总分 ~55-65% 为常见通过线，但未发现明确的及格/不及格阈值
- 与已有评分体系互补：自动化系统（signal-scoring-synthesis）管「系统怎么评分」，10+2 管「人怎么决策」
- 应用于 MES 5 分钟 K 线的每一笔实盘交易，146+ 交易日的持续使用验证了其实战有效性

## 12 项评分清单

```
#1  K线质量        -5%    信号棒是否弱（doji、小实体、影线过长）
#2  C vs prior H    -5%    收盘价是否低于前高（空头）/高于前低（多头）
#3  C vs prior L    -5%    收盘价是否低于前低（空头）/高于前高（多头）
#4  doji            -5%    当前棒是否为十字星（方向不明确）
#5  tick gap        -5%    入场方向上是否缺乏跳空缺口确认
#6  BO/mkt regime   -10~-20%  突破失败风险评分 / 当前市场阶段与信号匹配度
#7  late leg        -10~-20%  是否处于趋势腿的末期（追涨杀跌风险）
#8  price control   +5%    是否在主要摆动点有价格控制力
#9  1ABR            中性   当前价格距离 ATR 倍数的位置（参考项，不加减）
#10 time control    +5%    第二腿的时间是否充足（非仓促入场）
#11 leg2 完成度     ~55-65% 第二腿的进度百分比（衡量趋势成熟度）
#12 腿型标签        标注    Late Leg / Channel / L1 / L2 等分类标签
```

## 与相关概念的关系
- [[signal-scoring-synthesis]]：区别——signal-scoring 是自动化 lFin/sFin 五因子公式，10+2 是手动 12 项清单。前者是「机器的评分」，后者是「人的校验」。
- [[execution-scoring]]：区别——execution-scoring 是三因子加权（bg×0.55+struct×0.25+sig×0.20），10+2 是等权加减分。前者用于信号排序，后者用于入场决策。
- [[ctx-scoring]]：Ctx 评分（ctx1/ctx2/ctx3）与 10+2 的 #6（BO/mkt regime）有重叠——都评估市场阶段匹配度。
- [[rs-scoring]]：RS 评分（0-100 分）与 10+2 的 #1-#5（K线质量维度）有重叠——都关注信号棒强度。
- [[trade-management-system]]：10+2 相当于交易管理系统的「第 0 组件」——入场前的最后校验。
- [[trader-equation]]：10+2 的本质是确保每笔交易的胜率×回报满足交易者方程式。

## 实战应用
在每笔交易入场前，按 12 项清单逐项加减分。减分项（#1-#7）识别风险，加分项（#8、#10）确认优势，#11（leg2 完成度）判断趋势阶段。总分偏低（<50%）时放弃交易，总分中等（~55-65%）时执行但降低仓位，总分偏高（>65%）时正常仓位。

## 来源支撑
- [[journal-huangzongprice-mes-review-collection]]

## 矛盾与待验证
- **"+2" 的含义不明**：所有资料来源中，"10+2" 的具体含义未被解释——是指 10 个评分项 + 2 个标签项（#9 1ABR + #12 腿型标签），还是 10 项加减分 + 2 项附加检查？待 huangzongprice 确认。
- **评分权重未公开**：#6（BO/mkt regime）和 #7（late leg）的权重标注为 -10% 至 -20%，但触发 -20% 的具体条件不明。
- **与其他评分系统关系**：10+2 的 #1-#5 维度与 signal-scoring-synthesis 的 K 线评分（#2、#3）重叠，但权重分配方式完全不同——两者独立使用还是互补使用？待确认。
- **通过阈值缺失**：未发现明确的「总分低于 X% 放弃交易」的硬规则，似乎是结合上下文做最终判断。
