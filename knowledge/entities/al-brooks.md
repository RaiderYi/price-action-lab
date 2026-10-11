# 阿尔·布鲁克斯

## 身份/定义
Al Brooks（阿尔·布鲁克斯），美国价格行为学（Price Action）交易教育者。前眼科医生转行全职交易员，著有《Reading Price Charts Bar by Bar》等系列教材，是当代价格行为学最有影响力的传播者之一。

## 核心贡献/观点
- **裸K交易哲学**：不看指标，仅凭K线形态、市场结构和上下文判断方向
- **信号类型系统**：定义了 H1/H2/L1/L2、楔形、高潮反转、TR Fade 等可学习的入场模式（见 [[brooks-signal-catalog]]）
- **四步分析法**：趋势→区间→反转→上下文，层层递进地分析市场
- **80/20 规则**：交易区间边界的第3–4次测试为最优逆势入场点
- **交易区间理论**：区间=任何存在双向交易的区域，不确定感是其标志。真空效应、紧密TR、突破模式等子概念构成完整的区间分析框架（见 [[trading-range-characteristics]]）

## 代表作品
- [[book-brooks-reading-price-charts]]：《Reading Price Charts Bar by Bar》（英文原版，2009，428页）——Brooks 奠基之作，完整覆盖 15 章
- [[book-brooks-reading-price-charts-cn]]：同上书 Google 机翻中文版（逐条阅读价格图表），提供中文术语对照
- Brooks 价格行为三部曲（Wiley Trading Series，2012）：
  - 《Trading Price Action Trends》（趋势篇）→ [[book-brooks-trends]]（OCR 失败，待修复）
  - 《Trading Price Action Trading Ranges》（区间篇）
  - 《Trading Price Action Reversals》（反转篇）→ [[book-brooks-reversals]]（已收录，英文原版）
- 图表百科全书：
  - [[brooks-signal-catalog]]（6747 页图表地图集——Brooks 方法论"看图说话"的终极索引）
- 本项目资料：
  - [[article-brooks-pa-verification]]（Brooks 定义 vs 代码实现对照）
  - [[README-summary]]（huangzongprice 基于 Brooks 方法论开发的 MES 量化策略）
  - [[integration-summary-20260306]]（策略从 MES 扩展到 BTC + A股 多市场系统的完整历程）
  - [[course-notes-PA-study]]（Brooks 全套课程笔记，92页，57个章节的完整教学体系）
  - [[encyclopedia-al-10-best-setups]]（Al Brooks 10 大交易架构实战解析，44页图解）
  - [[encyclopedia-brooks-price-action-manual]]（Brooks 本人撰写的 26,000 词免费手册，108 页，25 章——系统阐述其整个交易哲学）
  - [[article-20200818-brooks-10-best-pa-patterns]]（Brooks 博客原文——10 大形态的最浓缩官方总结，2020 年发表）
  - [[brooks-signal-catalog]]（图表百科全书——Brooks Trading Course 全幻灯编译，4777 页，~100 模式×4 变体 = ~400 条目，按字母分类的终极参考指南）
  - [[course-slides-brooks-price-action-fundamentals]]（Brooks Trading Course 完整视频幻灯片，5414 页，53 视频组——最权威的原始教学资料）
  - [[article-20240315-price-action-intro]]（PA 入门全景——将 Brooks 与 Beggs、Seiden 并列为三大流派之首）
  - [[article-20200830-brooks-price-action-definition]]（Brooks 博客——什么是价格行为？基础入门文章，系统阐述 PA 的宽泛定义、六个核心方面、80% 法则、市场惯性与测试机制）

## 与其他实体的关系
- **理查德·威科夫**：Brooks 的价格行为学继承并简化了威科夫的供需区/吸筹派发框架
- **Brooks 教学体系**：课程笔记 [[course-notes-PA-study]] 完整记录了从术语、K线基础到通道、高潮、交易管理的全套理论
- **交易社区**：Brooks 的方法论催生了大量量化实现（如 huangzongprice 的 MES → BTC/A股 多市场系统），形成了"原教旨主观派"与"量化编码派"的分歧。参见 [[integration-summary-20260306]] 中 Flask + WebSocket 实时推送进一步推向量化自动化的趋势
