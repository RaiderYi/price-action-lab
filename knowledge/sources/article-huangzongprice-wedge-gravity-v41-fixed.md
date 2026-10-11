# 楔形引力 Brooks 引擎 V4.1 — Pine Script 源码

## 元信息
- 作者：huangzongprice
- 日期：未标注（V4.1 修复版，基于 V3 编译错误修复）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_brooks_context_v4_fixed.txt`
- 语言：Pine Script v6
- 代码规模：1303 行 / 约 72 KB

## 一句话摘要
WG Brooks Context Engine 的 V4.1 完整 Pine Script 源码——包含 FSM 市场周期、三推楔形、引力场、H2/L2 状态机、紧急逃生、三层背景评分引擎（Location/Phase/Momentum）、执行评分合成、以及完整的可视化渲染层和 12 个警报条件。

## 核心架构

```
OHLC 输入
  ├── 基础传感器层：ATR(14/20)、EMA20、棒体/范围/中点、5/20 周期均实体
  ├── FSM 传感器层：唐奇安(N=20)、重叠度(5 周期均值)、R²(50 周期)、EMA 斜率
  ├── N-Bar 分型极点：ph0/ph1/ph2、pl0/pl1/pl2（5 棒分型）
  ├── [分析层] 市场周期 FSM（4 状态 → Path-A/B 双路径突破）
  ├── [分析层] 三推楔形识别（上升楔形/下降楔形 + 3 维质量评分）
  ├── [分析层] 引力场（6 个引力源高斯累加）
  ├── [分析层] H1/H2 / L1/L2 状态机（含超时保护）
  ├── [分析层] 紧急逃生预警（假突破 + 衰竭棒 + 竭尽 K 线）
  ├── [决策层] Location Context（8 个位置布尔 + +/- 分制）
  ├── [决策层] Phase Context（趋势/区间/过渡分类 + 趋势健康三档）
  ├── [决策层] Momentum Health（冲击分 + 趋势健康 + 成熟度 + 衰竭 + 当前腿转弱）
  ├── [决策层] Background Decision（3 层加权 → bgScore → bgSupport/bgVeto/bgConflict）
  ├── [分析层] 执行评分（bg×0.55 + struct×0.25 + sigBar×0.20 → A/B/C 分级）
  └── [渲染层] label/line/box/table/plot/bgcolor + 12 alertcondition
```

## 关键参数的默认值

| 参数组 | 关键参数 | 默认值 |
|--------|---------|--------|
| 市场周期 FSM | 唐奇安周期 N=20、重叠度窗口=5、Path-A 实体倍数=1.5、Path-A ATR 偏离=0.5 | |
| 基础参数 | ATR(14)、ATR(20)、分型左右距=5 | |
| 引力场 | 触发阈值=5.0、R² 窗口=50 | |
| 背景与信号 | 信号棒最低分=0.40、背景支持阈值=0.58、冲突差阈值=0.18 | |
| 执行权重 | bg×0.55 + struct×0.25 + sigBar×0.20 | |
| 楔形校验 | 空间对称比[0.25, 2.50]、时间对称比上限=3.0、最大跨度=200 bars | |
| H/L 计数超时 | 25 bars | |
| 执行约束 | 确认K线=关闭、确认幅度≥0.60×ATR、信号分级过滤=关闭、最低等级=C | |

## 提取出的新概念

以下机制在 V4.1 源码中首次出现，此前 ingest 的概念页中未完整记录：

### 1. 唐奇安通道定位网格
唐奇安通道（N=20）不仅是 FSM 状态切换的边界，更是整个位置评分的**主坐标系**：
- `midRangeLocation`：收盘在 donchMid ± donchSpan×20% → 减 0.28 分
- `lateBreakoutLong/Short`：收盘已超过前高/前低边界 0.6×ATR → 减 0.20 分
- `bullTargetNearby/bearTargetNearby`：目标位（对向边界）在 0.80 ATR 内 → 减 0.16 分
- `atBullSupport`：距 donchL ≤ 0.60 ATR
- `atBearResistance`：距 donchH ≤ 0.60 ATR

→ 创建 [[donchian-channel]]

### 2. Path-A / Path-B 双路径突破
Range → New Breakout 有两种触发路径：
- **Path-A**：单根大实体棒（body > 1.5×ATR20）且收盘超越唐奇安边界 + ATR 偏移
- **Path-B**：累计 3+ 次连续收盘在唐奇安边界同一侧（brkCnt >= 3）

Path-A 需要更大的单棒冲击力，Path-B 需要持续的边界穿透——两者互补。此前文档中仅描述了「突破」状态，未区分双路径。

→ 更新 [[fsm-market-cycle]]

### 3. 五元素过渡证据计数器
V4.1 用 5 个独立布尔信号做过渡判定，`transitionCount >= 2` 即触发：
1. `transitionByOverlap`：重叠度 > 0.32
2. `transitionBySlopeLoss`：EMA 不再陡峭或已走平
3. `transitionByBroadChannel`：阶段=通道 + 重叠度>0.24 + 置信度<0.72
4. `transitionByWedge`：检测到上升或下降楔形
5. `transitionByFailedBreakout`：假突破或紧急逃生触发

→ 更新 [[fsm-market-cycle]]

### 4. Phase 方向恢复
FSM 状态 0/1/3 的 `fsmDir == 0` 时，默认取 EMA3 斜率方向——防止状态切换后短暂的方向真空期。

→ 更新 [[fsm-market-cycle]]

### 5. 信号棒评分独立子模块
信号棒评分是一套独立的 3 因子加分制（非加权）：
- 收盘在棒线 75%以上/以下：+0.4
- 实体 ≥ 5 周期均实体的 1.2 倍：+0.3
- (close-low)/range 或 (high-close)/range ≥ 0.6：+0.3
→ `signalBarScore ∈ [0, 1.0]`，与结构分、背景分在最终 `lFin/sFin` 中加权合成。

### 6. 动量健康的四个子维度
此前 concept 页已覆盖 trendHealth/trendMaturity/exhaustRisk 三个子维度，V4.1 新增第四个：
- **currentLegWeakening**（当前腿转弱）：当 impulseScore 低于前值 + 重叠度升高 + EMA 不再陡峭 + 楔形出现 → 当前波动腿正在失去力量

这四个维度组合为：`momScore = 0.10 + impulse×0.30 + trendHealth×0.28 + swingCompare×0.12 - maturity×0.20 - exhaust×0.18 - legWeakening×0.12`

### 7. 背景否决的精确条件（4 类，源码级别）
| 否决类型 | 条件 |
|---------|------|
| 中部否决 | `midRangeLocation AND phaseIsRange` |
| 逆势否决 | 健康趋势且方向相反 + 对向衰竭风险<0.55 + 无楔形/H2支撑 |
| 追价否决 | 阻力位追多做多 / 支撑位追空做空 |
| 复合否决 | (成熟度≥0.65 或 衰竭≥0.60) + 当前腿转弱≥0.50 + 晚突破 |

→ 更新 [[background-scoring-engine]]

## 与现有知识的对应关系

| V4.1 模块 | 已有概念页 | 本次更新 |
|----------|-----------|---------|
| FSM 周期状态机 | [[fsm-market-cycle]] | +Path-A/B +5元素过渡 +方向恢复 |
| 三推楔形 | [[three-push-wedge|Three Push Wedge]] | 已覆盖，本次不更新 |
| 引力场 | [[gravity-field]] | +V4.1 来源引用 |
| H2/L2 状态机 | [[h2-l2-state-machine|H2/L2 State Machine]] | 已覆盖，本次不更新 |
| 紧急逃生 | [[emergency-exit]] | 已覆盖，本次不更新 |
| 背景评分引擎 | [[background-scoring-engine]] | +V4.1 来源引用 +否决4类精确条件 |
| 执行评分 | [[execution-scoring]] | 已覆盖，本次不更新 |
| 确认K线 | [[confirmation-bar]] | 已覆盖，本次不更新 |
| 唐奇安定位 | 🆕 [[donchian-channel]] | 新建 |

## 与已有资料的冲突

- **过渡检测差异**：V4.1 的 5 元素过渡检测（≥2 触发）比 ctx-scoring 中记录的 2 元素检测（仅 ema 变平 + 唐奇安扩张）更全面。两个引擎的过渡判定体系不同——ctx-scoring 是 Brooks 四步框架的 Pine 实现，V4.1 是 WG Brooks 引擎的嵌入式过渡检测。
- **权重差异**：V4.1 的执行分权重为 bg×0.55+struct×0.25+sigBar×0.20（默认值），而 execution-scoring 记录的三因子权重可能来自 v3 执行引擎的不同版本。V4.1 源码确认了此权重，应更新 execution-scoring 的概念页。

## V4.1 修复记录（来源码注释）

1. 修复缺失变量 `bgEventColor` / `bgEventTextColor`（V3 编译错误）
2. 修复 `line.set_xy1` 五参数调用错误（改为两次调用）
3. 全部使用 `label.new` 替代 `plotchar`（保持 V3 可视化风格）
4. 界面文本中文化（指标名称、plot 标题、Alert 消息）
