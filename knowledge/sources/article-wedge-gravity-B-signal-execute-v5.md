# 楔形引力 · 信号执行引擎 V5.0（指标B）

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6，V5.0 版本号）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_B_signal_execute_v5.txt`
- 格式：Pine Script v6 源码（955行）

## 一句话摘要
楔形引力系统的「指标B」——负责供需区/订单块识别、三层背景评分（位置×0.40+阶段×0.35+动能×0.25）、三因子执行评分（背景×0.55+结构×0.25+信号棒×0.20），最终输出多空入场信号（ABC等级）+ 紧急逃生预警。

## 核心模块

### 1. 供需区识别（Supply/Demand Zones）
- **类型系统**：`ZoneData` 包含 barStart/barEnd/highPrice/lowPrice/originPrice/isSupply/strength/isValid/isTested/testCount
- **供应区**：strongDown（实体>5均×倍率 + 阴线 + close<前低）+ baseRBR/RBD（前根小实体确认）→ 取3根范围 → 去重后入栈
- **需求区**：strongUp（实体>5均×倍率 + 阳线 + close>前高）+ demandBaseRBD/RBR → 同理
- **生命周期**：maxBars=100（可调），过期自动清理
- **强度倍数**：默认1.2×avgBody5（可调0.5-3.0）

### 2. 订单块识别（Order Blocks）
- **类型系统**：`OBData` 包含 barIndex/highPrice/lowPrice/isBullish/strength/isValid/isRetested
- **多头OB**：bearishOB（强阴线+实体>5均×1.5 + close<前低）遇 confirmUp（前根强阳线+close>本根high）→ 确认
- **空头OB**：bullishOB（强阳线+实体>5均×1.5 + close>前高）遇 confirmDown（前根强阴线+close<本根low）→ 确认
- **生命周期**：maxBars=80（可调，20-200）
- **强度倍数**：默认1.5×avgBody5（可调0.5-3.0）

### 3. 背景评分三层体系
每一根K线同时计算多头/空头两套背景分：

**位置层 (Location，权重0.40)**：
- 多头支持来源：距 pl0/donchL/EMA20/fib50 的最小 ATR 距离
- 空头支持来源：距 ph0/donchH/EMA20/fib50 的最小 ATR 距离
- atBullSupport（≤0.60 ATR）、nearBullSupport（≤1.20 ATR）、midRangeLocation（距donchMid≤20%区间）
- 区间中部位置对多空双方均扣分（-0.28）

**阶段层 (Phase，权重0.35)**：
- 趋势健康条件：phaseIsTrend + fsmConf≥0.70 + emaSteep + avgOlp<0.24
- 多头偏好：fsmDir==1 + 趋势健康 → +0.52；fsmDir==-1 + (下降楔形/H2/近支撑) → +0.22
- 空头偏好：fsmDir==-1 + 趋势健康 → +0.52；fsmDir==1 + (上升楔形/L2/近阻力) → +0.22
- 双向市场(phaseTwoSided)不处于关键位置时扣分

**动能层 (Momentum，权重0.25)**：
- 脉冲分（impulseScore）= bodyRatio×0.55 + breakMag×0.45
- 趋势健康分（trendHealthL/S）= impulseScore×0.35 + EMA陡峭+0.25 + 低重叠+0.20
- 衰竭风险（exhaustRiskL/S）= 楔形+0.25 + 高重叠+0.15
- 逆势结构加成：fsmDir相反 + (楔形/H2/L2) → +0.12

**背景决策层**：
- bgScoreL/S = locScore×0.40 + phaseScore×0.35 + momScore×0.25
- 背景冲突：一方<bgThr且>0.42，或双方分差>confThr(0.18)
- 背景否决：区间中部 + 区间阶段 → bgVeto
- 背景状态：多强(≥0.72)/多可/空强/空可/中性/否决

### 4. 执行评分体系
- **结构分**：下降楔形=0.70 / H2=0.55 / 上升楔形=0.70 / L2=0.55（简化为固定值，非v3版四维度累加）
- **信号棒分**：收盘极值(75%区间)0.4 + 实体强度(≥1.2×avgBody5)0.3 + 突破幅度(≥60%区间)0.3
- **lFin/sFin** = bgScore×0.55 + structureScore×0.25 + signalBarScore×0.20（权重可调）
- **ABC等级**：A≥0.80 / B≥0.60 / C<0.60

### 5. 信号门控链路
candidate（结构≥0.45 + 信号棒≥sigThr + close>midPt）→ bgSupport（非冲突+非否决+≥bgThr）→ bgVeto → gradeFilter → confirmBar(可选) → 最终信号

### 6. 紧急逃生预警
- 假突破（brkFail_EMG）：近3根破ph0但close<ph0
- 实体衰竭（exhBars）：连续2根实体重叠>70%
- 竭尽K线（exhCdl）：body≥1.5×avgB20 + range>1.2×ATR14
- emergNew = emergExit and not emergExit[1]（仅触发首根标记）

### 7. 渲染与信息面板
- 供需区/订单块：box绘制，最多显示3个
- 信号标签：含结构名/背景状态/等级/入场/止损/止盈
- TP/SL/ENT参考线：dotted入场+虚线止损止盈
- 18行信息面板：FSM状态/背景分(位置/阶段/动能/综合)/结构优先级/信号棒分/执行分等级/供需区OB计数/逃生状态/综合信号

## 提取出的新概念
- [[supply-demand-zone]] — 供需区识别（ZoneData类型 + 供应/需求区检测算法）
- [[order-blocks]] — 订单块识别（OBData类型 + 多空OB确认机制）

## 与现有知识的冲突
- **结构分简化**：V5.0 将结构分简化为固定值（楔形=0.70/H2=0.55/L2=0.55），此前 v3 执行引擎使用四维度累加结构分。V5 版本更简洁但丢失了细节粒度。
- **与 indicator A 的跨指标绑定**：源码中 `getIndicatorData()` 函数仅返回零值，V5 实际方案是「本地重新计算关键数据确保独立性」，放弃了 v3 的 `input.source` 跨指标 API 绑定方式，改回单指标自给自足。
- **引力场计算**：V5 的 gScore 仅使用 EMA20/ph0/pl0/fib50 四个引力源（vs V1.5 含 ph1/pl1/三日开盘重心共七个），门槛 gravOK=gScore>5.0（V1.5 使用可调参数 i_gThr），这些差异反映 V5 对引力场的简化定位——仅作为位置评分的辅助加成（locScore +0.12）而非独立评分维度。
