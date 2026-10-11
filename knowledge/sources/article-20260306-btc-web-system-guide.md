# BTC Price Action Web System 使用指南

## 元信息
- 作者：huangzongprice
- 日期：2026-03-06（v1.0.0 初始发布 + v1.1.0 当日升级）
- 原始位置：`raw/articles/huangzongprice/WEB_SYSTEM_GUIDE.md`
- 标的：BTC/USDT
- 技术栈：Flask + Flask-SocketIO + TradingView Lightweight Charts

## 一句话摘要
`app.py` 是 huangzongprice 价格行为策略的浏览器端实时交易仪表板，v1.1.0 升级至 TradingView 专业 K 线图表，提供历史回测可视化、交易标记叠加和 WebSocket 实时推送。

## 核心论点

### 1. 双模式互补架构
本指南覆盖的 `app.py`（Web 模式）与 [[article-huangzongprice-live-system-guide]] 覆盖的 `btc_price_action_live.py`（CLI 模式）形成双通道：
- CLI 模式：轻量、无依赖、适合本地交易员
- Web 模式：图形化、远程可访问、适合团队协作和复盘展示

### 2. v1.1.0 核心升级：TradingView 专业图表
| 维度 | v1.0.0（Chart.js） | v1.1.0（TradingView） |
|------|-------------------|----------------------|
| K线渲染 | 基础 OHLC | 专业级，高性能 |
| 数据容量 | 有限 | 大量 K 线流畅渲染 |
| 交易标记 | 无 | 绿色买入箭头 / 红色卖出箭头 / 黄色平仓标记 |
| 交互 | 基础缩放 | 鼠标滚轮缩放、拖拽平移、十字光标 |
| 时间轴 | 固定 | 可缩放时间轴 |

### 3. REST API 全景（11 端点）
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/status` | GET | 系统运行状态 |
| `/api/klines` | GET | K 线数据（支持 limit 参数） |
| `/api/trade_markers` | GET | 交易标记点数据 |
| `/api/config` | GET/POST | 配置读写 |
| `/api/signal_history` | GET | 历史信号记录 |
| `/api/backtest_stats` | GET | 回测统计（总交易/胜率/总R/夏普） |
| `/api/trades` | GET | 完整交易明细 |
| `/api/start` | POST | 启动系统 |
| `/api/stop` | POST | 停止系统 |
| `/api/update_now` | POST | 手动触发即时更新 |

### 4. WebSocket 事件协议
| 事件 | 方向 | 数据载荷 |
|------|------|---------|
| `connected` | 服务端→客户端 | app_name, version, state, klines, markers |
| `market_update` | 服务端→客户端 | price, regime, signal, klines |
| `new_signal` | 服务端→客户端 | direction, entry_price, stop_loss, target |
| `log` | 服务端→客户端 | time, level, message |

### 5. 与缠论系统的对比
| 特性 | v5 缠论系统 | 本系统（价格行为） |
|------|-----------|------------------|
| 分析理论 | 缠论（笔买卖点） | Al Brooks 价格行为 |
| 入场信号 | 笔买卖点 | 7 大价格行为模式 + RS 评分过滤 |
| K线图表 | ✅ 有 | ✅ **TradingView（专业级）** |
| 交易标记 | ✅ 有 | ✅ **有（买入/卖出/平仓三种标记）** |
| 机器学习 | XGBoost | 可扩展 |
| 部署复杂度 | 高 | 低 |

## 提取出的新概念

本文聚焦于 Web 系统的交付层（UI、API、部署），未引入全新价格行为理论概念。以下为与现有概念的关系映射：

- **已有概念覆盖**：
  - [[live-trading-monitor]] 已覆盖 CLI + Web 双模式架构，本文是其 Web 模式 v1.1.0 的详细操作手册
  - [[trade-management-system]] 的止损/BE/追踪逻辑通过 API 和信号面板可视化呈现
  - [[rs-scoring]] 的过滤结果通过信号卡片和 K 线标记在界面上展示
- **新增系统层面知识点**（记录于 live-trading-monitor 页面补充）：
  - TradingView Lightweight Charts 替代 Chart.js 的专业图表升级
  - 11 个 REST API 端点的完整规范
  - WebSocket 4 事件协议的详细定义
  - Gunicorn + Docker 生产部署方案

## 与现有知识的冲突

- **无冲突**：本文是 `integration-summary-20260306` 和 `live-trading-monitor` 在 Web 层面的详细展开，三者形成「架构全景 → 概念定义 → 操作手册」的三层递进关系
- **Chart.js → TradingView 迁移**：`live-trading-monitor` 概念页原记录 Web 模式使用 Chart.js，本文揭示 v1.1.0 已升级为 TradingView——需同步更新概念页以避免信息过时
