# Brooks PA Execution Engine v3 Lean Linked

## 元信息
- 作者：huangzongprice
- 类型：Pine Script v6 执行层指标
- 原始位置：`raw/articles/huangzongprice/brooks_pa_execution_engine_v3_lean_linked.txt`
- 配套说明：`brooks_pa_execution_engine_v3_lean_linked_README.md`
- 代码行数：529 行

## 一句话摘要
Brooks 价格行为量化系统的 v3 执行层——通过 20+ `input.source` API 绑定从独立 Context Engine 接收背景数据，独立产出 H2/L2 + 楔形 + 三因子评分 + ABC 等级过滤后的做多/做空信号。

## 核心论点

### 架构：两层分离
v3 采用 **Context Engine（背景引擎）→ Execution Engine（执行引擎）** 两层分离架构，替代 V1.5 的单指标双核设计。执行引擎不自行计算任何背景数据——所有背景输入通过 Pine Script `input.source` 机制从外部 Context Engine 指标绑定导入。

绑定的 API 信号共 21 个，分为三组：
- **背景许可组**：`bgSupportLong/Short`、`bgConflictLong/Short`、`bgVetoLong/Short`、`bgScoreL/S`、`bgStateCode`（9级状态码：9=否决/2=多强/1=多可/-2=空强/-1=空可/0=中性）
- **阶段信息组**：`phaseState`（0=突破/1=通道/2=震荡/3=新突破）、`phaseDir`（±1方向）、`phaseIsRange`、`phaseIsTransition`、`phaseTrendHealthy`、`phaseTrendWeakening`
- **动能评估组**：`trendMaturityL/S`、`exhaustRiskL/S`（趋势成熟度和衰竭风险）

联动安全机制：`linkOk` = API版本号匹配（==2.0）且 Ready 信号为真；未联动时禁用所有信号。

背景许可门控（6 状态）：
```pine
allowLong          = bgSupportLong  and not bgVetoLong  and linkOk
allowShort         = bgSupportShort and not bgVetoShort and linkOk
allowTrendLong     = allowLong  and phaseDir == 1
allowTrendShort    = allowShort and phaseDir == -1
allowReversalLong  = allowLong  and (phaseDir == -1 or phaseIsTransition or phaseIsRange)
allowReversalShort = allowShort and (phaseDir == 1  or phaseIsTransition or phaseIsRange)
```

### 两路线结构检测

**路线A：H2/L2** — 4 阶段状态机
- 多头链：`isPL` 起步 → 破高得 H1 → 回撤 → 再破 H1 高点 → H2 信号
- 空头链：`isPH` 起步 → 对称得 L2
- 内置超时机制（`i_timeoutH2L2`，默认 25 bars）
- 孕线（`insideBar`）跳过不推进状态
- H2 候选限定为顺势（`allowTrendLong`），L2 同理

**路线B：楔形** — 简化布尔检测
- 上升楔形（偏空）：三 pivot high 上升 + 时间序正确 + 跨度在 8~200 bars 范围
- 下降楔形（偏多）：三 pivot low 下降，对称判定
- 比 V1.5 大幅简化：砍掉对称/收口/跨度三项加权评分，改为纯布尔判定
- 楔形候选限定为反转场景（`allowReversalLong/Short` + 过渡/趋势弱化/成熟度/衰竭风险条件）

**路线A+B 共振**：H2趋势候选 + 楔形反转候选同时满足时，双方结构分各 +0.10（仅当 `confluenceLong`/`confluenceShort` 为真时触发）。

### 结构分计算公式（精确）

**H2 结构分**（5 项累加后 clamp01）：
```pine
structureScoreH2 = clamp(
  (allowLong   ? 0.30 : 0)
+ (allowTrendLong ? 0.20 : 0)
+ (bgScoreL >= 0.58 ? 0.20 : 0)
+ (not bgVetoLong   ? 0.15 : 0)
+ (not bgConflictLong ? 0.15 : 0)
)
```
最大值 1.00。最低门槛 `i_h2l2MinStruct`（默认 0.45）。

**楔形结构分**（4 项累加后 clamp01）：
```pine
structureScoreWedgeLong = clamp(
  (fallingWedge      ? 0.55 : 0)
+ (allowReversalLong ? 0.20 : 0)
+ (phaseIsTransition ? 0.15 : 0)
+ (exhaustRiskS >= 0.50 ? 0.10 : 0)
)
```
最大值 1.00。最低门槛 `i_wedgeMinStruct`（默认 0.45）。做空方向对称公式。

**执行分取两路线较大者的结构分**：
```pine
structureScoreLong  = max(longByH2 ? scoreH2 : 0, longByWedge ? scoreWedge : 0)
structureScoreShort = max(shortByL2 ? scoreL2 : 0, shortByWedge ? scoreWedge : 0)
```

### 三因子执行评分
```
execScore = bgScore × 0.55 + structureScore × 0.25 + signalBarScore × 0.20
```
- 信号棒评分：收盘极值0.40 + 实体vs均值0.30 + 影线占比0.30
- ABC 等级：A ≥ 0.80 / B ≥ 0.60 / C < 0.60
- 用户可配最低等级过滤（`i_gradeMin`）

### 可选确认K线
`i_useConfirm` 启用后，信号在下一根 K 线突破前高/低至少 `ATR14 × 0.60` 才确认入场。比 V1.5 的简单收盘确认更严格。

### 止损/入场/目标计算
```pine
stopBuf  = max(mintick, 0.5 × ATR20)           // 止损缓冲
entBuf   = max(mintick, 0.1 × ATR14)           // 入场缓冲

longSL   = majorSL - stopBuf                    // 止损：主要摆动低点 − ATR20×0.5
longEnt  = high + entBuf                        // 入场：当前bar高点 + ATR14×0.1
longRisk = max(longEnt - longSL, 0.5 × ATR14)   // 风险 ≥ 0.5 ATR
longTP   = longEnt + 2.0 × longRisk             // 止盈：固定 2:1 R:R

shortSL  = majorSH + stopBuf
shortEnt = low - entBuf
shortRisk = max(shortSL - shortEnt, 0.5 × ATR14)
shortTP  = shortEnt - 2.0 × shortRisk
```
- `majorSL` = 最近 pivot low 的值；`majorSH` = 最近 pivot high 的值
- `ATR20`（长）用于止损缓冲，`ATR14`（短）用于入场缓冲

### 简化决策面板
7 行右侧面板（替代 V1.5 的详细信息面板）：联动状态、背景、阶段、结构、等级、候选、信号。颜色编码（绿色多头/红色空头/灰色中性）。

### 出场参考线
做多/做空信号出现时自动绘制：入场线（虚点白）、止损线（虚线红/绿）、止盈线（2R，虚线绿/红）。

### 报警
6 条 `alertcondition`：H2 形成、L2 形成、多头候选、空头候选、做多信号、做空信号——全部带 `[执行层简化联动]` 前缀。

## 提取出的新概念
- [[execution-engine-architecture]] — 两层分离架构 + 简化决策面板
- [[execution-scoring]] — 三因子加权执行评分（bg×0.55+struct×0.25+sig×0.20）+ ABC 等级
- [[confirmation-bar]] — 可选确认K线机制

## 与现有知识的冲突
- **vs V1.5 lFin/sFin**：v3 用三因子公式（bg×0.55+struct×0.25+sig×0.20）替代 V1.5 五因子合成（ctxScore×ctxW+K线分×(1-ctxW)+gravBonus+structScore+extraBonus），砍掉引力加成和趋势反转加成。更简洁，但可能丢失位置信息和反转补偿。
- **vs V1.5 楔形**：v3 楔形检测从三项加权评分（对称35%+收口35%+跨度30%）退化为纯布尔判定（三 pivot + 时间序 + 跨度范围），可能漏检边缘楔形。
- **vs V1.5 H2/L2**：v3 状态机实现方式不同（4 阶段 vs bPh/sPh 多阶段），不含孕线穿透处理，信号可能不完全一致。
