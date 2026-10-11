# Context + Execution 联动设置说明

## 元信息
- 作者：huangzongprice
- 日期：未标注
- 原始位置：`raw/articles/huangzongprice/context_execution_linkage_setup.md`
- 相关文件：`brooks_pa_context_engine_v2_linkable.txt`、`brooks_pa_execution_engine_v2_linked.txt`

## 一句话摘要
本文是 Context Engine v2 + Execution Engine v2 联动的**操作设置手册**——通过 Pine Script 的 `input.source` 机制将执行引擎的 25 个 API 字段逐一绑定到背景引擎的 data window 导出，实现「背景层是唯一权威来源」的架构设计。

## 核心论点

### 1. 联动架构设计理念
执行引擎 v2 不内嵌背景副本，**真正依赖**背景引擎 v2 的 API 输出。如果背景 API 未正确绑定，执行层不会给出最终信号——这是设计行为，不是 bug。

### 2. 加载顺序（不可颠倒）
1. 先加载 **Brooks PA Context Engine v2 Linkable**（背景引擎）
2. 再加载 **Brooks PA Execution Engine v2 Linked**（执行引擎）
3. 在执行引擎参数中找到「背景联动 API 绑定」，逐项绑定 25 个 source

### 3. 需要绑定的 25 个 API 字段
执行引擎中的 `绑定 API xxx` 参数 → 背景引擎数据窗口的对应导出字段：

| # | 执行引擎 source 参数 | 背景引擎导出字段 |
|---|---------------------|----------------|
| 1 | 绑定 API 版本 | API 版本 |
| 2 | 绑定 API Ready | API Ready |
| 3 | 绑定 API 背景分L | API 背景分L |
| 4 | 绑定 API 背景分S | API 背景分S |
| 5 | 绑定 API 背景支持多 | API 背景支持多 |
| 6 | 绑定 API 背景支持空 | API 背景支持空 |
| 7 | 绑定 API 背景冲突多 | API 背景冲突多 |
| 8 | 绑定 API 背景冲突空 | API 背景冲突空 |
| 9 | 绑定 API 背景否决多 | API 背景否决多 |
| 10 | 绑定 API 背景否决空 | API 背景否决空 |
| 11 | 绑定 API 阶段状态 | API 阶段状态 |
| 12 | 绑定 API 方向 | API 方向 |
| 13 | 绑定 API 阶段置信度 | API 阶段置信度 |
| 14 | 绑定 API 阶段是震荡 | API 阶段是震荡 |
| 15 | 绑定 API 阶段是过渡 | API 阶段是过渡 |
| 16 | 绑定 API 趋势健康 | API 趋势健康 |
| 17 | 绑定 API 趋势弱化 | API 趋势弱化 |
| 18 | 绑定 API 双向环境 | API 双向环境 |
| 19 | 绑定 API 趋势健康L | API 趋势健康L |
| 20 | 绑定 API 趋势健康S | API 趋势健康S |
| 21 | 绑定 API 成熟度L | API 成熟度L |
| 22 | 绑定 API 成熟度S | API 成熟度S |
| 23 | 绑定 API 衰竭风险L | API 衰竭风险L |
| 24 | 绑定 API 衰竭风险S | API 衰竭风险S |
| 25 | 绑定 API 背景状态码 | API 背景状态码 |

### 4. 联动成功的判断标准
执行引擎右上角面板显示：
- `联动状态 = 已联动`
- `API 版本 = 2 ✓`
- `API Ready = 就绪`

如果显示「未联动」「API 版本 ×」「未就绪」，说明 source 绑定不完整或绑定错误。

### 5. 失败保护机制
当以下任意条件不满足时：
- API 版本不匹配
- API Ready 不为 true
- source 绑定错误导致关键字段无效

执行层会：
- 关闭背景许可
- **不输出最终做多/做空信号**
- 面板显示未联动状态

这是为了防止「静默回退到旧背景副本逻辑」。

### 6. 推荐参数
- 背景引擎：默认值先跑一轮
- 执行引擎：
  - `要求 API Ready 才运行 = 开`
  - `要求 API 版本匹配 = 开`
  - `启用背景许可过滤 = 开`

### 7. 测试验证流程
1. 加载背景引擎 → 加载执行引擎 → 逐项绑定 API source
2. 确认面板：已联动、API 版本正确、API Ready 就绪
3. 功能验证：背景转多时多头候选更容易通过；背景否决时执行候选被压制；背景分变化会影响执行分

### 8. 技术原理
Pine Script 没有真正的脚本间变量导入机制，因此采用：
> 背景脚本导出 invisible plot API → 执行脚本通过 `input.source` 绑定

优势：背景层成为唯一权威来源，执行层不再维护背景副本，背景与执行不再漂移。

## 提取出的新概念
- [[pine-source-binding]] — Pine Script 的 `input.source` 跨指标 API 绑定技术
- [[linkage-failure-safety]] — 联动失败安全机制：防止静默回退到旧背景副本

## 与现有知识的冲突
无冲突。本文是 [[article-huangzongprice-brooks-pa-execution-engine-v3-lean-linked]]（执行引擎 v3 架构文档）的操作配套手册，二者是「架构设计」←「配置实操」的互补关系。v3 执行引擎的联动机制原理与本文 v2 版本一致，字段绑定流程通用。
