# BTC 数据获取与价格行为策略集成 — 完成总结

## 元信息
- 作者：AI Assistant（huangzongprice 项目）
- 日期：2026-03-06
- 版本：2.0.0
- 原始位置：`raw/articles/huangzongprice/INTEGRATION_SUMMARY.md`
- 标的：BTC/USDT（加密货币）+ A股（沪深）
- 周期：5m / 15m / 30m / 60m / 日线 / 周线 / 月线

## 一句话摘要
将 Binance API（加密货币）和 baostock（A股）数据源与 Al Brooks 价格行为策略引擎集成，形成支持回测、实时监控、Web 界面的跨市场交易分析系统生态。

## 核心论点

### 1. 四版本系统生态
| 版本 | 脚本 | 数据源 | 运行模式 |
|------|------|--------|----------|
| BTC 回测 | `btc_price_action_backtest.py` | Binance API | 命令行批处理 |
| BTC 实时 | `btc_price_action_live.py` | Binance API | 命令行实时监控 |
| BTC Web | `app.py` | Binance API | Flask + WebSocket 浏览器界面 |
| A股 | `a_share_price_action.py` | baostock | 命令行 + Web（全量历史数据） |

### 2. 统一策略核心（All Brooks 方法论）
所有版本共享相同的策略引擎：
- **7 大入场信号**：SPB 限价单 > EMA 双测 > H1/H2/L1/L2 > 微型双底双顶(Horn) > BTC/STC > 楔形反转 > TR 逆势
- **RS 评分系统**（10+2 维度）：入场门槛 RS ≥ 70%，含趋势一致性、缺口、波幅、晚期腿惩罚（-20）
- **完整交易管理**：止损/止盈、成本保护（1R 后移至 BE）、SPB 追踪止损、时间止损（20 根 K 线）、Big Failure 立即出场

### 3. 数据源特征对比
| 特性 | Binance API | baostock |
|------|------------|----------|
| 市场 | 加密货币 | A股 |
| 数据量 | 单次最多 1000 条 | 全量历史（1990 至今） |
| 交易时间 | 24×7 | 9:30–15:00 |
| 网络要求 | 需访问 api.binance.com | 国内直连 |
| 复权 | 不涉及 | 支持前/后/不复权 |
| 交易日历 | 无 | 自动处理节假日 |

### 4. 输出报告体系
每次运行生成 4 类文件：
- 回测报告 PNG（资金曲线、回撤、胜率等 10 面板）
- 价格行为分析 PNG（按市场状态/信号类型分析 + RS 分布）
- 交易记录 CSV（完整交易明细）
- K 线数据 CSV（用于后续分析）

## 提取出的新概念
以下概念在当前 Wiki 中尚不存在，已创建对应概念页：
- [[trade-management-system]] — 完整交易管理体系（6 组件）
- [[multi-market-architecture]] — 同一 Brooks 策略跨 BTC/A股双市场部署
- [[live-trading-monitor]] — 实时交易监控系统（命令行 + WebSocket 双模式）

## 与现有知识的冲突
- **A股版本 vs 原 MES 策略**：A股版本使用完全相同的 Brooks 信号体系，但增加了复权处理、交易日历适配——验证了 Brooks 策略的跨市场通用性，也与 [[README-summary]] 中仅针对 MES 期货的定位形成互补
- **Web 界面 vs Brooks 纯主观**：Flask + WebSocket 的实时推送界面将 Brooks 方法论进一步推向量化自动化，加剧了 [[al-brooks]] 页面中已标注的"量化派 vs 主观派"张力
- **数据源限制**：Binance 1000 条/次的数据限制可能影响长时间回测的统计显著性，需在 [[trade-management-system]] 中标注
