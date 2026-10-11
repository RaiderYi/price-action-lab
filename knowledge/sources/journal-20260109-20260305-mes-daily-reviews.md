# MES 每日复盘集（2026.01.09 - 2026.03.05）

## 元信息
- 作者：huangzongprice（手写笔记 + Gemini AI 辅助分析）
- 日期：2026-01-09 至 2026-03-05（约 40 个交易日）
- 原始位置：`raw/books/huangzongprice/MES20*.md`
- 文件数量：40+ 篇
- OCR 质量：⚠️ PDF 提取有损坏 — 中文乱码严重，英文术语和数字基本可读
- 品种：MES（Micro E-mini S&P 500）期货，5 分钟为主周期 + 1 分钟辅助
- 分析方法：Al Brooks 价格行为学
- 标签：每日复盘、实盘日志、AI 辅助分析

## 一句话摘要
huangzongprice 在两个月的 MES 日内交易中，以 Al Brooks 方法论进行每日复盘，逐步形成了一套固定的复盘模板（日型分类 → K线级标注 → MC 10+2 评分 → Gemini AI 交叉验证），记录了 40+ 个实盘交易日的决策与结果。

## 复盘模板结构

每篇复盘遵循一致的格式：

```
1. 日型分类（Day Type）
   └── MES 5 Min: <类型标签>

2. K线级逐棒标注
   └── B1-B4 AIS ... B12 L1 sell STP ... B28 BE 2R ...
   └── 包含：入场/止损/止盈/移动止盈/离场信号

3. MC 10+2 评分（Micro Channel 质量检查清单）
   └── MC10+2 -5%K, -5% Cprior, -5% doji, -10% BO regime, ...
   └── ±5% price control, +5% time control, leg2 65% ...

4. 多维上下文
   └── ATM Straddle（隐含波动率）
   └── TR 45min/5min 位置
   └── SPB 5点小回撤趋势判断（首2小时缺口检查）
   └── SPY 联动参考
   └── Brooks Trading Course 视频引用

5. 交易结果
   └── 入场时间 × 信号类型 × 结果（±R）

6. Gemini AI 交叉分析（+gemini 版本特有）
   └── 四段式：Context → Signal → Trade Mgmt → Probability
   └── 对关键 K 线的 AI 解读
   └── 陷阱识别（L1 Trap, Climax Trap, Failed Wedge Trap）
```

## 日型分类体系

复盘覆盖的日型分布：

| 日型 | 频率 | 核心特征 |
|------|------|---------|
| **bear trend from the open then HL MTR** | 高 | 开盘空头趋势 → 日内形成 Higher Low → MTR 反转 |
| **trend trading range all day** | 高 | 全天倾斜型 TR，方向偏但非强趋势 |
| **bull trend from the open then trading range** | 中 | 开盘多头趋势 → 中后段转为区间 |
| **climactic reversal then trading range** | 中 | 开盘高潮反转 → 随后进入 TR |
| **small pullback bear/bull trend** | 中 | 小回撤强趋势（SPB 日） |
| **trading range all day** | 低 | 全天标准区间震荡 |
| **wedge bottom then HL MTR** | 低 | 楔形底 → HL 确认 → MTR 上行 |
| **bull broad channel all day** | 低 | 全天宽通道上行 |
| **sell climax from the open then HL MTR** | 低 | 开盘卖出高潮 → HL → MTR |

**关键观察**：最频繁的两种日型是 "bear trend from the open then HL MTR" 和 "trend trading range all day"，说明 2026 Q1 的 MES 以开盘单向推动+日内反转为主要节奏。

## 核心论点 / 可提取的知识

### 1. MC 10+2 评分系统

huangzongprice 在每篇复盘中反复使用一套 Micro Channel 质量评分：

```
MC 10+2 评分项：
-5% K          — K线质量（实体/影线）
-5% Cprior H/L — 收盘与前高/低的关系
-5% doji       — 十字星扣分
-10% no tick gap — 无tick缺口扣分
-10% BO regime — 突破失败/TR 环境扣分
-5%/wedge      — 楔形/衰竭扣分
-5% late leg   — 末段腿扣分
+5% price control — 价格控制力加分（影线短/实体大）
+5% time control  — 时间控制力加分（速度/角度）
+5% 1ABR           — 1倍平均棒线范围达标加分
Leg2 65%           — 第二腿概率评估

总计可能超过12项（10基础+extra），故称"10+2"
```

这套评分在实战中用于判断通道是否"足够紧"→ 顺势突破 vs 区间回摆的博弈。

### 2. SPB 日识别清单

SPB（Small Pullback）日 = 单边小回撤趋势日。huangzongprice 的识别规则（直接引用原文）：

```
1. Start from TR
2. Open gap; When there are 2 gaps or one gap and one body gap
   in 1st 2 hours, 60% chance small pullback trend will last all day
3. Parallel to EMA
4. Seems to be a failure soon → 假象（实际延续）
5. H1/H2/L1/L2 are strong (TRES setup)
```

### 3. TRES 设置

当 H1/H2/L1/L2 四个级别的信号都强劲时，市场处于高概率状态：
- 顺势方向 = 明确的 Always In 方向
- 回调到 EMA 附近的高2/低2 = 高胜率入场
- 适用于 SPB 日和强趋势日

### 4. Gemini AI 的分析方法论

Gemini 对每笔关键交易的评注遵循 **四段式框架**：

| 阶段 | 英文标签 | 分析内容 |
|------|---------|---------|
| A | Context Recognition | 判断市场环境（趋势/TR/高潮/通道） |
| B | Signal & Entry Quality | K线质量、入场位置、确认信号 |
| C | Trade Management | BE 止盈时机、追踪止损、仓位缩放 |
| D | Mathematical Expectancy | 胜率×赔率 vs 风险、Scalp vs Swing 判断 |

Gemini 也系统性地标注了**陷阱模式**：
- **L1 Trap**：首次回撤做顺势（L1/H1）→ 实则假突破/高潮反转
- **Climax Trap**：高潮K线后追入 → 被 TBTL 反转吃掉
- **Failed Wedge Trap**：趋势末段楔形 → 突破失败→原方向延续
- **Second Leg Trap**：第二腿信号 → 实则 Complex Pullback 中的一个陷阱

### 5. 实战交易统计印象

从 40+ 篇复盘中提取的交易结果模式：

| 信号类型 | 常见结果 |
|---------|---------|
| H2 buy STP（多头趋势中） | +2R ~ +3R |
| L2 sell STP（空头趋势中） | +1R ~ +3R |
| L1 sell STP（高潮后） | -1R 到 +1R（高波动） |
| wedge bull/bear flag | 1R ~ 2R |
| STC（Sell/Buy The Close） | 1R ~ 4R（极端波动） |
| OB（Outside Bar）突破 | -1R 到 +1R（高不确定性） |
| failed wedge | -1R（陷阱→反向才是正确方向） |

**关键教训**：
- L1/H1 入场在非极端趋势中容易被"Second Leg Trap"击杀
- STC（Buy/Sell The Close）在确认高潮反转后胜率极高
- 突破失败（Failed BO）是比原方向更可靠的交易信号
- ATM Straddle < 0.4% 的"Chop Day"应减少交易频率

### 6. 心理学/纪律引用

每篇复盘末尾常见：
- **"Best Loser Wins"** — Tom Hougaard 的止损纪律哲学
- **"For where your treasure is, there will your heart be also"** — 仓位管理/心理平静
- **Brooks Trading Course 视频编号引用**（如 14B, 14E, 37A, 42B 等）

## 提取出的新概念

以下概念为本次 ingest 首次系统引入 Wiki：

| 概念 | 说明 |
|------|------|
| [[spb|SPB]] | SPB 日 5 点识别清单 + 60% 全天延续概率规则 |
| [[rs-scoring]] | MC 10+2 Micro Channel 质量评分系统 |
| [[journal-20260109-20260305-mes-daily-reviews]] | H1/H2/L1/L2 全部强劲的特殊市场状态 |
| [[journal-20260109-20260305-mes-daily-reviews|Four-stage review]] | Gemini AI 四段式复盘框架（Context→Signal→Mgmt→Expectancy）|

## 对已有概念的加深

| 已有概念 | MES 复盘补充 |
|----------|------------|
| [[climax]] | 实战中的 climax 识别：Range > ABR×1.5~2 + 紧通道 = 高潮 |
| [[three-push-wedge|Three Push Wedge]] | Failed Wedge Trap 的完整实战案例；楔形末段=衰竭信号（非入场信号） |
| [[major-trend-reversal|Major Trend Reversal]] | HL MTR 的实战确认流程（HL 形成→L2/H2 入场→移动止盈到新 HL） |
| [[trend-from-the-open]] | SPB 日的 5 点识别清单扩展了开盘趋势的判断框架 |
| [[micro-channels]] | MC 10+2 评分提供了量化 MC 质量的实战工具 |
| [[TBTL]] | 多次在高潮反转后使用 TBTL 确认二腿入场 |
| [[breakout-mechanics]] | Failed BO 作为反向信号的反复实战验证 |
| [[protective-stops]] | 大量 BE 移动止盈实战案例（1R→BE→Trailing） |
| [[always-in]] | AIL/AIS 标注在每篇复盘中用于总体方向判断 |
| [[measured-move]] | 大量 MM 投影用于目标位设定（1R MM, 2R MM, 3R MM） |

## 与现有知识的冲突

无原则性冲突。MES 复盘中的实战观察完全一致地验证了 Brooks 理论框架。

一个值得关注的细微差异：huangzongprice 的 MC 10+2 评分体系比 Brooks 原著中的 MC 描述更为**量化和系统化**——Brooks 原著更侧重于定性描述（"紧"vs"宽"），而 huangzongprice 在实践中发展出了逐项加减分的清单。这可能是从 Brooks 理论到量化落地过程中的自然演进。

## 待办

- [ ] MC 10+2 评分的精确权重（各 ±5%/10% 的实际数值含义）需查看 Pine Script 源码确认
- [ ] PTM 引用系统（如 `PTM20241222`, `PTM20250525`）的含义待确认——可能是个人 Price/Time Matrix 笔记体系
- [ ] SPY 联动规则（"SPBKK Kaverage bar"）的具体定义待查
- [ ] 若能在后续获得 Gemini 的完整中文原文，可大幅提升这些复盘的可读性
