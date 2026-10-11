# Wedge-Gravity V2 Master — Pine Script v6 全量源码

## 元信息
- 作者：huangzongprice
- 日期：未标注（版本号 V2 Master）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_master_v2.txt`（1093行 Pine Script v6 源码）
- 配套文件：`wedge_gravity_tradingview_master_v2.pine`

## 一句话摘要
WG V2 Master 是 V1.5 的重大升级——新增 Brooks 四步背景层、Path-A/Path-B 双路突破检测、趋势/反转信号分离评分、ABC 三级信号分级和 26 行信息面板，从「信号识别」升级为「背景→信号→否决」完整决策流水线。

## 核心论点

### 架构升级（V1.5 → V2）

| 维度 | V1.5 | V2 Master |
|------|------|-----------|
| 计算模式 | 每 tick 计算 | `calc_on_every_tick=false`（性能） |
| 风险线 | 散落各处 | `f_riskHz()` / `f_riskLb()` 函数化复用 |
| 背景层 | 无 | Brooks 四步法（Step1-4）可选启用 |
| 突破检测 | 唐奇安穿破 | Path-A（激进即时）+ Path-B（保守延迟3根） |
| 楔形评分 | 简单对称比 | 三个子评分：对称40% + 收口35% + 跨度25% |
| 信号评分 | 单一 lFin/sFin | 趋势/反转分离 + 信号分级 A/B/C |
| 可靠性 | 基础 | 7 种可选过滤器（确认K线/失败/重叠/关键位/分级/反转高阈/警报仅收盘） |
| 面板 | 10+行 | 26行信息面板 |
| 警报 | 4条 | 9条（含 Brooks 否决边沿警报） |

### 模块架构

```
OHLC
 ├─ 模块一A：FSM 传感器（EMA斜率 + K线重叠度 + 唐奇安通道 + R²）
 │    └─ 模块一B：关键位置引力场（高斯衰减：EMA/极值/50%位/缺口中枢）
 ├─ 模块二A：N-Bar 分型极点
 │    └─ 模块二B：三推楔形识别（对称×收口×跨度三子评分）
 ├─ Brooks Step1：支撑阻力评分（7种S/R + MM目标 + 整数关口→ ctx1_score）
 ├─ Brooks Step2：市场阶段（FSM + 过渡检测 → ctx2_score + phaseStr）
 ├─ Brooks Step3：动能健康度（重叠/斜率/衰竭/楔形 → ctx3_score）
 ├─ Brooks Step4：一票否决（TR区位 + 紧急逃生 → 二元否决）
 ├─ 模块三：H1/H2/L1/L2 状态机（孕线免疫 + 超时重置）
 ├─ 模块四：信号K线评分（趋势/反转分离 + 7种可选过滤）
 │    ├─ 结构优先级（楔形 > H2/L2）
 │    ├─ 关键位分层（Tier-1/Tier-2）
 │    ├─ 确认K线（延迟一根 + ATR阈值）
 │    ├─ 失败过滤（紧急逃生硬否决）
 │    ├─ 高重叠/低置信过滤
 │    ├─ 信号分级过滤（A/B/C）
 │    └─ Brooks 否决闸
 └─ 风控（动态止损/止盈/入场参考线 + 9条警报条件）
```

### FSM 四状态 + 双路突破

状态：`BREAKOUT(0) → CHANNEL(1) → TRADING_RANGE(2) → NEW_BREAKOUT(3) → CHANNEL(1) → ...`

- **Path-A（激进即时）**：实体 > 1.5×ATR20 + 收盘超出唐奇安边界 > 0.5×ATR20 + 创周期新高/低 → 立即切换 NEW_BREAKOUT
- **Path-B（保守延迟）**：连续 3 根 K 线收盘维持在唐奇安边界外侧 → 切换 NEW_BREAKOUT

### 信号评分公式（V2 新增趋势/反转分离）

多头：`lFin = min(ctxScore × 0.70 + lScore × 0.30 + gravBonus + structScoreL + extraBonusL, 1.0)`

- `structScoreL` = 对称40% + 收口35% + 跨度25%（楔形时）或 0.55（H2时）
- `extraBonusL` = 反转时 `(pos×0.60+mom×0.40) × 0.10`；趋势时 `(mom×0.70+pos×0.30) × 0.10`
- 反转信号可选更高阈值（+0.10）

### 信号分级（A/B/C）

- A级：≥ 0.80
- B级：≥ 0.60
- C级：< 0.60
- 可配置最低等级过滤（选 A 则仅 A 级出信号）

## 提取出的新概念

| 概念 | 说明 |
|------|------|
| [[path-ab-breakout]] | Path-A 激进即时 vs Path-B 保守延迟双路突破检测 |
| [[signal-grading-system]] | ABC 三级信号分级系统（≥0.80=A / ≥0.60=B / <0.60=C）+ 等级过滤 |
| [[trend-reversal-separation]] | 趋势/反转信号分离评分：趋势重动量、反转重位置，不同权重分配 |
| [[confirm-bar-delay]] | 可选确认K线机制：信号延迟一根 + 突破 ATR×0.60 阈值确认 |
| [[key-level-tier]] | 关键位分层过滤：Tier-1（ph0/pl0/donch边界）×ATR vs Tier-2（ph1/pl1/EMA/50%）×ATR |
| [[wedge-quality-scoring]] | 楔形质量三子评分：空间对称40% + 收口收敛35% + 跨度25% |

## 与现有知识的冲突

- **[[wedge-gravity-dual-core]]**：V2 在 V1.5 双核架构上新增 Brooks 四步背景层，形成「FSM + 评分」→「四步背景 + 双核信号」三层架构
- **[[signal-scoring-synthesis]]**：V2 将单一 lFin/sFin 公式升级为趋势/反转分离评分 + 信号分级，权重分配逻辑根本不同
- **[[fsm-market-cycle]]**：V2 新增 Path-A/Path-B 双路突破 + 过渡检测系统（5种过渡信号），比 V1.5 的单路唐奇安突破更精细
- **[[brooks-four-step-context]]**：V2 的 Brooks 四步实现提供了 ctx1/ctx2/ctx3 的具体评分公式和权重（此前该概念仅描述框架未给出精确公式）

## 待办

- 与 V3 Context Engine 的 ctx 评分做交叉对比（V2 Brooks 四步 vs V3 三层加权）
- V2 的 9 条警报条件是否需要在 A 股分析系统中复用
