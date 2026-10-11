---
title: "信号分级系统（Signal Grading System）"
phase: [trend, range, transition]
signal_types: [wedge, swing]
tags: [lfin, abc, sfin, 等级, 执行引擎]
difficulty: intermediate
related: [signal-scoring-synthesis, signal-reliability-pipeline, execution-scoring, cycle-strategy-gating, signal-priority-system, wedge-gravity-dual-core, article-huangzongprice-wedge-gravity-v2-master, article-20260519-wedge-gravity-v41-flowchart, ctx-scoring, background-permission, fsm-strategy-constraints, article-20260519-wedge-gravity-brooks-v1-pine]
char_count: 3295
---
# 信号分级系统（Signal Grading System）

## 一句话定义
将最终信号评分 `lFin`/`sFin` 按固定阈值映射为 A/B/C 三级，通过可选的最低等级过滤屏蔽弱信号。

## 核心要点
- **三级阈值**（硬编码，不可调）：
  | 等级 | 阈值 | 含义 |
  |------|------|------|
  | A | lFin/sFin ≥ 0.80 | 强信号——多因子共振、高置信 |
  | B | lFin/sFin ≥ 0.60 | 中等信号——核心条件满足 |
  | C | < 0.60 | 弱信号——勉强过触发阈值但可靠性低 |
- **等级判定**：`lGrade = lFin >= 0.80 ? "A" : lFin >= 0.60 ? "B" : "C"`
- **等级过滤**：通过 `i_useGradeFilter`（默认关闭）和 `i_gradeMin`（默认 "C"）控制——设为 "B" 时屏蔽所有 C 级信号，设为 "A" 时仅允许 A 级
- **过滤实现**：`gradeOKL = not i_useGradeFilter or lRank >= gradeRank`——关闭时所有等级放行
- **等级在入场标签中展示**：`Grade: A/B/C`，与结构名、趋势/反转类型并列

## 与相关概念的关系
- [[signal-scoring-synthesis]]：分级系统的输入是 `lFin`/`sFin`（信号评分合成的最终输出）——评分决定分数，分级决定是否放行
- [[signal-reliability-pipeline]]：7层信号可靠性管道的第7层——分级过滤是管道最末端的质量闸门
- [[execution-scoring]]：v3 执行引擎继承了 ABC 分级系统，将 `execScore` 同样映射为 A/B/C，并引入与结构分的联动（A 级结构分更高、C 级被降权）
- [[cycle-strategy-gating]]：分级过滤是 7 层信号可靠性管道的第 6 层——位于失败过滤/重叠过滤/关键位过滤之后、确认K线之前
- [[signal-priority-system]]：V4.1 的 5 级信号优先级体系是本分级系统的上位替代——从 3 级信号质量分级升级为 5 级完整决策层级（硬规则→逃生→结构→背景→信号）
- [[wedge-gravity-dual-core]]：分级系统是双核架构中软评分核的输出后处理——不影响分数计算，仅影响最终信号是否触发

## 分级在各版本中的使用
| 版本 | 分级系统 | 默认状态 | 备注 |
|------|---------|---------|------|
| V2 Master | A/B/C 三级 + 等级过滤 | 过滤关闭 | 首次引入，`i_useGradeFilter=false` |
| v3 执行引擎 | A/B/C 三级 + 等级联动结构分 | 默认启用 | 等级影响 structScore，C 级扣分 |
| V4.1 | 5 级优先级体系 | 默认启用 | 取代 ABC 分级，增加硬规则/逃生层 |

## 实战应用
调试信号频率时，若信号过多（噪音交易），开启 `i_useGradeFilter=true` 并设 `i_gradeMin="B"` 可过滤约 40-60% 的弱信号。若信号过少，检查 `i_gradeMin` 是否误设为 "A"——A 级信号在大多数品种上稀少（日均 0-2 次），适合波段交易而非日内高频。

## 来源支撑
- [[article-huangzongprice-wedge-gravity-v2-master]]（V2 Master 源码第781-788行——等级判定 + 等级过滤逻辑）
- [[execution-scoring]]（v3 执行引擎的 ABC 分级继承）
- [[article-20260519-wedge-gravity-v41-flowchart]]（V4.1 的 5 级优先级体系——ABC 分级的演进方向）

## 矛盾与待验证
- ABC 阈值（0.80/0.60）是固定值，与 `i_sigThr`（默认 0.40）无联动关系——可能出现 `i_sigThr=0.60` 时 C 级信号全部被信号评分自身过滤（因为 C 级 < 0.60 = 阈值），导致分级过滤形同虚设。是否需要将分级阈值与触发阈值联动（如 A ≥ thr×1.5）是开放问题
- 各等级的实际胜率/盈亏比无回测数据支撑——A 级信号是否真优于 B/C 级、差距多大，尚无统计验证


---

## Merged Content (from signal-grading)

# 信号分级 ABC

## 一句话定义
将信号综合评分 `lFin`/`sFin` 按阈值映射为 A/B/C 三级字母等级，支持最低等级过滤。

## 核心要点
- **三级阈值**：A 级 ≥0.80 → 高置信信号，B 级 ≥0.60 → 中等信号，C 级 <0.60 → 弱信号/噪音
- **等级与评分的关系**：字母等级是连续评分的离散化投影——A级意味着信号在引力场、K线形态、结构和背景四个维度全部高分
- **可配置最低等级**：`i_gradeMin` 参数支持 "A"/"B"/"C" 三档，设为 "A" 时仅保留最强信号
- **双向独立分级**：多头和空头各自独立评定等级（`lGrade` / `sGrade`），不互相影响
- **与最终触发分阈值独立**：`lFin >= i_sigThr` 和 `lRank >= gradeRank` 是两道独立过滤——前者是连续阈值，后者是离散等级
- **面板展示**：右上角信息面板第 15 行实时显示 `多{等级} / 空{等级}`
- **默认关闭**：`i_useGradeFilter = false`，用户需手动开启信号分级过滤

## 与相关概念的关系
- [[signal-scoring-synthesis]]：分级是评分的「输出层」——`lFin`/`sFin` 算出后，等级立即确定
- [[ctx-scoring]]：Brooks 背景评分影响 lFin/sFin → 间接影响等级——TR 中 ctxScore 低时很难达到 A 级
- [[background-permission]]：分级过滤和背景许可过滤是两道独立闸门——信号可能 A 级但被 Brooks Step4 否决
- [[fsm-strategy-constraints]]：A 级信号在 TR 中可能因方向约束被 `allowLong`/`allowShort` 屏蔽——等级与许可独立
- [[execution-scoring]]：v3 执行引擎的 ABC 三级系统与此概念形成呼应，但评分合成公式不同（v3 三因子 vs V1.5 五因子）

## 实战应用
在信号标签中直接显示等级（如 `Grade: A`），交易员可据此决定仓位大小——A 级满仓、B 级半仓、C 级不交易；结合 `i_gradeMin = "B"` 过滤所有 C 级弱信号。

## 来源支撑
- [[article-20260519-wedge-gravity-brooks-v1-pine]] — Pine Script 源码，第 767–773 行定义等级映射与过滤逻辑

## 矛盾与待验证
- **等级阈值的稳定性**：0.80/0.60 的分割点是经验设定，未经过回测校验——不同品种/时间框架可能需要调整
- **与 v3 执行引擎 ABC 标准的一致性**：v3 的等级划分基于三因子评分（bg×0.55+struct×0.25+sig×0.20），阈值可能不同，需对照验证
