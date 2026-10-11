# baostock

## 身份/定义
baostock 是一个免费、开源的 A 股数据 Python 库（`pip install baostock`），提供 1990 年至今的全量历史行情数据，支持多周期、自动复权和交易日历。

## 核心贡献/观点
- 完全免费的 A 股数据源，无请求频率限制
- 日线数据覆盖 1990 年至今，分钟线（5m/15m/30m/60m）覆盖最近 2-3 年
- 自动处理 A 股交易日历（节假日、非交易日自动跳过）
- 支持三种复权模式：前复权（`adjustflag='2'`）、后复权（`adjustflag='3'`）、不复权（`adjustflag='1'`）
- 国内直连（`www.baostock.com`），无需翻墙——相比 Binance API 的显著部署优势
- 在 huangzongprice 项目中作为 A 股数据适配层的**唯一数据源**

## 数据字段
```python
{
    'datetime': '2024-01-15 14:30:00',  # 时间
    'open': 1680.00,                     # 开盘价
    'high': 1695.00,                     # 最高价
    'low': 1675.00,                      # 最低价
    'close': 1688.00,                    # 收盘价
    'volume': 15234,                     # 成交量（手）
    'amount': 2567890000.00              # 成交额（元）
}
```

## 代表作品/相关页面
- [[article-ashare-guide]]（huangzongprice 项目 A 股使用指南）
- [[integration-summary-20260306]]（四版本系统架构中的 A 股数据源）
- [[multi-market-architecture]]（双市场架构中的数据适配层）

## 与其他实体的关系
- **Binance API**：互补——baostock 覆盖 A 股，Binance 覆盖加密货币，两者通过 [[multi-market-architecture]] 统一
- **TradingView**：替代——baostock 提供原始数据，TradingView Pine 指标提供可视化分析
- **[[al-brooks]]**：baostock 本身与 Brooks 方法论无关，在 huangzongprice 项目中作为 Brooks A 股策略的数据基础设施
