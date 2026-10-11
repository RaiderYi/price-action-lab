---
title: "PTM 先前交易记忆系统"
phase: [trend, range, breakout, transition]
signal_types: [pullback-entry, swing]
tags: [ptm, 每日复盘, brooks, context, prior]
difficulty: intermediate
related: [multi-timeframe-context, brooks-four-step-context, execution-engine-architecture, trading-journal-format, journal-mes-daily-reviews, mes-daily-review-workflow, brooks-signal-catalog, ctx-scoring, climax, major-trend-reversal, journal-mes-daily-review-collection]
char_count: 2147
---
# PTM 先前交易记忆系统

## 一句话定义
通过日期编号交叉引用历史上相似市场背景的复盘记录，构建个人化的市场模式记忆库——Brooks PA 方法的个人落地版。

## 核心要点
- 格式：`PTM + YYYYMMDD`（如 `PTM20241201`、`PTM20241222`）
- 作用：当当前市场与历史上某日背景相似时，引用那天的复盘结论作为参考
- 本质上是一个人工版的"相似市场检索系统"
- 常见引用场景：S/R 成本背景（`cost context`）、宏观形态（`PTM20241201` 的 3 摆动点规则）、突破模式（`PTM20241215` 的 K1-2K3K）

## PTM 引用类型

| PTM 编号 | 内容 | 引用场景 |
|----------|------|---------|
| PTM20241201 | 高 TF/LTF 3 swing points 规则 | 识别多 TF 共振的摆动点 |
| PTM20241208 | 趋势恢复 = 失败反转 = 回调 | 测试成功/失败的判断 |
| PTM20241215 | K1-2K3K 突破确认三棒规则 | 突破是否有效的判断 |
| PTM20241222 | 成本背景（Cost Context） | S/R 位置的成本基础分析 |
| PTM20250105 | 模糊性原则、周期性波动原则 | 不确定市场中的决策框架 |
| PTM20250412 | （未明确，与前 PTM 共同引用） | 宏观背景对比 |

## 与相关概念的关系
- [[multi-timeframe-context]]：PTM 经常在 45min/15min 的宏观背景判定中被引用，帮助确认多 TF 框架的判断
- [[brooks-four-step-context]]：PTM 可视为 Brooks 四步法的"记忆增强"——将 Step1（价位）的历史 S/R 延伸到具体日期
- [[execution-engine-architecture]]：量化版 PTM 等价于 Context Engine 中基于历史 S/R 的背景判断
- [[trading-journal-format]]：PTM 是复盘格式中的跨日期链接层

## 实战应用
每天复盘时，如果当前市场形态让你联想到过去的某个交易日，写下 `PTM + 日期`。后续遇到相似形态时，翻看 PTM 引用的日期，验证自己的判断是否一致。PTM 网络越密，对市场的"似曾相识感"越强，入场信心越高。

## 来源支撑
- [[journal-mes-daily-reviews]]（151 份 MES 每日复盘中的跨日期引用）

## 矛盾与待验证
- PTM 系统目前完全依赖人脑记忆——没有自动化检索工具
- 一个可探索的方向：将 PTM 引用数字化，建立"市场日型相似度搜索引擎"，在 A 股分析系统中实现自动 PTM 匹配
- PTM 网络当前仅约 6 个节点，覆盖面有限。随着复盘日增加，PTM 网络密度应自然增长


---

## Merged Content (from ptm-prior-trading-memory)

# PTM (Prior Trading Memory) — 跨期交易记忆对照法

## 一句话定义
遇到当前形态时主动回忆历史上相似形态的日期和教训，实现 Brooks 所说的 "screen time" 积累。

## 核心要点
- PTM = Prior Trading Memory，是 huangzongprice MES 每日复盘的核心学习方法
- 每条 PTM 记录包含：日期 + 形态描述 + 关键教训
- 通过跨期对照，将离散的每日复盘编织成持续的学习曲线
- PTM 不仅回忆相似形态，更回顾当时的决策结果（盈/亏/陷阱）

## 与相关概念的关系
- [[mes-daily-review-workflow]]：PTM 是复盘工作流的记忆索引层
- [[brooks-signal-catalog]]：PTM 对照的是具体信号类型在不同背景下的成功/失败案例
- [[ctx-scoring]]：PTM 帮助识别"相同信号+不同背景"会导致不同结果
- [[climax]]：PTM 中最常见的对照主题——高潮后总是进入 TR 的历史验证
- [[major-trend-reversal|Major Trend Reversal]]：PTM 中 HL MTR 的对照频率最高

## 实战应用
复盘时遇到当前架构，追问"上次见到这个形态是什么时候？那次结果如何？"——用日期标注（如 PTM20250302）建立记忆锚点。

## 来源支撑
- [[journal-mes-daily-review-collection]]
- 复盘中出现 PTM 标注的日期：2025-12-22, 2025-01-12, 2025-01-26, 2025-02-16, 2025-03-02, 2025-05-18, 2025-05-25

## 矛盾与待验证
暂无。
