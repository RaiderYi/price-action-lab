# PA背景分析引擎 v6 [优化版]

## 元信息
- 作者：huangzongprice
- 日期：未标注（v6，Pine Script `//@version=6`）
- 原始位置：`raw/articles/huangzongprice/@version=6.txt`
- 文件类型：Pine Script v6 源码 — 独立 overlay 指标

## 一句话摘要
Brooks PA 背景分析引擎的 v6 独立优化版：四步流水线（支撑阻力→市场阶段→动能/健康度→一票否决）重新实现，新增无重绘基础、盒体留存垃圾回收、相对定位标签和 Table 状态面板。

## 核心论点

### 1. 架构总览：四步流水线

与 [[brooks-four-step-context]] 一致的四步分析框架，但以独立 Pine Script v6 指标实现，不依赖 WG_V15 双核架构：

| 步骤 | 功能 | 输入参数组 | 关键输出 |
|------|------|-----------|---------|
| Step 0 |  | — | 未收盘K线使用上一根确认数据 |
| Step 1 | 支撑阻力定位 | `pivotLen=5`, `maxSR=6`, `srNearATR=0.35` | 阻力线数组 + 支撑线数组 |
| Step 2 | 市场阶段判断 | 16个参数（EMA/ATR/效率/重叠阈值） | 四阶段：上涨趋势/下跌趋势/震荡区间/过渡阶段 |
| Step 3 |  | `momLookback=20`, `closeExtremePct=0.25`, `climaxDistATR=2.2` | `momentumScore`(0-100) + `healthScore`(0-100) |
| Step 4 | 一票否决 | — | 6条精准否决文案 |

### 2. 关键改进（相对于此前版本）

#### 2.1 无重绘基础（Step 0）
```pinescript
o = barstate.isconfirmed ? open : nz(open[1], open)
h = barstate.isconfirmed ? high : nz(high[1], high)
```
当前 K 线未收盘时，所有 o/h/l/c 统一使用上一根已确认 K 线数据，从源头消除重绘。详见 [[anti-repainting]]。

#### 2.2 动能与健康度分离（Step 3）
v6 将 Step 3 拆分为两个独立评分体系：
- **动能分（momentumScore）**：五因子加权——趋势棒比 30% + 均线斜率 20% + EMA 距离 15% + 效率 20% + 重叠度 15%
- **健康度分（healthScore）**：四正一罚——效率 35% + 重叠度 25% + 实体质量 20% + (1-扩展惩罚) 20% - 高潮惩罚

精确加权公式 + 高潮检测（climaxPenalty）在此前版本中未公开。详见 [[momentum-health]]。

#### 2.3 可视化三修复
- **修复1 — 盒体留存与垃圾回收**：震荡区间盒体用 `var box` 持久化 + `wasRange` 状态机控制创建/扩展/断开生命周期，离开震荡后历史盒体保留在图表上
- **修复2 — 相对定位标签**：阶段切换标签改用 `yloc.abovebar`/`yloc.belowbar` 代替绝对 y 坐标，免疫图表缩放错位
- **修复3 — 极简十字信号**：SR 贴近信号从 `shape.circle` 改为 `shape.xcross`，配合相对定位去除杂音

详见 [[indicator-visual-optimization]]。

#### 2.4 Table 状态面板
使用 Pine Script v6 `table` 系统在右上角绘制 2×8 状态面板，显示：市场阶段、主导方、位置背景、动能评分、健康度、重叠与效率、一票否决。克服了 `label` 系统在图表缩放时的错位问题。

### 3. 参数体系

v6 对外暴露 **14 个可调参数**，分 4 组：
- **支撑阻力**（3）：`pivotLen=5`, `maxSR=6`, `srNearATR=0.35`
- **市场阶段**（6）：`emaLen=20`, `atrLen=14`, `stageLookback=30` + 3 个阈值（效率高 0.38/低 0.22, 趋势重叠≤0.42/震荡重叠≥0.55）
- **动能健康**（3）：`momLookback=20`, `closeExtremePct=0.25`, `climaxDistATR=2.2`
- **可视化**（7 个 bool 开关）

### 4. 与先前版本的关系

| 版本 | 架构 | 实现方式 | v6 对应的变化 |
|------|------|---------|-------------|
| WG_V15 Context Engine | 嵌入式子模块 | WG_V15 双核架构内 | v6 是独立指标 |
| v1 standalone (`brooks_pa_context_engine_v1`) | 四步流水线 + 五因子动能 | 独立 Pine Script | v6 动能拆分为双评分 + 精确公式公开 |
| v2 standalone (`brooks_pa_context_engine_v2_linkable`) | 四层显式加权 + API 导出 | 独立 Pine Script | v6 去掉 API 绑定，专注可视化 |
| v3 背景层 (`phase1`) | Playbook Engine 5 模块 | 背景-执行联动架构 | v6 回到独立模式，不涉及执行联动 |

## 提取出的新概念

- [[anti-repainting]] — 无重绘基础：实时K线使用上一根确认数据防止信号闪烁（**新建**）
- [[momentum-health]] — 动能-健康度双评分：v6 将 Step 3 拆分为两个独立评分体系并公开精确公式（**新建**）
- [[indicator-visual-optimization]] — TradingView 指标可视化优化方法论：三层信号分级+盒体留存+相对定位+Table 面板（**补建**——此前被引用但未创建）

## 与现有知识的冲突

无冲突。v6 的核心分析框架（四步流水线、四阶段判断、支撑阻力定位）与已有 [[brooks-four-step-context]] 和 [[ctx-scoring]] 一致。公开的精确加权公式补充了此前「公式未公开」的矛盾标注。

## 更新已有概念
- [[brooks-four-step-context]]：添加 v6 参考 + 标注 Step 3 动能/健康度公式已在 v6 公开
- [[ctx-scoring]]：添加 v6 momentumScore/healthScore 精确加权公式
- [[indicator-visual-optimization]]：**补建**该页面（此前被 VERSION_HISTORY 引用但从未创建），以 v6 三修复为核心案例
