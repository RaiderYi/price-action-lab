# PA 形态 Al Brooks 定义校验参考

## 元信息
- 作者：huangzongprice（GitHub）
- 日期：未标注（伴随 `btc_price_action_live.py` 代码仓库）
- 原始位置：`raw/articles/huangzongprice/PA_BROOKS_VERIFICATION.md`
- 关联代码：`btc_price_action_live.py`（`VALID_PA_SIGNAL_VALUES` 白名单）
- 用途：开发阶段校验文档，确保代码实现与 Brooks 原著定义一致

## 一句话摘要
将 `btc_price_action_live.py` 中 16 种 Brooks 信号（8 多头 + 8 空头）的检测逻辑逐条对照 Brooks 原著定义，提供调试 API 和前端校验机制。

## 核心论点

### 1. 信号类型白名单（16 种）
代码只输出 `VALID_PA_SIGNAL_VALUES` 白名单内的信号，不含 Brooks 原著中 High 4 / Low 4 / Trouble Top 等未实现的类型。

**多头信号（8 种）：**
| 信号 | 核心规则 | 函数 |
|------|---------|------|
| `bull_h1` | 回调中第一根高点 > 前高点 | `_try_h1_bull` |
| `bull_h2` | 两腿回调后更高低点，收盘在棒线上半部 | `_try_h2_bull` |
| `bull_h3_wedge` | 三推下跌楔形底，信号K近EMA | `_try_h3_wedge_bull` |
| `bull_wedge_flag` | 旗杆+楔形收敛回调+近EMA | `_try_wedge_bull_flag` |
| `bull_btc` | AIL确认，连续强阳线，收盘近高点 | `_try_btc` |
| `bull_tr_fade` | TR底部第3–4次测试反转 | `_try_tr_fade_long` |
| `bull_post_climax` | 空头高潮后反转，TBTL完成 | `_try_post_bear_climax_long` |
| `bull_double_bottom` | 两底价差≤0.5 ATR，H2变体 | `_try_double_bottom_bull` |

**空头信号（8 种）：**
| 信号 | 核心规则 | 函数 |
|------|---------|------|
| `bear_l1` | 反弹中第一根低点 < 前低点 | `_try_l1_bear` |
| `bear_l2` | 两腿反弹后更低高点，收盘在棒线下半部 | `_try_l2_bear` |
| `bear_l3_wedge` | 三推上涨楔形顶，信号K近EMA | `_try_l3_wedge_bear` |
| `bear_wedge_flag` | 旗杆+楔形收敛反弹+近EMA | `_try_wedge_bear_flag` |
| `bear_stc` | AIS确认，连续强阴线，收盘近低点 | `_try_stc` |
| `bear_tr_fade` | TR顶部第3–4次测试反转 | `_try_tr_fade_short` |
| `bear_post_climax` | 多头高潮后反转，TBTL完成 | `_try_post_bull_climax_short` |
| `bear_double_top` | 两顶价差≤0.5 ATR，L2变体 | `_try_double_top_bear` |

### 2. 关键过滤规则（跨信号共享）

| 规则 | 适用范围 | 阈值 |
|------|---------|------|
| 回调/反弹深度 | H1/L1 | 0.3~5 ATR |
| 回调/反弹深度 | H2/L2 | 0.5~5 ATR |
| 双顶/双底价差 | Double | ≤0.5 ATR |
| 收盘位置（上半部） | H2/BTC/双底 | close > bar_mid |
| 收盘位置（下半部） | L2/STC/双顶 | close < bar_mid |
| 高潮K实体 | Post Climax | >1.8 ATR |
| TR区间K线数 | TR Fade | ≥8 |
| TR边界测试次数 | TR Fade | ≥2 |
| TBTL完成 | Post Climax | classify层过滤 |

### 3. 调试与校验基础设施
- **API**：`GET /api/pa_signal_types` 返回信号白名单及描述
- **前端**：未知 `signal_type` 输出 `[PA校验] 未知信号类型` 控制台警告
- **历史扫描**：只输出白名单内的信号，屏蔽未实现类型

## 提取出的新概念
以下概念在当前 Wiki 中尚不存在，已同步创建对应概念页：

- [[brooks-signal-catalog]] — 布鲁克斯16种信号类型系统全览
- [[bar-close-position]] — 收盘位置规则（上半部/下半部过滤）
- [[tbtl]] — TBTL十棒两腿确认机制
- [[atr-scaling]] — ATR归一化与深度/价差过滤
- [[trading-range-quality]] — 交易区间质量评定标准

## 与现有知识的冲突
- 本文档明确指出代码**未实现** Brooks 原著中的 High 4 / Low 4 / Trouble Top 等信号类型，需在 [[brooks-signal-catalog]] 中标注为"未代码化"
- 该验证文档是开发阶段的内部对照工具，不具备交易教学价值——其"定义"来自代码实现意图，可能已包含工程技术性简化
