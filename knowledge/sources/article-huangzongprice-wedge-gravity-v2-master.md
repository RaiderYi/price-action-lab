# Wedge-Gravity V2 Master · Brooks

## 元信息
- 作者：huangzongprice
- 日期：未标注（V2 Master，介于 V1.5 和 V4.1 之间；`@version=6`，`calc_on_every_tick=false`）
- 原始位置：`raw/articles/huangzongprice/wedge_gravity_tradingview_master_v2.txt`
- 格式：Pine Script v6（1093 行，overlay indicator）

## 一句话摘要
Wedge-Gravity 系统的 V2 生产级主版本——将 V1.5 双核架构升级为完整的 Brooks 四步法集成，新增 FSM 周期策略门控、楔形三因子质量评分、趋势/反转分离评分、ABC 信号分级、7 层可配置信号可靠性管道，是 Wiki 中可追溯的最完整单文件实现。

## 核心论点

### 整体架构（9 模块流水线）
1. **基础指标**：ATR14/20、EMA20、K 线基础量（实体/振幅/中点）
2. **FSM 传感器**：EMA 斜率（emaSteep/emaFlat）、K 线重叠度（avgOlp）、唐奇安通道（donchH/L，20周期）
3. **FSM 市场周期引擎**：四状态机（BREAKOUT/CHANNEL/TRADING_RANGE/NEW_BREAKOUT）+ 三条硬规则转移路径 + Path-A/B 双路突破
4. **N-Bar 分型极点**：ta.pivothigh/pivotlow（swN=5），精准定位 ph0/1/2 和 pl0/1/2
5. **三推楔形识别**：上升/下降楔形 + 三因子评分（对称性40%+收口35%+跨度25%）
6. **引力场**：高斯衰减模型——EMA20、ph0/pl0、ph1/pl1、fib50、3日缺口 的加权吸引力
7. **Brooks 四步背景层**：Step1 价位（7种S/R→ctx1_score）→ Step2 阶段（FSM+过渡→ctx2_score）→ Step3 动能（重叠/斜率/衰竭/实体→ctx3_score）→ Step4 否决（TR位置+紧急逃生）
8. **信号评分合成 + 7层可靠性管道**：lFin/sFin → 失败过滤 → 重叠过滤 → 关键位过滤 → 分级过滤 → 确认K线 → Brooks否决
9. **动态风控 + 可视化**：ENT/SL/TP 线、信号K线高亮、26行信息面板、9条警报条件

### V2 相对 V1.5 的核心新增
- **Brooks 四步法完整集成**：通过 `i_useBrooks4` 总开关可选启用，ctx1/ctx2/ctx3 评分 + Step4 否决完整落地
- **周期策略门控**：FSM 状态 → allowLong/allowShort 精确规则（突破仅顺势、通道顺势+边界逆势、震荡仅边界反向）
- **趋势/反转分离评分**：趋势信号侧重动量（momScore×0.70 + posScore×0.30），反转信号侧重位置（posScore×0.60 + momScore×0.40）
- **楔形三因子质量评分**：对称性(symScore×0.40) + 收口(convScore×0.35) + 跨度(spanScore×0.25)
- **信号分级 ABC**：A(≥0.80)、B(≥0.60)、C，可选最低等级过滤
- **7层可靠性管道**：失败过滤 / 重叠过滤 / 关键位过滤 / 分级过滤 / 确认K线 / Brooks否决（G7参数组）
- **Path-A/B 双路突破**：Path-A（激进即时，单根大实体+收盘越界）、Path-B（保守延迟，连续3根收盘维持边界外）
- **过渡检测**：EMA 斜率突变（emaSteep[1]→emaFlat）或唐奇安宽度扩张（donchWiden）
- **函数化风控线**：`f_riskHz()` / `f_riskLb()` 减少重复代码

### V2 与后续版本的关系
- **V2 → V4.1**：V4.1 保留 V2 的核心架构（FSM+楔形+评分+四步法），新增信号优先级体系（5级）和背景评分微细则
- **V2 → v3 Context/Execution 分离**：v3 将 V2 的单体内嵌架构拆分为两层（Context Engine + Execution Engine），V2 的 ctx1/ctx2/ctx3 在 v3 中演变为 locScore/phaseScore/momScore 三层加权
- **V2 → V5.0**：V5.0 保留 V2 的楔形三因子评分（symScore×0.40 + convScore×0.35 + spanScore×0.25）和周期策略门控，但放弃 Brooks 四步法集成

## 提取出的新概念
- [[cycle-strategy-gating]]：FSM 周期策略门控——V2 Master 中 allowLong/allowShort 的精确规则首次以完整代码呈现
- [[signal-grading-system]]：信号分级 ABC——V2 首次引入的三级分级+可选最低等级过滤

## 与现有知识的关联
- 本源码是 [[article-wg-v15-analysis]]（V1.5分析）和 [[article-20260519-wedge-gravity-brooks-v1-pine]]（V1 Brooks源码）的直接升级版本
- Brooks 四步法的精确公式（ctx1/ctx2/ctx3_score）在本源码中首次通过加权加法完整公开——此前 [[ctx-scoring]] 页仅记录了定性描述，V2 源码提供了精确权重
- V2 的 `fsm=0` 路径：与 V1.5 相同，代码中无任何语句主动设置 `fsm=0`（仅 `var int fsm = 2` 初始化），BREAKOUT(0) 仍为死分支——这与 [[article-huangzongprice-context-engine-v1]] 中 v1 standalone FSM 的 `fsm=0` 可达性形成对比

## 与现有知识的冲突
- （无明显冲突——V2 是 V1.5 的增强版，所有机制向后兼容。唯一需注意：V2 的 ctx1/ctx2/ctx3 精确公式与 v1 standalone Context Engine 的加减分制是两种不同的量化策略，已在 [[ctx-scoring]] 页分别记录）
