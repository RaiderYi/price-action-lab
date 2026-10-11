---
title: "实时交易监控系统"
phase: [trend, range, breakout]
signal_types: [pullback-entry]
tags: [web, app, websocket, btc, price]
difficulty: intermediate
related: [brooks-signal-catalog, rs-scoring, trade-management-system, multi-market-architecture, indicator-visual-optimization, signal-dashboard, integration-summary-20260306, article-huangzongprice-live-system-guide, article-20260306-btc-web-system-guide, README-summary]
char_count: 2615
---
# 实时交易监控系统

## 一句话定义
基于 Al Brooks 价格行为策略的实时行情监控系统，支持命令行交互模式与 WebSocket 浏览器推送双模式。Web 端 v1.1.0 升级为 TradingView Lightweight Charts 专业 K 线图表。

## 核心要点
- 两种运行模式：命令行实时轮询（`btc_price_action_live.py`）和 Web 浏览器界面（`app.py`）
- Web 版本使用 Flask + Flask-SocketIO 实现服务器推送，无需刷新页面
- 实时信号产生时控制台/界面醒目提醒，附带入场价、止损、目标价

## 双模式对比

| 特性 | 命令行模式 | Web 模式 |
|------|-----------|----------|
| 脚本 | `btc_price_action_live.py` | `app.py` |
| 技术栈 | Python CLI | Flask + SocketIO + TradingView Charts |
| 更新方式 | 定时轮询 | WebSocket 实时推送 |
| 可视化 | 静态 PNG 图片 | 动态 TradingView 专业 K 线 + 交易标记 |
| 远程访问 | 不支持 | 浏览器访问（http://localhost:5000） |
| 资源占用 | 低 | 中 |
| 适用场景 | 本地交易员 | 远程监控 / 团队协作 |
| 生产部署 | — | Gunicorn / Docker |

## 运行流程
```
1. 初始化 → 加载配置，获取历史数据
2. 历史回测 → 运行完整回测，生成基准报告
3. 实时监控 → 循环：等待→获取新数据→分析→生成信号面板
```

## Web 界面组成（v1.1.0）
- **当前行情面板**：实时价格、市场状态（趋势/区间/SPB）
- **最新信号面板**：入场方向、入场价、止损、目标、RS 评分
- **K 线走势图**：TradingView Lightweight Charts 专业 K 线，带绿色买入箭头 / 红色卖出箭头 / 黄色平仓标记叠加
- **回测统计**：历史交易笔数、胜率、总 R 收益、夏普比率
- **系统日志**：实时滚动日志，WebSocket 推送，信号产生时高亮
- **配置面板**：交易对、周期、更新间隔可调
- **REST API**：11 个端点（`/api/klines` `/api/trade_markers` `/api/backtest_stats` 等）供外部消费

## WebSocket 事件协议
| 事件 | 说明 |
|------|------|
| `connected` | 连接建立，推送初始数据（K 线 + 标记 + 状态） |
| `market_update` | 周期性市场数据更新（价格、趋势、信号） |
| `new_signal` | 新入场信号提醒（方向、价格、止损） |
| `log` | 服务器日志实时推送 |

## 与相关概念的关系
- [[brooks-signal-catalog]]：实时系统检测所有 16 种信号类型，白名单外信号输出 `[PA校验]` 警告
- [[rs-scoring]]：信号检测后经 RS 评分过滤，≥70% 才触发面板提醒——RS 评分是信号→提醒之间的质检关卡
- [[trade-management-system]]：实时信号面板直接显示入场价/止损/目标，由交易管理体系计算
- [[multi-market-architecture]]：Web 模式基于 BTC 版本（`app.py`），A股版本的 Web 界面由 `a_share_price_action.py --web` 提供
- [[indicator-visual-optimization]]：监控图表上的信号渲染应遵循三级分层体系——核心信号 large 常开，辅助信号 tiny 默认关
- [[signal-dashboard]]：监控系统解决"怎么推送"（技术架构），信号面板解决"推送什么"（认知架构）——信号面板定义了监控系统显示的7大诊断维度

## 实战应用
```bash
# 命令行实时监控（BTC 5m，每60秒更新）
python btc_price_action_live.py --symbol BTCUSDT --live-interval 60

# Web 界面
python app.py --port 5000
# 浏览器打开 http://localhost:5000

# A股 Web 界面
python a_share_price_action.py --code sh.600519 --web --port 5000
```

## 来源支撑
- [[integration-summary-20260306]]（INTEGRATION_SUMMARY.md — 实时系统和 Web 系统的完整说明）
- [[article-huangzongprice-live-system-guide]]（LIVE_SYSTEM_GUIDE.md — CLI 模式的详细操作手册）
- [[article-20260306-btc-web-system-guide]]（WEB_SYSTEM_GUIDE.md — Web 模式 v1.1.0 完整操作手册 + API/部署规范）
- [[README-summary]]（原策略的实时面板设计）

## 矛盾与待验证
- **WebSocket 生产部署**：v1.1.0 已文档化 Gunicorn + eventlet 方案（`gunicorn -w 4 -b 0.0.0.0:5000 app:app`）和 Docker 部署模板，原有「未说明生产部署方案」的疑虑已部分消除，但文档未提供 eventlet monkey-patching 的具体配置说明
- **信号频率 vs 更新间隔**：如果更新间隔（如 60 秒）大于信号产生频率，可能遗漏盘中信号——当前系统未有信号缓存/补推机制
