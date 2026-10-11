# MES 每日复盘日志 — Brooks PA 实战日记

## 元信息
- 作者：huangzongprice
- 日期范围：2025-01-05 ~ 2026-03-05（约 14 个月，覆盖 ~145 个交易日）
- 原始位置：`raw/books/huangzongprice/MES*.md`（145+ 文件）
- 原始格式：PDF → pdftotext（部分含 gemini AI 辅助分析）
- 标的：MES（Micro E-mini S&P 500，5 分钟 K 线）

## 一句话摘要
huangzongprice 的 MES 日内交易实战日志，每交易日一份 Brooks PA 标注复盘，包含独特的微上下文评分体系（MC 10+2）、跨期交易管理洞察（PTM）、以及 gemini AI 辅助分析。

## 核心论点

### 1. 日志结构
每份复盘文件遵循统一结构：
- **日级摘要**：一句话市场状态（如 "bear trend from the open then HL MTR"、"trading range all day"、"climactic reversal then trading range"）
- **棒线级标注**：逐棒（B1/B2/...）标注 Brooks PA 信号 — H1/H2/L1/L2 入场、STC/BTC、EMA 交叉、高潮、楔形、旗形、测量走势等
- **MC 10+2 评分**：对重要腿段的微上下文质量打分（见下文）
- **交易记录**：入场/止损/盈亏（STP/BE/1R/2R/i1R）
- **多时间框架**：1min / 5min / 15min / 45min 联动分析
- **日内结构**：开盘区间 → 腿段 → 反转 → TR → 收盘
- **期权语境**：ATM Straddle（隐含波动率参考）

### 2. MC 10+2 微上下文评分体系
这是本日志最独特的分析框架，对每个腿段使用 12 项加权检查清单打分：

```
MC10+2 评分项（示例，以 `-5%` / `+5%` 表示加减分）：
- K线质量 (-5%)：趋势棒/十字星？实体≥1/3棒幅？
- C prior H/L (-5%)：收盘相对于前高/前低的位置
- body/range 比率 (-5%)
- doji (-5%)：出现十字星扣分
- BO mrk regime (-10% 或 -20%)：当前是突破/通道/TR/Wedge？
- late leg (-10% 或 -5%)：腿段末期扣分
- price control (+5%)：价格控制权（谁在主导？）
- swing point (+5%)：是否在关键摆动点？
- 1 ABR (+5%)：波动幅度在平均棒幅以内
- time control (+5%)：时间控制（腿段持续时间）
- leg2 百分比 (55%-65%)：腿2完成度
```

总分通常被编码为 `MC10+2 65%` 等形式，作为入场决策的辅助参考。

### 3. PTM 跨期交易管理
日志频繁出现 `PTM20250112`、`PTM20250420` 等标记，表示跨期关联的交易管理洞察。例如：
- `PTM20250126`：微通道空头棒的特征判断
- `PTM20250412`：逆势限价单不可行 / 止损陷阱 50% 反转规律
- `PTM20250216`：速度（velocity）与加速度（acceleration）的物理学类比
- `PTM20241222`：HTF 上下文对当日框架的影响

PTM 形成了一个跨交易日的「经验数据库」，将单个交易日的教训系统化保存为可复用的经验法则。

### 4. gemini AI 辅助分析
部分复盘文件（约 50 个）附带 gemini 分析段落（标记 `gemini`），提供第二视角的 AI 审查：
- 识别执行缺陷（"The Execution Flaw"）
- 标注意外事件（"The Bull Surprise"、"The Climax Trap"）
- 提供替代入场/出场方案
- 引用 Brooks 原著规则（如 Rule #5、TBTL、AIL 框架）

### 5. 反复出现的实战主题
贯穿 145+ 日复盘的高频主题：
- **80% 反转失败**：趋势中反向入场几乎总是失败
- **高潮后必入 TR**：高潮 → TBTL → 交易区间 → 腿2
- **H2/L2 最可靠入场**：二次信号远优于一次信号
- **TTR 不交易**：紧密交易区间压倒一切策略
- **Measured Move**：腿 1=腿 2 投影反复作为利润目标
- **Best Loser Wins**：交易哲学 — 接受小亏是赢大钱的前提
- **SC2**：反复出现的署名标记，推测为交易导师/策略来源

## 提取出的新概念

以下概念为现有 Wiki 未覆盖、从本日志集合中首次提取：

| 概念 | 说明 | 状态 |
|------|------|------|
| [[rs-scoring]] | MC 10+2 微上下文评分体系 | 🆕 |
| [[trade-management-system]] | PTM 跨期交易管理经验数据库 | 🆕 |
| [[journal-mes-daily-review-202501-202603]] | MES 日内复盘方法论（日志结构+标注规范） | 🆕 |
| [[atm-straddle-gauge]] | ATM Straddle 期权隐含波动率作为日内 PA 语境 | 🆕 |

## 与现有知识的冲突

### 补充而非冲突
本日志是现有 Brooks 理论 Wiki 的**实战应用层补充**，不包含与已有概念矛盾的新理论。关系如下：
- 日志中的所有信号（H1/H2/L1/L2/MTR/楔形/高潮/旗形/TR）均基于已有概念页中记录的理论
- MC 10+2 是已有概念（[[signal-scoring-synthesis]]、[[execution-scoring]]）的实战简化版 — 更偏定性/经验权重、更轻量
- 与 [[al-brooks]] A股分析系统的 30min 框架形成「MES 5min 日内 ⇄ A股 30min 波段」互补

### 缺失的理论基础
日志中反复引用的以下 Brooks 规则/概念在 Wiki 中可能覆盖不足：
- **Leg1 = Leg2 的物理学类比**（速度=距离/棒数、加速度=速度变化率）— Brooks Trading Course 16C 的内容
- **CHOB**（Channel Overshoot and Breakout）— 通道过冲突破形态
- **Gift Bar** — 高潮后的赠送棒（容易被误解为趋势恢复）
- **cavemen** — 原始交易者的价格行为本能反应

## 数据质量说明
- pdftotext 提取：中文/图表标注大量丢失，但 Brooks 英文术语和棒线编号保留良好
- gemini 版：AI 分析为中文撰写，可读性优于纯 OCR 版
- 约 10 个文件存在日期编号错误（如 `MES2050925` 实为 2025-09-25，`MES202060109` 实为 2026-01-09）
