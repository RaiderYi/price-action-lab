# Brooks PA Wedge Gravity Engine V5.0 — 系统优化版

## 元信息
- 作者：huangzongprice
- 日期：未标注（Pine Script v6 指标）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_brooks_context_v5.txt`
- 代码行数：1520 行（含注释/更新日志）
- 版本演进：V1.5→V4.1→V5.0（基于 V4.1 全面重构）
- 脚本类型：独立 overlay 指标（单文件自包含，不支持 input.source 绑定）

## 一句话摘要
V5.0 将楔形识别、FSM、引力场、H2/L2、紧急逃生、供需区、订单块、三层背景决策、执行评分全部集成到单一 Pine Script v6 指标中——新增 supply/demand zone 和 order block 识别模块，引入 Pine Script v6 类型化数据结构（WedgeData / ZoneData / OBData）。

## 核心论点

### 架构总览：V5 单体全栈引擎

```
OHLC → [基础层: ATR/EMA/Donchian/N-Bar Pivot]
     → [分析层: FSM / 楔形 / 引力场 / H2-L2 / 紧急逃生 / S-D Zone / OB]
     → [背景决策层: Location(40%) + Phase(35%) + Momentum(25%)]
     → [执行层: bgScore×0.55 + structScore×0.25 + sigBarScore×0.20]
     → [渲染层: 极点标签/楔形连线/周期标签/H2L2/逃生/背景/信号/面板]
     → [警报层: 10种警报条件]
```

### V5.0 核心新增（vs V4.1）

#### 1. 类型化数据结构（Pine Script v6 type）
- `WedgeData`：楔形 5 极点（bar/price）+ 3 维评分（symScore/convScore/spanScore）
- `ZoneData`：供需区（起始/结束/上下限/原点/方向/强度/测试状态）
- `OBData`：订单块（所在bar/上下限/多空方向/强度/回测状态）
- 统一对象生命周期管理（单例模式 for 渲染对象）

#### 2. 供需区识别模块（G6 参数组，V5 新增）
独立于 Brooks 经典 S/R 的 SMC 风格供需区检测：
- **供应区识别**：强下跌后出现 RBR（Rally-Base-Rally）或 RBD（Rally-Base-Drop）→ Base区（小实体）→ 标记为供应区
- **需求区识别**：强上涨后出现 DBD（Drop-Base-Drop）或 DBR（Drop-Base-Rally）→ Base区 → 标记为需求区
- **强度验证**：强K线实体 ≥ avgBody5 × 1.2，Base区实体 < avgBody5 × 0.3
- **生命周期**：可配置最大 bar 数（默认 100），自动过期清理
- **重叠检测**：新区域与已有区域重叠时跳过，避免重复标记
- **可视化**：红色半透明框（供应区）、绿色半透明框（需求区），最多显示最近 3 个

#### 3. 订单块识别模块（G7 参数组，V5 新增）
- **多头 OB**：强势下跌阴线（实体 > avgBody5 × 1.5 + 收盘低于前低）→ **下一根必须反向强上涨**（实体 > avgBody5 × 0.8 + 收盘高于OB高）才算确认
- **空头 OB**：强势上涨阳线 → 下一根必须反向强下跌确认
- **强度验证**：OB K线实体 ≥ avgBody5 × 1.5
- **确认机制**：避免"孤立的强K线"被误判为OB
- **生命周期**：默认 80 bar，自动过期清理
- **可视化**：绿色半透明（多头OB）、深红色半透明（空头OB），最多显示最近 3 个

#### 4. 代码结构优化
- 使用 type 封装减少变量传递复杂度
- 统一的单例模式管理所有渲染对象（line/box/label）
- 供需区/OB 清理使用独立循环变量名避免作用域冲突（V5.0b 修复）

### 核心模块（继承自 V4.1）

#### 市场周期 FSM（四状态）
| 状态 | 编码 | 转移路径 |
|------|------|---------|
| BREAKOUT | 0 | bo2ch → CHANNEL |
| CHANNEL | 1 | ch2rng → RANGE |
| TRADING_RANGE | 2 | rng2nbk(Path-A强力突破 / Path-B连续3根) → NEW_BREAKOUT |
| NEW_BREAKOUT | 3 | bo2ch → CHANNEL |

动态置信度调整：突破/新突破 → avgOlp<0.20+EMA陡峭=0.90 否则 0.65；通道 → EMA陡峭+非平坦=0.75 否则 0.50；区间 → EMA平坦=0.80 否则 0.50

#### 三推楔形识别
- **上升楔形**（偏空）：H-L-H-L-H 结构，`ph2b < pl1b < ph1b < pl0b < ph0b`，价格上升+上下界斜率收口
- **下降楔形**（偏多）：L-H-L-H-L 结构，`pl2b < ph1b < pl1b < ph0b < pl0b`，价格下降+上下界斜率收口
- 三维修正：对称分（空间比+时间比）×0.5 + 收敛分 + 跨度分

#### 引力场
高斯加权引力模型，6 个引力源：EMA20(×3.0), ph0(×5.0), pl0(×5.0), ph1(×3.0), pl1(×3.0), fib50(×4.0)。总得分 > 5.0 阈值触发 `gravOK`。

#### H2/L2 状态机
- **做多路径**：分型低点→H1(过前高)→触发H2→H2(再过H1高)→H2信号
- **做空路径**：分型高点→L1(破前低)→触发L1→L2(再破L1低)→L2信号
- 超时重置：25 bar 内未完成即重置（可配置）

#### 紧急逃生
三种触发条件：假突破（近3根破ph0但收盘回落）、实体衰竭（连续2根重叠度>0.7）、竭尽K线（实体≥avgBody20×1.5 + 波幅>ATR14×1.2）

#### 三层背景决策
固定权重：`bgScore = locScore×0.40 + phaseScore×0.35 + momScore×0.25`
- 位置层：6价位（ph0/pl0/donchH/donchL/EMA20/fib50）ATR归一化距离 + 加减分制
- 阶段层：FSM方向 + 5种过渡检测 + 阶段健康分类（健康/弱化/双向）
- 动能层：冲动×0.30 + 健康×0.28 − 成熟度×0.20 − 衰竭×0.18 − 腿弱化×0.12

背景四类否决：区间中部+震荡 / 逆势健康趋势 / 追价 / 成熟度+衰竭+目标

#### 执行评分
`lFin/sFin = bgScore×0.55 + structureScore×0.25 + signalBarScore×0.20`（权重可调）
- ABC 三级：lFin≥0.80=A / ≥0.60=B / <0.60=C
- 可选确认K线（i_useConfirm）和分级过滤（i_useGradeFilter）

### 信息面板（32行 × 2列）
市场周期 / 趋势方向 / 置信度/R² / 背景结论 / 位置分 / 阶段分 / 动量分 / 背景分 / 背景支持 / 背景否决 / 位置特征 / 阶段特征 / 过渡证据 / 动能健康 / 成熟度 / 衰竭风险 / 楔形形态 / H/L计数 / 结构优先级 / 信号棒分 / 结构分 / 执行分/等级 / 多头背景许可 / 空头背景许可 / 紧急逃生 / 候选信号 / 前方目标 / 引力场得分 / 供需区/OB数量 / 综合信号

### 警报条件（10 种）
做多入场 / 做空入场 / H2做多 / L2做空 / 紧急逃生 / 新突破启动 / 进入通道 / 进入震荡 / 背景转多 / 背景转空 / 上升楔形 / 下降楔形

## 提取出的新概念

### V5 全新概念
- [[supply-demand-zone]] — V5 新增：RBR/RBD 模式供需区识别（SMC风格，独立于Brooks经典S/R）
- [[order-block-recognition]] — V5 新增：多空订单块识别+确认机制+生命周期管理
- [[v5-integrated-architecture]] — V1.5→v3→V4→V5 架构演进全景：从双核分离到单体全栈

### V5 对已有概念的补充
- [[wedge-gravity-dual-core]]：V5 是双核架构的最新全栈整合版本
- [[ctx-scoring]]：V5 内嵌了完整的三层背景评分（40/35/25），无需 API 绑定
- [[momentum-health]]：V5 的动量层使用完全相同的五因子公式
- [[three-push-wedge|Three Push Wedge]]：V5 使用类型化 WedgeData 封装楔形数据
- [[execution-engine-architecture]]：V5 从两层分离回归单体架构
- [[execution-scoring]]：V5 使用相同的三因子执行评分（55/25/20）
- [[background-permission]]：V5 的背景许可逻辑（allowLong/Short + veto + conflict）
- [[supply-demand-zone]] / [[supply-demand-zone]]：如果存在这两个概念页，V5 提供了 Pine Script 工程化实现

## 与现有知识的衔接
- V5 是从 V4.1「Context/Execution 两层分离」的**反向演进**——将背景引擎和执行引擎重新合并到一个指标文件中，牺牲模块化换取零依赖部署
- V5 保留了三层背景评分的完整公式（与 v1 Context Engine 源码一致），但通过 type 封装使代码更可维护
- V5 新增的供需区和订单块是**SMC（Smart Money Concepts）理论**的 Pine Script 实现，与 Brooks 的经典支撑/阻力属于不同理论体系
- V5 的信息面板从 V1.5 的 15 行扩展到 32 行，成为 huangzongprice 系列指标中信息最密集的版本

## 潜在风险
- 供需区和订单块在低流动性市场可能产生误报
- 建议 H1 及以上时间框架使用
- 快速波动市场可能产生过多区域标记
- 单文件 1520 行，维护和调试的复杂度高于模块化版本
