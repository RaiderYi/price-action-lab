# 楔形引力 Brooks 引擎 V4.1 — 完整判断流程图

## 元信息
- **作者**：huangzongprice
- **日期**：未标注（V4.1 版本，基于 V4.2 源码）
- **原始位置**：`raw/articles/huangzongprice/流程图_楔形引力V4.1.md`
- **文档性质**：技术架构图 + 参数速查表（共 564 行，含大量 ASCII 流程图）

## 一句话摘要
WG Brooks Context Engine V4.1 的完整架构文档——从 OHLC 输入到最终入场信号的 7 层流水线，每个模块的精确判定条件、参数阈值和状态转换硬规则。

## 核心论点

### 总体架构（7 层流水线）
1. **基础指标计算层**：ATR14/ATR20、EMA20、唐奇安通道、N-Bar 分型、K 线重叠度、引力场得分
2. **市场周期 FSM**：4 状态（BREAKOUT→CHANNEL→RANGE→NEW_BREAKOUT），每根 K 线最多一次状态转移
3. **结构识别层**：三推楔形（5 点模式 + 4 校验条件）、Brooks H/L 计数状态机、紧急逃生预警
4. **背景决策层**：三层加权评分——Location(40%) + Phase(35%) + Momentum(25%) → 背景分 → 背景支持/否决
5. **执行层**：结构信号 + 背景支持 + 信号棒评分 → 入场信号；动态风控计算 Entry/StopLoss/TakeProfit

### FSM 状态转换硬规则（带精确量化条件）
- **转换 A（突破→通道）**：barRng ≥ 1.0×ATR20 AND 逆势 K 线
- **转换 B（通道→震荡）**：逆势强 K 线三条件——barBody>1.0×ATR20 + 极强收盘(25%内) + 突破ph0/pl0
- **转换 C（震荡→新突破）**：Path-A 即时（大实体>1.5×ATR20+收盘超出+创新高/低）或 Path-B 延迟（连续3根收盘在边界外）

### 背景评分微细则
- **Location 40%**：atBullSupport +0.30, nearBullSupport +0.18, 引力场触发 +0.12, 接近50%Fib +0.08, EMA下方 +0.05；中部 -0.28, 追多 -0.20, 靠近空头阻力 -0.28~-0.14
- **Phase 35%**：趋势健康 +0.52, 趋势转弱 +0.30, 下降楔形+H2+近支撑 +0.22, 震荡+近支撑 +0.24
- **Momentum 25%**：冲击分(实体+收盘位) + 趋势健康(EMA+重叠度+无逃生) + 波动比 + 加分项(H2/L2结构 +0.12)
- **背景否决**：中部+震荡、健康趋势与策略方向相反、晚突破、高成熟度+高衰竭+当前腿转弱+晚突破

### 信号优先级体系（5 级）
1. 硬规则事件（周期状态切换）→ 立即执行
2. 紧急逃生预警 → 提示风险
3. 结构识别 → 提供交易机会
4. 背景决策 → 否决或支持
5. 信号生成 → 最终入场信号

### 动态风控公式
- stopBuf = max(mintick, 0.5×ATR20), entBuf = max(mintick, 0.1×ATR14)
- ENT 和 SL 基于结构极值 + 缓冲；Risk = max(ENT-SL, 0.5×ATR14)；TP = ENT ± 2.0×Risk

## 提取出的新概念

### 此前 Wiki 已覆盖的概念（含新细节补充）
- [[wedge-gravity-dual-core]] — 双核架构（已有）；新增 V4.1 三层评分微细则和背景否决条件
- [[fsm-market-cycle]] — FSM 四状态机（已有）；新增精确量化转换阈值
- [[three-push-wedge|Three Push Wedge]] — 三推楔形（已有）；新增 5 点模式识别图和 4 项校验条件
- [[h2-l2-state-machine|H2/L2 State Machine]] — H2/L2 计数（已有）；新增完整状态转换图和超时保护
- [[emergency-exit]] — 紧急逃生（已有）；新增三种预警类型和精确触发条件
- [[gravity-field]] — 引力场（已有）；新增 Location 层引力场触发分(+0.12)
- [[signal-scoring-synthesis]] — 信号评分合成（已有）；新增信号棒评分阈值(0.40)和执行分三权重

### 本次新建概念
- [[signal-priority-system]] — 5 级信号优先级体系：从硬规则到入场信号的完整决策层级
- [[background-scoring-engine]] — 背景评分引擎：Location/Phase/Momentum 三层微细则
- [[dynamic-risk-control]] — 动态风控参数：ATR 缓冲 + 结构极值的 SL/ENT/TP 计算

## 与现有知识的冲突
- **背景评分体系**：[[wedge-gravity-dual-core]] 将三层评分归于 v3 升级，但本 V4.1 文档已包含完整的三层评分细则（40/35/25 权重）。这说明三层评分可能在 V4.1 阶段已实现，而非 v3 独有的架构演进。时序关系需澄清。
- **信号评分合成**：[[signal-scoring-synthesis]] 中的 lFin/sFin 公式（五因子）与本 V4.1 的执行分三权重公式（bg×0.55+struct×0.25+sig×0.20）是两套不同的评分体系——前者是 V1.5 的软评分核，后者是 V4.1/v3 的三因子执行分。需标注版本差异。
- **参数默认值差异**：V4.1 文档给出 `i_bgThr=0.58, i_sigThr=0.40`，而 [[signal-scoring-synthesis]] 未记录具体默认阈值——两页应互补。
