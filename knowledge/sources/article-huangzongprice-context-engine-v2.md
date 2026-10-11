# Brooks PA Context Engine v2 Linkable — Pine Script 源码

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6 独立 overlay 指标）
- 原始位置：`raw/articles/huangzongprice/brooks_pa_context_engine_v2_linkable.txt`
- 脚本类型：独立 overlay 指标（自包含，不依赖 `input.source` API 绑定外部数据）
- 代码行数：489 行
- API 版本：2.0

## 一句话摘要
v2 Context Engine 将 Brooks「分析背景」四步法升级为四层显式加权评分流水线（位置40%+阶段35%+动能25%），5 过渡信号检测 + 双重路径 FSM 转移 + 四条件否决闸，输出 7 状态背景结论 + 30+ API 导出变量 + 8 条报警。

## 核心论点

### 与 v1 的差异

| 维度 | v1 Context Engine | v2 Context Engine |
|------|------------------|------------------|
| 代码行数 | 465 行 | 489 行 |
| 参数组织 | 散列 `G0/G1/G2/G3` | 六组 `G0-G5`（显示控制独立为 G5） |
| FSM 转移 | 简单 `rng2nbk` | **双路径**：`pathA`（大实体+过Donchian边界）+ `pathB`（≥3根连续同向突破）→合并为 `rng2nbk` |
| 突破计数 | 无 | `brkCnt`：FSM=2 时累计同向突破 Donchian 的次数，方向变更时重置 |
| 假突破检测 | 无 | `brkFail_EMG`：近 3 根突破 ph0 但收盘回落 |
| 信息面板 | 15 行 × 2 列 | **17 行** × 2 列（+API 版本 / API Ready 行） |
| API 导出 | 少（仅位置/阶段/动量分 + 背景结论二元标志） | **30+ 变量**（全子维度 L/S + 阶段状态码/方向/置信度/过渡/双向等） |
| 报警条件 | 7 条 | **8 条**（+背景支持做多/做空） |
| Donchian | 仅 donchH/donchL | + `donchMid`（中点） + `donchSpan`（宽度） |
| 楔形检测 | 无（或简化为 V1.5 方法） | `risingWedge`/`fallingWedge`：基于 ph/ph/b 的相对位置关系（8-200 bar 跨度） |
| R² 相关性 | 无 | `r2 = r²(close, bar_index, 50)`（50 周期趋势线性拟合度） |
| 衰竭棒检测 | 仅 `exhCdl` | `exhCdl` + `exhBars`（重叠度判定，但 `exhBars` 为死代码——定义后未使用） |
| API Ready | 无 | `apiReadyFlag`：所有评分变量非 na → 1.0 |
| 版本标识 | 无 | `apiVersion = 2.0` |

### 架构总览

```
OHLC → 基础数据层 (ATR14/20 + EMA20 + Donchian + Pivot + R²)
     → [Layer 1: 位置层 40%] → locScore L/S（ATR归一化距离 → 加分/扣分）
     → [Layer 2: 阶段层 35%] → phaseScore L/S（FSM + 5过渡信号 + 阶段健康分类）
     → [Layer 3: 动能层 25%] → momScore L/S（冲动/健康/成熟度/衰竭/弱化）
     → [Layer 4: 综合与否决]   → bgScore → conflict? → veto? → 7 状态码
     → [渲染层]               → 背景色 + EMA/Donchian/Fib50 + 标签 + 信息面板
     → [API 导出层]            → 30+ plot(data_window) 供下游执行层联动
```

### 第一步：位置层（权重 0.40）

参见 [[atr-position-scoring]]。关键逻辑：

- 距离归一化：`f_distAtr(level, atrBase) = |close - level| / max(atrBase, mintick)`
- 四类关键价位：分型极点 (ph0/pl0) + Donchian 20 (donchH/donchL) + EMA20 + Fib50
- 取最近距离：`bullSupportDist = min(pl0, donchL, ema20, fib50)` / `bearResistDist = min(ph0, donchH, ema20, fib50)`
- 加分项：强支撑 +0.30 / 弱支撑 +0.18 / 近 Fib50 +0.08 / EMA20 同侧 +0.05
- 扣分项：区间中部 −0.28 / 对方强阻力 −0.28 / 追价 −0.20 / 目标接近 −0.16
- 最终 `f_clamp01()` 钳位到 [0,1]

### 第二步：阶段层（权重 0.35）

**FSM 引擎**（与 v1 一致的四状态 + 三条转移路径）：

| 状态 | 编码 | 含义 | 转移触发 |
|------|------|------|---------|
| BREAKOUT | 0 | 突破 | `bo2ch`：振幅≥1×ATR20 + 逆势回调 |
| CHANNEL | 1 | 通道 | `ch2rng`：大实体+极强收盘+突破分型 |
| TRADING_RANGE | 2 | 震荡 | `rng2nbk`（见下方） |
| NEW_BREAKOUT | 3 | 新突破 | 等效 BREAKOUT 行为 |

**rng2nbk 双路径设计**（v2 核心改进）：

1. **路径A (`pathA`)**：实体 > 1.5×ATR20 + 收盘过旧 Donchian + 高/低突破 Donchian 边界 → 瞬间转移，`fsmConf=0.90`
2. **路径B (`pathB`)**：FSM=2 期间连续 ≥3 根收盘同向突破旧 Donchian → 累计确认后转移

- `brkCnt`：在 FSM=2 时累计同向突破次数，方向变更时清零

**5 信号过渡检测**（与 v1 相同）：
1. `transitionByOverlap`：avgOlp > 0.32
2. `transitionBySlopeLoss`：EMA 不陡或平坦
3. `transitionByBroadChannel`：通道 + 重叠 > 0.24 + 置信 < 0.72
4. `transitionByWedge`：上升楔形或下降楔形
5. `transitionByFailedBreakout`：`brkFail_EMG`

≥2 信号 = 过渡状态。

**阶段健康分类**：
- `phaseTrendHealthy`：趋势 + 置信≥0.70 + EMA陡峭 + 低重叠 + 非过渡
- `phaseTrendWeakening`：趋势 + ≥1 过渡信号 + (高重叠 或 非EMA陡峭)
- `phaseTwoSided`：震荡 或 过渡 或 重叠度 > 0.35

**阶段评分**（基础 0.08）：
- 多头方向：趋势健康 +0.52 / 趋势弱化 +0.30 / 仅趋势 +0.20
- 震荡 + 近支撑：+0.12
- 对方趋势健康：−0.26
- 双向环境 + 不近关键位：−0.14

### 第三步：动能层（权重 0.25）

参见 [[momentum-health]]。四维综合公式：

```
momScore = 0.10 + impulseScore×0.30 + trendHealth×0.28 
           − trendMaturity×0.20 − exhaustRisk×0.18 − legWeakening×0.12
```

**冲动评分 (impulseScore)**：`bodyRatio×0.55 + breakMag×0.45`，其中 `bodyRatio = barBody/barRng`，`breakMag = (close−low)/barRng`(多) 或 `(high−close)/barRng`(空)

**趋势健康 (trendHealth)**：冲动×0.35 + EMA斜率×0.25 + 低重叠×0.20 + 无衰竭棒×0.20

**成熟度 (trendMaturity)**：楔形×0.35 + 追价×0.25 + 衰竭棒×0.20 + 目标近×0.20

**衰竭风险 (exhaustRisk)**：假突破×0.40 + 楔形×0.25 + 高重叠×0.15 + 目标近×0.20

**腿弱化 (legWeakening)**：冲动衰减×0.30 + 高重叠×0.25 + EMA走平×0.20 + 楔形×0.25

### 第四步：综合与否决

**综合背景分**：
```
bgScoreL = locScoreL×0.40 + phaseScoreL×0.35 + momScoreL×0.25
bgScoreS = locScoreS×0.40 + phaseScoreS×0.35 + momScoreS×0.25
```

**冲突检测**（任一触发 → 背景不支持）：
1. bgScore < 0.58 且 > 0.42（灰色地带）
2. 多空差距 > 0.18（方向不明确）
3. 双向环境 + 不近目标方向关键位

**四类否决条件**（任一触发 → bgStateCode=9）：
1. 区间中部 + 震荡阶段
2. 对方趋势健康 + 对方衰竭风险 < 0.55
3. 追价突破 + 在对方阻力/支撑
4. 成熟度≥0.65 或衰竭风险≥0.60 + 目标接近

**7 状态输出**：
| 状态码 | 状态名 | 条件 |
|--------|--------|------|
| 2 | 多强 | bgSupportLong + bgScoreL≥0.72 |
| 1 | 多可 | bgSupportLong + bgScoreL<0.72 |
| 0 | 中性 | 无明确方向 |
| −1 | 空可 | bgSupportShort + bgScoreS<0.72 |
| −2 | 空强 | bgSupportShort + bgScoreS≥0.72 |
| 9 | 否决 | 任一否决条件触发 |

### API 导出层（30+ data_window 变量）

v2 将所有评分子系统和状态标志通过 `display=display.data_window` 导出为不可见图层，供下游执行层通过 `input.source` 绑定：

| 类别 | 变量 | 数量 |
|------|------|------|
| 位置分 | locScoreL/S | 2 |
| 阶段分 | phaseScoreL/S | 2 |
| 动量分 | momScoreL/S | 2 |
| 背景分 | bgScoreL/S | 2 |
| 阶段状态 | phaseState, phaseDir, phaseConfidence | 3 |
| 背景逻辑 | bgSupportL/S, bgConflictL/S, bgVetoL/S | 6 |
| 阶段分类 | phaseIsRange, phaseIsTransition, phaseTrendHealthy, phaseTrendWeakening, phaseTwoSided | 5 |
| 健康/成熟/风险 | trendHealthL/S, trendMaturityL/S, exhaustRiskL/S | 6 |
| 元信息 | bgStateCode, apiVersion, apiReadyFlag | 3 |

### 报警系统（8 条）

1. 背景转多（`bgBullNew`）→ 含 ticker+周期
2. 背景转空（`bgBearNew`）→ 含 ticker+周期
3. 背景否决（`bgVetoNew`）→ 含 ticker+周期
4. 背景支持做多（持续信号）
5. 背景支持做空（持续信号）
6. 位于区间中部
7. 衰竭风险高（exhaustRiskL > 0.6 或 exhaustRiskS > 0.6）

### 楔形检测算法

v2 新增的独立楔形检测：

```
risingWedge:  ph2b < pl1b < ph1b < ph0b  (高点逐步右移)
              AND ph1 > ph2               (HH — higher high)
              AND pl0 > pl1               (HL — higher low)
              AND 8 ≤ (ph0b−ph2b) ≤ 200

fallingWedge: pl2b < ph1b < pl1b < pl0b  (低点逐步右移)
              AND pl1 < pl2               (LL — lower low)
              AND ph0 < ph1               (LH — lower high)
              AND 8 ≤ (pl0b−pl2b) ≤ 200
```

楔形信号**同时影响**成熟度(+0.35)、衰竭风险(+0.25)、腿弱化(+0.25)三个子维度——累计可压低 momScore 约 0.145，是动能层最强的空头信号源。

## 提取出的新概念

**无全新概念**。v2 的所有核心架构（位置层/阶段层/动能层/否决闸/FSM/成熟度/衰竭风险/追价）均已在之前的 ingest 中作为独立概念页创建。本次 ingest 的核心价值是：

1. **落地来源页**：填补了 3 个已有概念页（[[context-engine-v2]]、[[atr-position-scoring]]、[[momentum-health]]）一直引用的不存在的来源页
2. **记录 v1→v2 差异**：双路径 FSM 转移、楔形检测、R² 相关性、API Ready 等 v2 增量
3. **提供参数全集**：6 组可配置参数（G0-G5）的默认值与含义

## 与现有知识的衔接

- [[context-engine-v2]]：本文是概念页对应的完整源码来源
- [[atr-position-scoring]]：Layer 1 位置评分的完整实现
- [[momentum-health]]：Layer 3 动能四维的完整实现
- [[fsm-market-cycle]]：Layer 2 FSM 引擎的 v2 版本（双路径转移）
- [[exhaustion-risk]]：衰竭风险四因子评分的源码
- [[trend-maturity]]：趋势成熟度四因子评分的源码
- [[late-breakout]]：追价判定逻辑的完整条件
- [[three-push-wedge|Three Push Wedge]]：v2 独立楔形检测算法
- [[article-huangzongprice-context-engine-v1]]：v1 来源页——姐妹篇，记录了 v2 的 12 项增量改进

## 与现有知识的冲突

- **无直接冲突**。v2 是 v1 的渐进升级版——保留了全部核心架构（四层加权+FSM+否决），新增了双路径转移、独立楔形检测、更丰富的 API 导出。唯一的退化是 v2 中 `exhBars`（重叠式衰竭棒检测）定义后从未使用，属于死代码。
- v2 砍掉了 V1.5 中的引力场和 H2/L2 状态机——这是 v2 精简路线的体现，已在 [[context-engine-v2]] 的矛盾与待验证中标注。
- 默认权重 40/35/25 与 v1 完全相同——说明作者对此权重配比有较高信心，但同样未经回测交叉验证。

## 完整参数表

### G0：基础参数
| 参数 | 默认 | 含义 |
|------|------|------|
| `i_atr14` | 14 | ATR 短周期 |
| `i_atr20` | 20 | ATR 长周期 |
| `i_swN` | 5 | N-Bar 分型左右距 |
| `i_emaLen` | 20 | EMA 周期 |
| `i_donchN` | 20 | Donchian 周期 |
| `i_visBars` | 300 | 显示回看K线数 |

### G1：位置层
| 参数 | 默认 | 含义 |
|------|------|------|
| `i_srNearAtr` | 0.60 | 强支撑阻力距离(ATR) |
| `i_srSoftAtr` | 1.20 | 弱支撑阻力距离(ATR) |
| `i_midRangePct` | 0.20 | 区间中部阈值 |
| `i_fibNearAtr` | 0.80 | Fib50 接近阈值 |
| `i_targetNearAtr` | 0.80 | 目标位接近阈值 |
| `i_lateBreakAtr` | 0.60 | 追价判定 ATR |

### G2：阶段层
| 参数 | 默认 | 含义 |
|------|------|------|
| `i_olpLen` | 5 | 重叠度均值窗口 |
| `i_trendOlpMax` | 0.24 | 趋势重叠上限 |
| `i_rangeOlpMin` | 0.35 | 震荡重叠下限 |
| `i_emaSteepMul` | 0.50 | EMA斜率阈值ATR倍数 |
| `i_phaseConfTrend` | 0.70 | 趋势健康置信度阈值 |

### G3：动能层
| 参数 | 默认 | 含义 |
|------|------|------|
| `i_impulseBodyMul` | 1.20 | 强信号棒实体倍数 |
| `i_exhaustBodyMul` | 1.50 | 衰竭棒实体倍数 |
| `i_exhaustRangeMul` | 1.20 | 衰竭棒波幅倍数 |
| `i_maturityThr` | 0.65 | 成熟度高阈值 |
| `i_exhaustRiskThr` | 0.60 | 衰竭风险高阈值 |

### G4：综合与否决
| 参数 | 默认 | 含义 |
|------|------|------|
| `i_bgThr` | 0.58 | 背景支持阈值 |
| `i_confThr` | 0.18 | 多空冲突差阈值 |
| `i_locWeight` | 0.40 | 位置层权重 |
| `i_phaseWeight` | 0.35 | 阶段层权重 |
| `i_momWeight` | 0.25 | 动能层权重 |

### G5：显示控制
8 个布尔开关：背景色/EMA20/Donchian/Fib50/波段极点/背景标签/信息面板
