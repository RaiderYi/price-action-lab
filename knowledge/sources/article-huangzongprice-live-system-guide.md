# btc_price_action_live.py 使用指南

## 元信息
- 作者：huangzongprice
- 日期：2026-03-06（v1.0.0 发布日期，见更新日志）
- 原始位置：`raw/articles/huangzongprice/LIVE_SYSTEM_GUIDE.md`

## 一句话摘要
`btc_price_action_live.py` 是 huangzongprice 价格行为策略的 CLI 实时交易系统，支持历史回测→实时监控的衔接流水线，以 RS 评分作为信号质量过滤器。

## 核心论点

1. **命令行即运行** — 无需 Web/Flask 依赖，`python btc_price_action_live.py` 即可交互或命令行启动，降低部署门槛
2. **回测→实时流水线** — 启动后自动先跑完整历史回测生成基准报告，再进入实时监控循环，确保交易者对策略绩效心中有数
3. **RS 评分过滤** — 所有价格行为信号经 RS（Relative Strength）评分过滤，默认阈值 70%，低于阈值的信号静默丢弃
4. **信号提醒三层机制** — 控制台醒目横幅 + 信号面板保存到 `live_output/` + 可编程回调函数（支持邮件/微信扩展）
5. **程序化接口** — 提供 `LiveConfig` 和 `BTCLiveTradingSystem` 类，可直接 import 集成到更大的系统中

## 命令行参数全景

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `--symbol` | BTCUSDT | 交易对 |
| `--interval` | 5m | 时间周期 |
| `--days` | 60 | 历史数据天数 |
| `--equity` | 10000 | 初始资金 |
| `--risk` | 0.01 | 每笔风险比例 |
| `--rs` | 70 | RS 评分阈值 |
| `--no-live` | — | 仅回测不监控 |
| `--live-interval` | 60 | 实时更新间隔（秒） |

## 提取出的新概念

- [[rs-scoring]] — RS 评分系统（信号质量的综合量化过滤器）→ 已创建概念页

## 与现有知识的冲突

- **与 `integration-summary-20260306` 互补无冲突**：INTEGRATION_SUMMARY 是架构全景（「我们要做什么」），LIVE_SYSTEM_GUIDE 是单一脚本的操作手册（「怎么跑这个脚本」）
- **RS 评分的"综合维度"未公开**：指南展示 RS 评分的使用方式（阈值、过滤），但评分的内部计算维度和权重未在本文中说明——这是待验证的知识缺口
