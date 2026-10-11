# MES 每日复盘语料库（黄宗 2025.08-2026.03）

## 元信息
- 作者：huangzongprice（黄宗）
- 日期：2025-08-06 ~ 2026-03-05（跨7个月，151个交易日）
- 原始位置：`raw/books/huangzongprice/MES*.md`（302文件：151 .md + 151 .pdf）
- 标的：MES（Micro E-mini S&P 500）5分钟 + 1分钟K线
- 辅助分析：约50%的复盘含 Gemini AI 辅助分析（`+gemini` 标记）

## 一句话摘要
151个交易日的 Brooks 价格行为学实战复盘语料库——每日标注日型（regime）、信号入场、ATM波动率环境和 Gemini 辅助分析。

## 核心论点

### 日型分类（151天统计）

| 日型大类 | 英文标签 | 大致占比 | 典型范例 |
|---------|---------|---------|---------|
| 趋势交易区间日 | trend trading range all day (TTRD) | ~35% | LTR-UTR TTRD / bear broad channel |
| 开盘趋势+TR | bear/bull trend from the open then TR | ~25% | bear from open then HL MTR |
| 纯交易区间 | trading range all day | ~10% | TR all day |
| 高潮反转+TR | climactic reversal then TR | ~8% | sell climax then HL MTR |
| 楔形反转 | wedge bottom/top then ... | ~8% | wedge bottom then HL MTR |
| 开盘趋势+恢复 | trend from open then trend resumption | ~5% | bear from open then LL MTR |
| 其他 | expanding TRI/bull trap/FOMC day | ~5% | FOMC trading range day |

### ATM 跨式波动率（5min 背景过滤）
- 范围：0.31% ~ 0.90%
- 中位数：~0.62%
- 高波动日（>0.80%）：通常对应 FOMC 日或关键数据日
- 低波动日（<0.50%）："Chop"信号，TR 日概率 >80%

### Gemini AI 辅助分析模式
约50%的复盘文件包含 `+gemini` 标签，典型输出结构：
1. **Timing & Trap Analysis**：识别入场时机和陷阱
2. **Context 判断**：高潮后 TBTL、TR 环境确认
3. **Micro-Execution**：逐根K线的微观执行细节
4. **Signal Bar Veto**：信号棒否决条件（如逆势K线否决顺势入场）

### 重复出现的交易格言
- "For where your treasure is, there will your heart be also." — 每篇复盘固定引用
- "Best Loser Wins" — Tom Hougaard 理念，数篇引用
- "1R vs 2R / Leg 2" — Brooks 关于腿2的回报评估

### 信号密度分布
- 日均信号数：0~12 条
- 中位数：~2 条/天
- 高信号日（>5条）：通常对应趋势日或大幅摆动日
- 零信号日：通常为窄幅 TR 日

## 提取出的新概念

**全新概念（3）**：
- [[corpus-mes-daily-reviews]] — Brooks 日型分类体系（151天实证总结）
- [[atm-straddle-gauge]] — ATM跨式波动率作为日内环境过滤工具
- [[journal-huangzongprice-mes-reviews]] — huangzong 的每日复盘方法论（初版+Gemini增强）

**新增实战数据支撑（~20个已有概念）**：
[[always-in]] · [[climax]] · [[three-push-wedge|Three Push Wedge]] · [[major-trend-reversal|Major Trend Reversal]] · [[trend-from-the-open]] · [[trending-trading-range-days]] · [[trading-range-quality]] · [[trend-resumption]] · [[opening-reversals]] · [[final-flag]] · [[spike-and-channel]] · [[breakout-mechanics]] · [[measured-move]] · [[channel]] · [[protective-stops]] · [[tbtl]] · [[end-of-day-patterns]] · [[trend-maturity]] · [[buying-selling-pressure]] · [[signal-bars]]

## 与现有知识的冲突
**无冲突**。此为 Brooks 理论在 MES 实盘中的验证语料库——151天中未发现与 Brooks 理论矛盾的模式。
**发现**：TTRD（趋势交易区间日）占比高达 ~35%，远超 Brooks 教材中暗示的频率——这是最需要熟练掌握的日型。
