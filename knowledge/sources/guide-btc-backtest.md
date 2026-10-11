# BTC 价格行为回测系统使用指南

## 元信息
- 作者：huangzongprice
- 日期：未标注
- 原始位置：`raw/articles/huangzongprice/BTC_BACKTEST_GUIDE.md`
- 标的：BTC/USDT（可扩展到 ETH 等 Binance 交易对）
- 周期：5m / 15m / 1h / 4h / 1d
- 相关脚本：`btc_price_action_backtest.py`

## 一句话摘要
huangzongprice BTC 价格行为回测系统的完整操作手册，涵盖数据获取、参数配置、回测运行、报告解读和故障排除。

## 核心论点

### 1. 三种运行模式

| 模式 | 命令示例 | 用途 |
|------|---------|------|
| 基本回测 | `--symbol BTCUSDT --interval 5m --days 60` | 从 Binance API 获取数据 → 运行完整回测 → 生成报告 |
| 本地 CSV | `--csv ./data/btc_2024.csv` | 使用已有 OHLCV 数据文件回测，绕过 API 限制 |
| 信号面板 | `--dashboard --days 14` | 仅生成当前市场状态信号快照（不运行回测），快速了解市场状态 |

### 2. 回测报告体系（10 + 7 面板）

**标准回测报告**（10个面板）：资金曲线 → 累计R值 → R值分布直方图 → 胜率饼图 → 按市场状态盈亏 → 按信号类型盈亏 → 出场原因分析 → RS评分与盈亏相关性 → 回撤曲线 → 月度盈亏。

**价格行为专项分析**（7个面板）：按市场状态平均R → 按信号类型平均R → 多空方向总盈亏 → RS评分分布 → RS评分与盈亏散点图 → 持仓时间分布 → 价格图表与交易点位。

**输出文件**：
- `*_backtest_*.png` — 标准回测报告
- `*_price_action_*.png` — 价格行为专项分析
- `*_trades_*.csv` — 交易记录明细
- `*_data_*.csv` — K线数据（便于二次分析）
- `signal_dashboard.png` — 实时信号面板（仅 --dashboard 模式）

### 3. RS敏感性分析

通过 `--sensitivity` 标志启用。系统自动以默认RS值（70）为基准，上下各测试多个档位，生成对比表格。这是量化"信号质量 vs 交易频率"权衡的关键工具。详见 [[rs-sensitivity-analysis]]。

### 4. 信号面板功能（--dashboard）

生成当前市场的实时快照，包含：K线图与信号标记、信号提醒卡片（入场/止损/目标价）、入场前检查清单、80/20规则评估、检测到的形态、波幅状态、历史回测统计摘要。

### 5. Python API 集成

支持通过 `BTCPriceActionBacktest` 类编程调用，可将回测嵌入自动化流程：

```python
from btc_price_action_backtest import BTCPriceActionBacktest
bt = BTCPriceActionBacktest(symbol="BTCUSDT", interval="5m", initial_equity=10000, min_rs=70)
bt.load_data(days=60)
bt.run_backtest()
print(f"胜率: {bt.stats['win_rate']*100:.1f}%")
bt.generate_visualization(output_dir="my_results")
```

## 提取出的新概念

- [[rs-sensitivity-analysis]] — RS敏感性分析：系统化测试不同RS阈值以优化策略表现的方法论
- [[signal-dashboard]] — 信号面板：实时市场诊断快照，将7大维度价格行为分析合成为单一决策界面（第2次 ingest 补充提取）

## 与现有知识的冲突

- 无显著冲突。本指南是操作手册，不引入新的理论观点。其7大信号体系与 [[brooks-signal-catalog]] 一致，RS评分系统与 [[README-summary]] 一致。
- 指南推荐的默认参数（RS≥70、风险1%、20根K线时间止损）与 MES 策略完全相同，验证了 Brooks 策略框架的跨市场参数一致性。
- Binance API 单次1000条K线的限制（约83小时5分钟数据）是实际操作中需要注意的约束，长周期回测需分多次请求或在 [[integration-summary-20260306]] 中提到的本地CSV方案。
