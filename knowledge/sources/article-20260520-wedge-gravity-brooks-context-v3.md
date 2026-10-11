# Wedge-Gravity Brooks Context Engine V3.0（完整 Pine Script 源码）

## 元信息
- 作者：huangzongprice
- 日期：未标注（推测 2025 年中，为 V3 背景引擎的完整 Pine Script v6 实现）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_brooks_context_v3.txt`
- 代码量：1,139 行 Pine Script v6
- 性质：可运行的生产级代码（非设计文档），包含所有精确公式、参数默认值和阈值

## 一句话摘要
WG Brooks 系统的 V3 完整 Pine Script 源码——实现了从 OHLC 输入到入场信号的完整流水线：FSM 周期引擎→三推楔形检测→引力场→H1/H2/L1/L2 状态机→紧急逃生→三层背景评分（Location/Phase/Momentum）→背景裁决→结构评分→执行评分→动态风控→信号输出。

## 核心论点

### 架构层级（从输入到输出的 12 层流水线）

```
OHLC 数据
  → 基础指标（ATR14/20, EMA20, Donchian20, 重叠度）
  → 模块一A：FSM 市场周期引擎（4 状态机 + 置信度）
  → 模块二A：N-Bar 分型极点（波段高/低点检测）
  → 模块二B：三推楔形识别（上升/下降楔形 + 3 维质量评分）
  → 模块一B：关键位置引力场（高斯衰减 + 6 个关键价位）
  → 模块三：H1/H2/L1/L2 状态机（25 根超时保护）
  → 模块四：紧急逃生预警（假突破/实体衰竭/竭尽K线）
  → 背景层一：Location Context（6 种位置判定 + 加减分 → locScore 0-1）
  → 背景层二：Phase Context（5 项过渡证据 + 趋势/区间/过渡判定 → phaseScore 0-1）
  → 背景层三：Momentum Health（5 因子：impulse/trendHealth/maturity/exhaust/legWeakening → momScore 0-1）
  → 背景裁决层：bgScore = loc×0.40 + phase×0.35 + mom×0.25 → bgSupport/bgConflict/bgVeto
  → 结构层：楔形/H2 结构评分 + 信号棒评分 → 执行分 = bg×0.55 + struct×0.25 + signal×0.20
  → 动态风控：ATR 缓冲 ENT/SL/TP + 确认K线可选 + ABC 等级过滤
  → 可视化 + 11 种警报条件
```

### 关键参数默认值

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `i_donchN` | 20 | Donchian 通道周期 |
| `i_olpLen` | 5 | 重叠度均值窗口 |
| `i_brkMul` | 1.5 | 新突破 Path-A 实体倍数 |
| `i_brkOff` | 0.5 | 新突破 Path-A 偏离 ATR |
| `i_atr14` / `i_atr20` | 14 / 20 | ATR 双周期 |
| `i_swN` | 5 | N-Bar 分型左右距 |
| `i_gThr` | 5.0 | 引力场触发阈值 |
| `i_sigThr` | 0.40 | 信号棒最低分 |
| `i_bgThr` | 0.58 | 背景支持阈值 |
| `i_confThr` | 0.18 | 背景冲突差阈值 |
| `i_execBgW` / `i_execStW` / `i_execSbW` | 0.55 / 0.25 / 0.20 | 执行分三因子权重 |
| `i_symLo` / `i_symHi` | 0.25 / 2.50 | 楔形空间对称比范围 |
| `i_tRatio` | 3.00 | 楔形时间对称比上限 |
| `i_timeout` | 25 | H/L 计数等待超时 |

### 背景裁决层核心逻辑

**bgScore 公式**：
```
bgScoreL = clamp(locScoreL × 0.40 + phaseScoreL × 0.35 + momScoreL × 0.25, 0, 1)
bgScoreS = clamp(locScoreS × 0.40 + phaseScoreS × 0.35 + momScoreS × 0.25, 0, 1)
```

**背景支持条件**（bgSupport）：
1. bgScore ≥ i_bgThr（0.58）
2. bgScore ≥ 对立方向分数 - 0.02
3. NOT bgConflict
4. NOT bgVeto

**背景冲突条件**（bgConflict）：
- bgScore < 阈值 且 > 0.42
- 或 对立方向分数 - 本方分数 > 0.18
- 或 双边势且不近本方 S/R
- 或 近对向阻力且无楔形/H2 支撑

**背景否决条件**（bgVeto）——4 项：
1. 区间中部 + 震荡区间
2. 健康趋势方向与策略相反（且无楔形/H2/L2 支撑）
3. 贴近对向 S/R + 追价突破
4. 高成熟度/衰竭 + 当前腿转弱 + 追价突破

**背景状态输出**：
- `VETO`：任一方否决
- `BULL_STRONG`：bgSupportLong 且 bgScoreL ≥ 0.72
- `BULL_OK`：bgSupportLong 但 bgScoreL < 0.72
- `BEAR_STRONG`：bgSupportShort 且 bgScoreS ≥ 0.72
- `BEAR_OK`：bgSupportShort 但 bgScoreS < 0.72
- `NEUTRAL`：无明确支持

### 与设计文档的关键差异

本文是**可运行源码**，与之前的设计文档（V4.1 流程图、v3 升级设计稿等）的差异：
- 设计文档描述"应该有什么"，源码定义"实际怎么算"
- 源码中的 FSM 状态机（Breakout=0/Channel=1/Range=2/NewBreakout=3）是运行的实现，与设计文档的状态编号可能不同
- 引力场阈值 i_gThr=5.0 和三层权重 40/35/25 在代码中硬编码为可调参数
- 执行分权重 0.55/0.25/0.20 在代码中是用户可调参数（`i_execBgW`/`i_execStW`/`i_execSbW`）

## 提取出的新概念

本源码首次以可运行代码形式呈现以下子系统的完整实现细节（之前仅有设计文档描述）：

1. **动量健康度五因子系统**（impulseScore + trendHealth + trendMaturity + exhaustRisk + currentLegWeakening）→ [[momentum-health]]
2. **阶段过渡五证据检测**（overlap/slope/broadChannel/wedge/failedBreakout ≥ 2 → transition）→ [[phase-transition-detection]]
3. **背景否决四条件**（midRange+range / healthy-opposite-trend / S/R+lateBreakout / maturity+exhaust+lateBreakout）→ [[background-veto]]

## 与现有知识的冲突

- 本源码中 FSM 状态编号（0=Breakout, 1=Channel, 2=Range, 3=NewBreakout）与 [[fsm-market-cycle]] 中记录的编号（可能不同——FSM 页标注"0=突破, 1=通道, 2=震荡, 3=新突破"）完全一致，**无冲突**
- 三层权重 40/35/25 与 [[background-scoring-engine]] 记录一致，**精确吻合**
- 执行分权重默认值 0.55/0.25/0.20 与 [[signal-scoring-synthesis]] 记录的"三因子公式"一致，且源码中声明为可调参数——确认这些权重是经验值而非数学最优解
