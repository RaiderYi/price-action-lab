# Brooks PA Execution Engine v1

## 元信息
- 作者：huangzongprice
- 日期：未标注（推测 2025 年初，早于 v3 Lean Linked）
- 原始位置：`raw/articles/huangzongprice/brooks_pa_execution_engine_v1.txt`
- 技术栈：Pine Script v6，TradingView 指标
- 代码行数：770 行

## 一句话摘要
单文件单体执行引擎，内嵌精简背景层 + H2/L2 状态机 + 三推楔形 + 三因子加权评分，在背景许可过滤后输出做多/做空信号及参考价位。

## 核心论点

### 1. 单体架构（vs v3 的链接架构）
v1 采用"背景层内嵌"设计——背景评分（locScore、phaseState、momScore、bgScore）全部在同一指标内计算，不依赖外部 Context Engine。这与 v3 的 `input.source` API 绑定 + Context/Execution 两层分离形成鲜明对比。

### 2. 背景许可三层过滤
背景评分 → 冲突检查 → 否决检查 → 净许可。六个背景状态：否决 / 多强 / 多可 / 空强 / 空可 / 中性。

### 3. H2/L2 状态机（v1 快速版）
- 四阶段：Phase0(等枢轴) → Phase1(等突破) → Phase2(等回调) → Phase3(等二次突破) → 信号
- 内含棒自动跳过（inside bar filter）
- 超时机制：25 根 K 线自动复位
- 可选"仅顺势"模式

### 4. 三推楔形（简化检测）
- 上升楔形：ph2 > ph1 且 pl0 > pl1 → 偏空
- 下降楔形：pl1 < pl2 且 ph0 < ph1 → 偏多
- 无 TBTL 参与（纯三推结构）
- 可选过渡期优先模式

### 5. 三因子执行评分
`execScore = bgScore × 0.55 + structScore × 0.25 + sigBarScore × 0.20`
→ ABC 三级等级（A≥0.80, B≥0.60, C<0.60）

### 6. 趋势成熟度与衰竭风险
v1 引入了两个 v3 中未出现的独立评分维度：
- **趋势成熟度**（trendMaturityL/S）：楔形 + 晚期突破 + 衰竭K线 + 目标接近
- **衰竭风险**（exhaustRiskL/S）：突破失败 + 楔形 + 高重叠率 + 目标接近
→ 动量评分 = 冲量分 + 趋势健康 - 趋势成熟度 - 衰竭风险

### 7. 共振增强
H2 + 下降楔形 或 L2 + 上升楔形 同时触发时，结构分 +0.10。

## 提取出的新概念

| 概念 | 文件名 | 说明 |
|------|--------|------|
| 趋势成熟度 | [[trend-maturity]] | 量化趋势老化程度（楔形/晚期突破/衰竭K线/目标接近） |
| 衰竭风险 | [[exhaustion-risk]] | 突破失败+楔形+重叠率+目标接近的四因子反向风险 |
| 背景许可过滤 | [[background-permission]] | 硬否决→软冲突→净许可的三层过滤机制 |

## 与现有知识的冲突

### v1 vs v3 (Lean Linked) 架构差异
- **v1**：背景层内嵌，单文件自包含
- **v3**：Context Engine → input.source API → Execution Engine 两层分离
- **v1 优势**：部署简单，无需跨指标联动
- **v3 优势**：背景逻辑可独立迭代，避免 H2/L2 状态机背景变量冗余

### FSM 状态机差异
- **v1**：四状态（突破/通道/震荡/新突破），transition 由重叠率+EMA陡度+avgOlp 判断
- **v3**：同样四状态，但 transition 标记更精细（显式 `phaseIsTransition`）
- **V1.5**：同样四状态，最初版本

### H2/L2 实现差异
- **v1**：内含棒跳过 + 超时复位，快速响应
- **v3**：更精简的状态机，无内含棒跳过，趋势方向从背景变量读取
- **V1.5**：最复杂的五阶段状态机

### 评分公式差异
- **v1**：三因子（bg×0.55 + struct×0.25 + sig×0.20），无引力/反转加成
- **v3**：同样三因子，但背景分来源不同（input.source 绑定 vs 内嵌计算）
- **V1.5**：五因子（lFin/sFin），含引力加成 + 趋势反转加成

## 版本链定位

```
V1.5 (单指标双核, 五因子评分)
  ↓ 架构简化
v1 Execution Engine (单体内嵌背景, 三因子评分, 新增成熟度/衰竭风险)
  ↓ 架构拆分
v3 Lean Linked (Context+Execution两层分离, input.source API绑定)
```
