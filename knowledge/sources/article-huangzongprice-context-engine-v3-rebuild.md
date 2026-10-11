# Wedge-Gravity Brooks Context Engine V3 Clean Rebuild — 防缩放版

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6 指标）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_brooks_context_clean_v3_rebuild.txt`
- 代码行数：1201 行
- 版本定位：V3 纯净重构版——与 V5 全栈版和 V1 执行引擎形成版本光谱
- 脚本类型：独立 overlay 指标（单文件自包含）

## 一句话摘要
V3 Clean Rebuild 是 WG Brooks 引擎的**防缩放重构版**——主图仅保留纯可视化元素（line/box/bgcolor），所有文字标签和历史事件不参与 TradingView autoscale，解决了标注导致图表缩放的痛点。架构上与 V5 共享三层背景决策 + 三因子执行评分核心，但无 SMC 供需区/订单块，代码更精简。

## 核心论点

### 防缩放设计（Anti-Autoscale）——本版核心创新

```
主图层（参与autoscale）：line / box / bgcolor / plot → 纯视觉
不参与autoscale：label / plotchar / plotshape → 文字/标签/事件标记
```

TradingView 默认将所有图形对象纳入 Y 轴自动缩放——标注密集时图表被压成一条线。V3 Rebuild 通过 `plotchar`（轻量事件标记）替代 `label` 作为主要标注手段，配合 `max_labels_count`/`max_lines_count` 限制，实现标注与价格范围的彻底解耦。详见 [[anti-autoscale-rendering]]。

### 架构总览：7 层流水线

```
OHLC → [基础层: ATR/EMA/Donchian/N-Bar Pivot]
     → [分析层: FSM / 楔形 / 引力场 / H2-L2 / 紧急逃生]
     → [背景决策层: Location(40%) + Phase(35%) + Momentum(25%)]
     → [执行层: bgScore×0.55 + structureScore×0.25 + signalBarScore×0.20]
     → [显示状态层: 事件对象状态 + 单例缓存]
     → [渲染层: plotchar事件 + line/box/label单例 + 主图plots + bgcolor]
     → [警报层: 10种alertcondition]
```

### 市场周期 FSM（四状态精确转换）

| 状态 | 编码 | 转移条件 | 置信度动态调整 |
|------|------|---------|--------------|
| BREAKOUT | 0 | bo2ch → CHANNEL | avgOlp<0.20+EMA陡=0.90 else 0.65 |
| CHANNEL | 1 | ch2rng → RANGE | EMA陡+非平=0.75 else 0.50 |
| TRADING_RANGE | 2 | rng2nbk → NEW_BREAKOUT | EMA平=0.80 else 0.50 |
| NEW_BREAKOUT | 3 | bo2ch → CHANNEL | same as BREAKOUT |

**转换路径精确条件**：
- `bo2ch`（突破→通道）：FSM∈{0,3} 且振幅≥1.0×ATR20 且方向K线回撤
- `ch2rng`（通道→区间）：FSM=1 且实体>1.0×ATR20 且收盘贴近极值并突破分型极点
- `rng2nbk`（区间→新突破）：Path-A（强力突破：实体>1.5×ATR20+收盘突破Donchian边界+偏移ATR）或 Path-B（连续3根收盘突破同侧Donchian边界）

### 三层背景决策（与 V4.1/V5 一致）

固定权重：`bgScore = locScore×0.40 + phaseScore×0.35 + momScore×0.25`

**Location 层（40%）**：6 个关键价位 ATR 归一化距离 + 加减分制（详细见 [[position-layer-scoring]]）
**Phase 层（35%）**：FSM 方向 + 5 过渡检测 + 阶段健康分类（详细见 [[background-scoring-engine]]）
**Momentum 层（25%）**：四子评分互锁系统（详细见 [[momentum-health]]）

### 背景许可与否决

- **背景冲突**：bgScore 低于阈值但仍>0.42，或对立方向分差>0.18，或双边势+无支撑/阻力
- **背景否决（4类）**：区间中部+震荡 / 逆势健康趋势（无楔形/H2支撑）/ 追价场景 / 高成熟度+高衰竭+腿弱化+追价叠加
- **背景支持**：bgScore≥阈值(0.58) 且 领先对手≥0.02 且 无冲突/否决
- **6 种状态码**：否决 / 多强 / 多可 / 空强 / 空可 / 中性

### 过渡检测系统（5 证据计数器）

5 个过渡证据 → 计数≥2触发 `phaseIsTransition`：
1. 重叠度过高（avgOlp > 0.32）
2. EMA 斜率丧失（不陡 or 平坦）
3. 宽通道（通道状态+高重叠+低置信度）
4. 楔形形态（上升/下降楔形）
5. 假突破/衰竭（breakFail_EMG or emergExit）

### 紧急逃生（3 条件）

与 V4.1/V5 相同：假突破（近3K破ph0但close<ph0）/ 双根实体衰竭（连续重叠>0.7）/ 竭尽K线（实体≥1.5×avgBody20 + 波幅>1.2×ATR14）

### 执行评分

`lFin = bgScoreL×0.55 + structureScoreL×0.25 + signalBarScoreL×0.20`（权重可配置）
- 结构分来源：下降楔形（对称×0.40+收敛×0.35+跨度×0.25）或 H2（固定 0.55）
- 信号棒分：三分项（收盘位+实体+突破幅度，各0.3-0.4）
- ABC 三级：≥0.80=A / ≥0.60=B / else C
- 可选确认K线（i_useConfirm）和分级过滤（i_useGradeFilter）

### 信息面板（30行 × 2列）

市场周期 → 趋势方向 → 置信度/R² → 背景结论 → 位置分 → 阶段分 → 动量分 → 背景分 → 背景支持/否决 → 位置特征 → 阶段特征 → 过渡证据 → 动能健康 → 成熟度 → 衰竭风险 → 楔形形态 → H/L计数 → 结构优先级 → 信号棒分 → 结构分 → 执行分/等级 → 多头/空头背景许可 → 紧急逃生 → 候选信号 → 前方目标 → 引力场得分 → 综合信号

### 警报条件（10种）

做多入场 / 做空入场 / 新突破启动 / 进入通道阶段 / 进入震荡区间 / H2做多 / L2做空 / 紧急逃生预警 / 背景转多/转空 / 背景否决触发 / 背景允许+候选

## 提取出的新概念

- [[anti-autoscale-rendering]] — V3 Rebuild 核心创新：Pine Script 中纯可视化与文字标签的分离模式
- [[momentum-health]] — 动能层四子评分互锁系统：trendHealth × 0.28 + impulse × 0.30 − trendMaturity × 0.20 − exhaustRisk × 0.18 − legWeakening × 0.12

## 与已有版本的衔接

| 版本 | 定位 | 关键差异 |
|------|------|---------|
| V1.5 | 双核架构原型 | 硬规则FSM+软评分五因子，单指标 |
| V1 执行引擎 | 单体内嵌背景 | 首次出现趋势成熟度+衰竭风险+三层许可 |
| V3 Rebuild（本版） | 纯净重构 | **防缩放设计**，无SMC模块，1201行精简 |
| V4.1 | 架构文档 | Context/Execution两层分离设计，三层评分完整 |
| V5.0 | 全栈整合 | 新增供需区+订单块，type类型化，1520行 |

V3 Rebuild 的定位是「最接近 V4.1 设计文档的纯净实现」——它保留了完整的背景决策+执行评分管线，但剥离了 V5 的 SMC 模块和类型化开销，代码更易阅读和维护。

## 与现有知识的冲突

无明显冲突。V3 Rebuild 的三层评分权重（40/35/25）和三因子执行分（55/25/20）与 V4.1/V5 完全一致，证实了这些核心公式的稳定性。

## 潜在风险
- 防缩放设计通过 plotchar 的 `location=location.belowbar/abovebar` 定位标记，可能与相邻K线视觉重叠
- 单例渲染模式（最新信号/楔形只显示一个）在快速切换行情中可能丢失历史信号上下文
