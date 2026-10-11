# MES 每日复盘合集

## 元信息
- 作者：huangzongprice
- 日期：2025-08-06 ~ 2026-03-05（约7个月，150+ 天）
- 原始位置：`raw/books/huangzongprice/MES*复盘*.md`
- 品种：MES（Micro E-mini S&P 500 期货）
- 主时间框架：5 分钟（部分早期和后期含 1 分钟）
- 图表工具：SC2（部分标注 "by SC2"）
- AI 辅助：部分复盘含 Gemini AI 分析（标注 "+gemini"）

## 一句话摘要
huangzongprice 历时7个月的 MES 日内交易实盘复盘记录——每天用 Brooks 价格行为术语逐棒标注图表，部分引入 Gemini AI 做入场质量分析。

## 核心论点

### 1. 复盘方法论

每份复盘遵循统一结构：

```
MES 5 Min: [一句话市场类型描述]
[图表区域 — 逐棒标注]
  B# L1/L2/H1/H2 buy/sell STP/STC, 1R/2R/BE
  MC 10+2 评分: -5%/+5% 各项加减分
[结果记录区 — 最终 P&L 汇总]
[Gemini 注释区 — AI 对具体入场的分析（部分文件）]
```

### 2. 标注体系（huangzongprice 自定义记法）

| 记法 | 含义 |
|------|------|
| `B#` | 第 # 根 K 线 |
| `H1/H2/H3` | 多头第一次/二次/三次入场（High 1/2/3） |
| `L1/L2/L3` | 空头第一次/二次/三次入场（Low 1/2/3） |
| `buy/sell STP` | 止损入场单 |
| `STC` | 止损收盘（Stop Close） |
| `1R/2R/3R/4R` | 盈亏倍数（risk multiple） |
| `BE` | 保本（Breakeven） |
| `AIL/AIS` | Always In Long/Short |
| `SPB` | Small Pullback Bull/Bear（小回撤趋势） |
| `OB` | 外包棒（Outside Bar） |
| `BB` | 竹节（Barbwire） |
| `TTR` | Tight Trading Range |
| `TBTL` | 十棒两腿 — Post Climax 反转确认 |
| `MTR` | 主要趋势反转（Major Trend Reversal） |
| `TRI` | 三角形/扩散三角形 |
| `LTR-UTR` | Lower TR ↔ Upper TR 切换 |
| `BOM` | Breakout Mode（突破模式） |
| `PTM[日期]` | Playbook Trade Mark 引用 |

### 3. MC 10+2 评分系统

每个关键波段附有 MC（Market Cycle）评分，格式为：

```
MC 10+2 [各项评分]
```

常见加减分项（±5% 或 ±10%）：
- **K 线形态**：K 线质量、十字星 (doji)
- **与前一棒关系**：C prior H/L（收盘相对于前高/前低）
- **缺口**：no tick gap (-10%)
- **突破标记**：BOmrk regime（-10% 或 +5%）
- **阶段**：late leg（-10%）、wedge（-5% 或 -10%）
- **价格控制**：price control major swing point（+5%）
- **时间控制**：time control leg2（45%~65%）
- **1ABR**：1 倍 ATR（+5%）

### 4. Gemini AI 辅助复盘

部分文件（标注 "+gemini"）包含 Gemini AI 对具体入场点的分析，体现：
- **入场时机分析**（Timing & Trap Analysis）：如"Bull Surprise"确认、假突破陷阱
- **背景验证**：引用 Brooks 原文（如"Climax usually leads to TBTL"）
- **执行缺陷标记**：如标注"The Execution Flaw"记录未按规则执行的情况
- **交易心理**：引用 Tom Hougaard "Best Loser Wins" 理念

### 5. 涵盖的市场日类型

从 150+ 天复盘中提取的日类型（按 Brooks 分类）：

| 日类型 | 示例文件 | 出现频率 |
|--------|---------|---------|
| 趋势交易区间日 (TTRD) | 20250821, 20251021, 20251031 | 最高频（约30%） |
| 开盘趋势日 (bull/bear from open) | 20250808, 20250826, 20250904 | 高频（约20%） |
| 楔形顶/底 → 反转 | 20250811, 20250819, 20250919 | 中频 |
| 买入/卖出高潮 → TBTL | 20250926, 20251110, 20251119 | 中频 |
| 区间全天 | 20250818, 20250829 | 低频 |
| MTR（主要趋势反转） | 20251106, 20251111, 20260305 | 低频 |
| 扩散三角形 (TRI) | 20250806, 20251017, 20251202 | 低频 |
| FOMC/新闻日 | 20250917, 20251029 | 极少 |
| V 反转 | 20251015 | 极少 |

### 6. 交易心理与管理

复盘中反复出现的交易心理要素：
- **"For where your treasure is, there will your heart be also"**（马太福音 6:21）— 多个文件末尾出现，提醒交易者心态与价值观
- **"Best Loser Wins"**（Tom Hougaard）— 接受亏损、快速止损是盈利前提
- **止损位移规则**：BE → 0R → 1R，层层推进
- **Rule of 4**：15 分钟内未达预期则退出

## 提取出的新概念

以下概念为 MES 复盘合集首次系统化提取：

| 概念 | 说明 |
|------|------|
| [[rs-scoring]] | MC 10+2 K线评分记法：逐棒加减分的量化复盘系统 |
| [[journal-mes-daily-reviews|AI-assisted review]] | AI（Gemini）辅助交易复盘：入场分析、陷阱识别、Brooks 引用验证 |
| [[journal-mes-daily-reviews]] | Brooks 日内复盘框架：标题→标注→MC评分→结果→AI分析的完整流程 |

## 对已有概念的补充

| 已有概念 | MES 复盘补充 |
|----------|------------|
| [[trending-trading-range-days]] | 150 天中 TTRD 占比约 30%，是最高频日型；细分出 LTR-UTR TTRD 子类型 |
| [[three-push-wedge|Three Push Wedge]] | 楔形顶/底作为日内反转触发信号频繁出现，实盘中的假楔形 vs 真楔形案例丰富 |
| [[climax]] | 买入高潮后 TBTL 横向整理再突破的实际演变过程可视化 |
| [[major-trend-reversal|Major Trend Reversal]] | HL MTR 和 LH MTR 在实盘中的逐棒演变过程被完整记录 |
| [[always-in]] | AIL/AIS 在多时间框架（1min + 5min）中的协同使用 |
| [[spike-and-channel]] | 尖峰期高动能→通道期双向交易的切换点被精确标注 |
| [[late-breakout]] | 尾盘突破作为独立日型出现多次（如 20251014, 20251027） |
| [[final-flag]] | 趋势末期 TR → 突破失败的实盘案例 |
| [[opening-reversals]] | 开盘 60-90min 内反转的逐棒标注 |
| [[trading-range-quality]] | LTR-UTR 双区间框架的实际应用 |

## 与现有知识的冲突

无明显理论冲突。复盘是 Brooks 理论的实盘验证——大部分日型都能在 Brooks 框架中找到对应分类。值得关注的是：

- **TTRD 高频性**：趋势交易区间日是最常见的日型（30%），远超 Brooks 书中描述的"常见"，这可能与 2025-2026 期间 MES 市场特征有关
- **AI 辅助复盘的局限性**：Gemini 分析偏定性且依赖 OCR 文本质量——中文 OCR 损坏导致部分分析无法关联到具体 K 线

## 独特价值

1. **Brooks 理论 → 实盘操作的桥梁**：理论概念如何在逐棒层面落地执行
2. **MC 评分系统的完整实例**：看量化评分如何在每一段走势中应用
3. **7 个月连续复盘的纪律性**：每天坚持复盘本身就是一种训练
4. **AI 辅助交易复盘的前沿探索**：huangzongprice 可能是最早将 Gemini 用于 MES 日内复盘的系统性实践者
5. **跨时间框架操作记录**：1min 和 5min 之间的信号传导与虚假信号辨别
