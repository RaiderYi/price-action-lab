# Brooks PA Execution Engine v1 — Pine Script 源码（自包含版）

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6，`//@version=6`）
- 原始位置：`raw/articles/huangzongprice/brooks_pa_execution_engine_v1.txt`
- 代码行数：770 行
- 脚本类型：独立 overlay 指标（自包含背景层，不依赖 `input.source` 外部绑定）
- 后续版本：[[article-huangzongprice-execution-engine-v2-linked]]（v2 两层分离）→ v3 lean linked

## 一句话摘要
huangzongprice Brooks PA 系统的**首个 Pine Script 执行引擎实现**——自包含架构（背景层←→执行层同在一个指标内），H2/L2 + 楔形双路线，三因子加权评分（bg×0.55 + struct×0.25 + sig×0.20）输出 A/B/C 分级信号，18 行信息面板 + 10 条报警条件。

## 核心论点

### 1. 自包含单指标架构（v1 独有，后续版本均放弃）
v1 是 huangzongprice 系统中**唯一将背景层与执行层放在同一个指标内的版本**。整个流水线内嵌：

```
OHLC → ATR/EMA/Donchian/Pivot → 精简背景层 → H2/L2 + 楔形 → 确认评分 → 信号输出
```

- 背景层（Location + Phase + Momentum 三层评分 → bgScore → bgVeto/bgConflict/bgSupport）作为指标的一个代码区段运行，不通过 API 绑定
- 优点：加载一个指标即可获得完整信号
- 缺点：背景逻辑与执行逻辑耦合，后续版本（v2/v3）拆分为两个独立指标

### 2. 精简背景层（内嵌，L115-278）
v1 的背景层是后续 Context Engine v1/v2 的前身，结构一致但更紧凑：

**三层加权**：`bgScore = locScore×0.40 + phaseScore×0.35 + momScore×0.25`

**位置层 (locScore)**：
- 6 个关键价位池：ph0, pl0, donchH(20), donchL(20), ema20, fib50
- `f_distAtr(level, atr)` 归一化所有距离为 ATR 倍数
- 多方取距支撑最近者（pl0/donchL/ema/fib50），空方取距阻力最近者（ph0/donchH/ema/fib50）
- atBullSupport（≤0.60 ATR）→ +0.30；near（≤1.20 ATR）→ +0.18
- midRangeLocation：距 donchMid ≤ donchSpan×0.20 → -0.28
- lateBreakoutLong/Short：追价突破 → -0.20
- 靠近对向阻力/支撑 → -0.28/-0.14
- 目标接近 → -0.16

**阶段层 (phaseScore)**：来自 FSM 四状态机（突破=0/通道=1/震荡=2/新突破=3）
- `phaseIsTrend`（0/1/3）→ 按 health confidence 分三档：0.70/0.45/0.20
- `phaseIsRange`（2）→ 0.35
- 过渡检测：`avgOlp > 0.32` 或 `!emaSteep || emaFlat` 或 `phaseState==1 && avgOlp > 0.30`

**动能层 (momScore)**：
```
momScore = 0.10 + impulseScore×0.30 + trendHealth×0.28 - trendMaturity×0.20 - exhaustRisk×0.18
```
- `impulseScore`：实体占比(0.55) + 收盘位占比(0.45)
- `trendHealth`：EMA陡峭 + 低重叠 + 无衰竭K线
- `trendMaturity`：楔形(0.35) + 追价(0.25) + 衰竭K(0.20) + 目标近(0.20)
- `exhaustRisk`：假突破败(0.40) + 楔形(0.25) + 高重叠(0.15) + 目标近(0.20)

**背景否决 (bgVeto)** — 四种条件任一触发即禁止：
1. 区间中部 + 震荡阶段
2. 反向健康趋势 + 本方向衰竭不高
3. 对向阻力位 + 追价突破
4. 高成熟度(≥0.65)或高衰竭(≥0.60) + 目标接近

**六状态背景许可**（后续版本核心创新，v1 首次实现）：
```
allowLong/Short          = bgSupport && !bgVeto
allowTrendLong/Short     = allow && phaseDir 同向
allowReversalLong/Short  = allow && (phaseDir 反向 || 过渡 || 震荡)
```

### 3. H2/L2 状态机（4 阶段 FSM）
与 v2/v3 相同的 4 阶段有限状态机：

| 阶段 | 多头链 (H2) | 空头链 (L2) |
|------|------------|------------|
| 0 | 等待 Pivot Low | 等待 Pivot High |
| 1 | PL 出现 → 记录 `hRefLow` | PH 出现 → 记录 `lRefHigh` |
| 2 | 上破 high[1] → **H1**，记录 `hRefHigh` | 下破 low[1] → **L1**，记录 `lRefLow` |
| 3 | 回撤 + 再上破 hRefHigh → **H2** | 反弹 + 再下破 lRefLow → **L2** |

- 超时：`i_timeoutH2L2`（默认 25 bars）
- 孕线（insideBar）不推进阶段
- 顺势过滤：`i_requireTrendH2`（默认开）→ H2 仅 `allowTrendLong`；L2 仅 `allowTrendShort`

**H2/L2 结构分**（5 项累加后 clamp01）：
```
structScoreH2 = allowLong(0.30) + allowTrendLong(0.20) + at/nearBullSupport(0.20) + !midRange(0.15) + !targetNearby(0.15)
```

### 4. 楔形检测（纯 Pivot 判定）
v1 的楔形检测与 v2/v3 相同——基于三组 pivot high/low 的时间-价格关系：

- **上升楔形**（偏空）：ph2b < pl1b < ph1b && ph1 > ph2 && pl0 > pl1，跨距 [8, 200]
- **下降楔形**（偏多）：pl2b < ph1b < pl1b && pl1 < pl2 && ph0 < ph1，跨距 [8, 200]

与 V1.5 的区别：v1 不做多维加权评分（对称性/收口/跨度），纯布尔判定 + 简单结构分。`i_wedgeNeedTransition`（默认关）可选强制要求过渡/衰竭背景。

**楔形结构分**：
```
wedgeQuality = wedgeDetected(0.55) + at/nearSupport(0.20) + phaseIsTransition(0.15) + exhaustRisk≥0.50(0.10)
```

楔形使用 `allowReversal*` 许可（非 `allowTrend*`）——因为楔形做的是衰竭反转而非顺势延续。

### 5. 共振机制 (Confluence)
当 H2 与下降楔形（或 L2 与上升楔形）**同一 bar 同时触发** → 双方结构分各 +0.10。这是 v1/v2 独有的机制（v3 是否保留待确认）。

### 6. 信号棒评分（3 项准则）
区别于 V1.5 的 lFin/sFin 五因子合成：

**做多**（满分 1.0）：
- 收盘 ≥ low + 0.75×range → +0.40
- body ≥ avgBody5 × 1.20 → +0.30
- (close−low) ≥ 0.60×range → +0.30

**做空**：对称规则。最低阈值 `i_sigThr`（默认 0.40）。

### 7. 执行评分与等级
三因子加权（与后续版本一致）：
```
execScore = bgScore×0.55 + structScore×0.25 + sigBarScore×0.20
```
- A 级（≥0.80）/ B 级（≥0.60）/ C 级（其余）
- `i_gradeMin` 可选最低等级门槛
- `i_useConfirm`（默认关）启用确认 K 线延迟入场

### 8. 止损/入场/目标
```pine
longSL  = majorSL - max(mintick, 0.5×ATR20)     // 止损在主要摆动低点下方
longEnt = high + max(mintick, 0.1×ATR14)         // 入场在突破高点上方
longRisk = max(longEnt - longSL, 0.5×ATR14)      // 风险 ≥ 0.5 ATR
longTP  = longEnt + 2.0×longRisk                 // 固定 2:1 R:R
```

### 9. 信息面板（18 行）
比 v3（7 行）详细得多：背景状态 / 市场阶段 / 方向 / H2/L2 / 楔形 / 多头结构+等级 / 空头结构+等级 / 背景分 L/S / 执行分 L/S / 信号棒分 L/S / 多头候选 / 空头候选 / 最终信号 / 共振 / 确认K线。

### 10. 显示层
- EMA20（黄色）、Donchian High/Low（橙色）
- 上升楔形三推连线（红色）+ 标签
- 下降楔形三推连线（绿色）+ 标签
- H1/H2/L1/L2 结构标签
- 信号K线高亮框（绿色=多 / 红色=空）+ 信号标签（入/损/盈价位）
- 入场/止损/止盈水平虚线
- Data Window 导出：bgScoreL/S、execScoreL/S、H2/L2结构分、楔形结构分

### 11. 报警条件（10 条）
H2形成 / L2形成 / 上升楔形 / 下降楔形 / 多头候选 / 空头候选 / 做多信号 / 做空信号 / 多头共振 / 空头共振。

## 提取出的新概念
（无——v1 的所有概念已在后续版本和设计文档的 ingest 中提取完毕。本来源页为这些概念提供**原始代码实现溯源**。）

已有概念及其在 v1 中的首次实现：
- [[position-layer-scoring]] — locScore 的完整公式首次出现在 v1
- [[exhaustion-risk]] — exhaustRisk（假突破0.40+楔形0.25+重叠0.15+目标0.20）
- [[trend-maturity]] — trendMaturity（楔形0.35+追价0.25+衰竭K0.20+目标0.20）
- [[late-breakout]] — lateBreakoutLong/Short 的 Donchian 判定逻辑
- [[background-permission]] — 六状态许可（allowLong/Short + trend/reversal 拆分）
- [[execution-scoring]] — 三因子加权（bg×0.55+struct×0.25+sig×0.20）+ ABC 分级
- [[h2-l2-state-machine|H2/L2 State Machine]] — 4 阶段 FSM + insideBar + 超时
- [[three-push-wedge|Three Push Wedge]] — 纯 Pivot 判定楔形（不做多维评分）
- [[fsm-market-cycle]] — 四状态机（突破/通道/震荡/新突破）
- [[confluence-trading]] — H2+楔形 同 bar 共振 +0.10
- [[signal-scoring-synthesis]] — 三因子 vs V1.5 五因子（lFin/sFin）

## 与现有知识的冲突
- **自包含 vs 两层分离**：v1 的背景评分内嵌在指标内，v2/v3 拆分为独立 Context Engine + `input.source` 绑定。[[execution-engine-architecture]] 中记录了这一架构演进。
- **背景评分的精确度和范围**：v1 的背景层是精简版（仅 164 行），v2/v3 的 Context Engine 大幅扩展了评分微细则和否决条件。v1 中没有「引力场触发」加分项（该概念在 V1.5 的 WG_V15 中引入，v2 的 Context Engine 中统一合并）。
- **信号棒评分简化**：v1 的 3 项准则 vs V1.5 的 lFin/sFin 五因子合成（多出引力加成 + 趋势反转加成）。[[signal-scoring-synthesis]] 中标注了此差异。

## 版本定位

| 版本 | Context | Execution | 架构 | 行数 |
|------|---------|-----------|------|------|
| V1.5 WG | 单指标内嵌 | 单指标内嵌 | 双核（硬规则 FSM + 软评分量化）| ~1200 |
| **v1 (本页)** | **单指标内嵌（精简）** | **单指标内嵌** | **单核自包含** | **770** |
| v2 | 独立 Context Engine v2 | 独立 Execution Engine v2 | 两层分离（25 input.source）| Context 465 + Exec ~850 |
| v3 | Context Engine v2（同 v2）| Execution Engine v3 lean | 两层分离（精简面板 7 行）| Exec ~700 |

v1 是 v2 Context Engine 的**直接前身**——v1 内嵌的背景层代码（L115-278，164 行）被提取并扩展为独立的 `brooks_pa_context_engine_v1.txt`（465 行）。v1 的执行部分（H2/L2 + 楔形 + 评分 + 显示）则演化为 v2/v3 的独立执行引擎。
