# Wedge-Gravity 楔形引力策略 V1.4 — Pine Script v6 源码

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6，V1.4 版本）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_fixed_v2.txt`
- 代码行数：950 行（含注释）
- 脚本类型：独立 overlay 指标（单文件自包含）
- 上一版本：V1.3（三推楔形校验逻辑保留）
- 新版功能标识：市场周期引擎 (Market Cycle FSM) 首次整合

## 一句话摘要
V1.4 是 WG 系列首个将「市场周期 FSM」作为独立引擎嵌入的版本——双核驱动（硬规则事件 + 特征评分），整合楔形识别、引力场、H2/L2 状态机、紧急逃生、G7 信号可靠性优化管道、动态风控和信息面板 16 行仪表盘。

## 核心论点

### 架构总览：七模块流水线

```
参数输入 → [基础指标: ATR14/20, EMA20, BarRange, MidPt]
         → [模块一A: FSM 传感器 — EMA斜率 / K线重叠度 / 唐奇安通道 / R²]
         → [模块二A: N-Bar 分型极点 — 精准定位，无 offset 偏移]
         → [模块二B: 三推楔形识别 — V1.3 校验逻辑+收口斜率评分]
         → [模块一B: 关键位置引力场 — 高斯衰减（6个引力源）]
         → [模块三: H1/H2/L1/L2 状态机 — 孕线免疫+超时重置]
         → [模块四: 信号K线评分 → lFin/sFin 合成]
         → [模块五: G7 信号可靠性管道 → 综合入场信号]
         → [模块六: 动态风控 → ENT/SL/TP]
         → [模块七: 可视化 + 信息面板 + 7种警报]
```

### 模块一A：FSM 传感器（3 个传感器 + 1 个辅助指标）

| 传感器 | 输入 | 输出 | 阈值 |
|--------|------|------|------|
| EMA 斜率 | `ema20v - ema20v[3]` vs `[10]` | `emaSteep` / `emaFlat` | `> 0.5×ATR20` 陡峭 / `< 0.5×ATR20` 走平 |
| K线重叠度 | `max(0, min(Cₚ,C) − max(Oₚ,O)) / |C−O|` | `avgOlp` (SMA窗口均值) | `i_olpLen=5` |
| 唐奇安通道 | `highest(high,20)` / `lowest(low,20)` | `donchH/donchL` + 前一周期不含当前Bar | `i_donchN=20` |
| R² | `correlation(close, bar_index, 50)²` | `r2` (0~1) | 仅展示，不参与信号过滤 |

### 市场周期 FSM（模块核心）

**四状态编码**：`0=BREAKOUT` / `1=CHANNEL` / `2=TRADING_RANGE` / `3=NEW_BREAKOUT`

**三条硬规则转换（优先级从高到低，if-else 互斥）**：

| # | 转换 | 条件 | 优先级 |
|---|------|------|--------|
| 1 | RANGE→NEW_BREAKOUT (`rng2nbk`) | Path-A（激进）：大实体 > 1.5×ATR20 + 收盘超边界 > 0.5×ATR20 + 创新高/低；Path-B（保守）：连续 3 根收盘在唐奇安边界外 | 最高 |
| 2 | BO/NEW_BK→CHANNEL (`bo2ch`) | 首根逆势回调 K 线幅度 ≥ 1×ATR20 | 中 |
| 3 | CHANNEL→RANGE (`ch2rng`) | 三条件同时满足：① 实体 > 1×ATR20 ② 收盘在 K 线极值 25% 以内（极强收盘）③ 突破最近重要分型极点（ph0/pl0） | 低 |

**置信度评分**（无状态转换时动态更新）：
- 突破/新突破：`avgOlp < 0.20 ∧ emaSteep → 0.90`，否则 `0.65`
- 通道：`emaSteep ∧ ¬emaFlat → 0.75`，否则 `0.50`
- 震荡：`emaFlat → 0.80`，否则 `0.50`

**初始化**：`fsm=2(TR)`，方向由 EMA 斜率自动补全。

### 模块二B：三推楔形识别（V1.3 校验逻辑保留）

**识别条件**：
- **上升楔形**（偏空）：`ph2b < pl1b < ph1b < pl0b < ph0b`（H-L-H-L-H 交替），价格逐步抬高，上下界斜率收口
- **下降楔形**（偏多）：`pl2b < ph1b < pl1b < ph0b < pl0b`（L-H-L-H-L 交替），价格逐步走低，上下界斜率收口

**校验函数** `f_wedgeOK`：空间对称比 `s2/s1 ∈ [0.25, 2.50]`，时间对称比 `t2/t1 ∈ [0.25, 3.00]`，总跨度 `∈ [10, 200]` bar。

**三维修正评分**：对称分（空间比+时间比）×0.5 + 收敛分（上下界斜率差异）+ 跨度分（10~i_wMax 归一化）。

### 模块一B：引力场（高斯衰减）

6 个引力源权重：EMA20(×3.0) / ph0(×5.0) / pl0(×5.0) / ph1(×3.0) / pl1(×3.0) / fib50(×4.0) / 缺口区(×4.0)。

公式：`gScore = Σ w × exp(−0.5 × (dist/ATR14)²)`，阈值 `i_gThr = 5.0`。`ctxScore = min(gScore/10, 1.0)`。

### 模块三：H1/H2/L1/L2 状态机

**孕线免疫**：`insideBar = high < high[1] ∧ low > low[1]` 时状态机暂停推进。

**超时重置**：25 bar 内未完成从 Phase 0 到信号的完整路径即重置（`i_timeout=25`）。

**做多路径**：分型低点 → H1（过前高）→ 回撤（破H1低）→ H2（再过H1高）→ H2 信号
**做空路径**：分型高点 → L1（破前低）→ 反弹（破L1高）→ L2（再破L1低）→ L2 信号

### 模块四：信号 K 线评分与合成

**K 线分**（0-1，三项累加）：
- 做多：收盘近高 ≥ 75% → +0.4；实体 ≥ avgBody5×1.2 → +0.3；下影占比 ≤ 40% → +0.3
- 做空：收盘近低 ≥ 75% → +0.4；实体 ≥ avgBody5×1.2 → +0.3；上影占比 ≤ 40% → +0.3

**合成公式**：
```
lFin = min(ctxScore × i_ctxW + lScore × (1−i_ctxW) + gravBonus + structScoreL + extraBonusL, 1.0)
```
其中 `gravBonus = gravOK ? 0.08 : 0.0`，`extraBonus = 最多 ~0.10`（趋势/反转分离加成）。

### 模块五：G7 信号可靠性管道

7 层可配置过滤，逐层把关：

| 层 | 参数 | 逻辑 | 默认 |
|----|------|------|------|
| 1. 结构优先级 | — | 楔形 > H2/L2（同时触发时优先楔形，不扩大触发范围） | 始终开启 |
| 2. 趋势/反转分离 | `i_useRevFilter` | 反转信号阈值 +0.10；趋势侧重动量，反转侧重位置 | 关闭 |
| 3. 确认 K 线 | `i_useConfirm` | 信号延后一根，需下一根突破信号高/低 ≥ 0.6×ATR | 关闭 |
| 4. 失败过滤 | `i_useFailFilter` | 紧急逃生触发 → 硬否决 | 关闭 |
| 5. 重叠/置信过滤 | `i_useOlpFilter` | `avgOlp ≤ 0.35 ∧ fsmConf ≥ 0.55` | 关闭 |
| 6. 关键位分层 | `i_useKeyFilter` | Tier-1（ph0/pl0/唐奇安 ≤ 1.0×ATR）或 Tier-2（ph1/pl1/EMA20/fib50 ≤ 0.8×ATR）或引力场触发 → 放行 | 关闭 |
| 7. 信号分级 | `i_useGradeFilter` | A(lFin≥0.80) / B(≥0.60) / C(<0.60)，最低等级可配置 | 关闭 |

**中点条件**：做多需 `close > midPt`，做空需 `close < midPt`——收盘位置不对即使分数达标也不入。

### FSM 策略约束（allowLong / allowShort）

| 周期状态 | 多头许可 | 空头许可 | 说明 |
|---------|---------|---------|------|
| BREAKOUT(0) / NEW_BREAKOUT(3) | `fsmDir==1` | `fsmDir==-1` | 仅顺势，绝对禁止逆势 |
| CHANNEL(1) 多头趋势 | `true` | `nearChanT ∧ sFin ≥ sigThr+0.15` | 顺势为主；通道顶边界允许高分逆势剥头皮 |
| CHANNEL(1) 空头趋势 | `nearChanB ∧ lFin ≥ sigThr+0.15` | `true` | 顺势为主；通道底边界允许高分做多 |
| TRADING_RANGE(2) | `nearDonchL` | `nearDonchH` | 仅唐奇安边界反向入场（假突破防御激活） |

其中 `nearDonchH/L` = 距上下轨 ≤ 0.5×ATR14，`nearChanT/B` = 距最近 ph0/pl0 ≤ 1.5×ATR14。

### 模块六：动态风控（ENT / SL / TP）

```
stopBuf = max(mintick, 0.5×ATR20)
entBuf  = max(mintick, 0.1×ATR14)
lSL = majorSL − stopBuf           // 多头止损：最近主要低点−ATR缓冲
lEnt = high + entBuf              // 多头入场：突破信号K高点+微缓冲
lTP = lEnt + 2.0 × (lEnt − lSL)   // 多头止盈：1:2 盈亏比
```

空头对称。入场前由风控给出 ENT/SL/TP 参考线，入场后交 [[trade-management-system]] 接管。

### 信息面板（16 行 × 2 列）

市场周期 / 趋势方向 / 置信度/R² / EMA 斜率 / 平均重叠度 / 唐奇安上下轨 / Path-B 计数 / 引力场得分 / 楔形形态 / 多空计数状态 / 结构优先级 / 信号类型 / 信号等级 / 多头策略许可 / 空头策略许可 / 紧急逃生 / 多头触发分 / 空头触发分 / 综合信号

### 警报条件（7 种）
做多入场 / 做空入场 / 新突破确认 / 突破转通道 / 进入震荡区间 / H2 多头计数 / 紧急逃生预警

## 提取出的新概念

### 本次 Ingest 新建
- [[fsm-strategy-constraints]] — FSM 策略约束：四周期状态→allowLong/allowShort 的精确映射规则（通道边界逆势附加阈值等）
- [[signal-reliability-pipeline]] — G7 信号可靠性管道：7层可配置过滤（结构优先级→趋势/反转分离→确认K线→失败过滤→重叠过滤→关键位分层→信号分级）

### 对已有概念的源码补充
- [[fsm-market-cycle]]：V1.4 是 FSM 作为独立引擎首次整合到 WG 指标的版本——精确量化了三转换条件（含 Path-A/Path-B 双路径突破）、置信度动态更新公式、5 个持久化变量的跨 Bar 维护
- [[wedge-gravity-dual-core]]：V1.4 的双核架构（硬规则 FSM + 软评分五因子）是本概念的基础实现——之前所有文档分析均基于此文源码
- [[signal-scoring-synthesis]]：V1.4 源码第 485-610 行——完整的 lScore/sScore 三项评分细则 + lFin/sFin 五因子合成公式 + 趋势/反转分离 + extraBonus 注入
- [[gravity-field]]：6 引力源 × 高斯衰减的完整实现（第 403-428 行）
- [[h2-l2-state-machine|H2/L2 State Machine]]：孕线免疫（insideBar 跳过）+ 25 bar 超时重置的完整状态机（第 433-523 行）
- [[three-push-wedge|Three Push Wedge]]：V1.3 校验逻辑（`f_wedgeOK`）+ 三维修正评分 + 5 极点精确排序条件（第 287-401 行）
- [[emergency-exit]]：三种触发条件（假突破/实体衰竭/竭尽K线）的精确判定（第 617-636 行）
- [[dynamic-risk-control]]：stopBuf/entBuf + 结构极值 + 1:2 盈亏比的 ENT/SL/TP 计算（第 706-715 行）

## 与现有知识的冲突

- **FSM `fsm=0` 可达性**：V1.4 中 `bo2ch` 检查 `fsm == 0 or fsm == 3`，但无代码显式设置 `fsm = 0`。`fsm=0` 仅作为初始化值（与 `fsm=3` 共用 `bo2ch` 转换），在运行中不会从其他状态转入，属于预留死分支。这与 [[fsm-market-cycle]] 的标注一致。
- **V1.4 vs V1.5/V5.0 的架构定位**：V1.4 是双核架构的首次 FSM 集成版本；V1.5/V4.1 在此基础上扩展了三层背景评分；V5.0 新增供需区/订单块模块。V1.4 的 G7 管道设计（7 层全可选、默认全关闭）体现了「给用户最大控制权」的设计哲学，后续版本逐步将某些层设为默认开启或内嵌。
