# 信号注册表与措辞约束

> 来源：`src/signal_registry.py`（SIGNAL_DEFINITION_REGISTRY）、`src/report_signal_filter.py`

## 注册表结构（Focus v1 后：19 键）

每个信号条目包含：

```python
"signal_type":        内部键名
"display_name_cn":    报告显示名
"pa_family":          家族分类
"direction":          long / short / derived / both
"maturity":           TRADE_READY | STRUCTURE_READY | CONTEXT_FACTOR | NOT_IMPLEMENTED | disabled
"strict_match":       是否 strict bar-counting 血统
"is_proxy":           是否代理实现
"enabled":            是否进入生产信号面（由 focus_config 裁决）
"core_definition_cn": KB 确认的核心定义
"trigger_rule / entry_rule / stop_rule":  三规则
"invalid_conditions": 失效条件列表
"report_allowed_wording / report_forbidden_wording":  报告措辞白名单/黑名单
```

## Focus v1 信号面（6 键 / 5 结构）

| 键 | 家族 | 概率定位 | 关键规则 |
|----|------|---------|---------|
| H2 / L2 | swing_proxy（严格血统） | 高胜率延续 | HL2>HL1，突破信号棒极值触发 |
| breakout | breakout（v1新增） | 确认后≥60% | 收破20棒前高+收在棒体30%极端+区间≥1.2ATR |
| wedge | reversal | 40%换≥2:1 | 三推（不必收敛），TBTL最小目标 |
| final_flag | trend_exhaustion | 40%换≥2:1 | 延续模式开始→反转结束，磁力位附近 |
| tr_fade | trading_range_strategy | 区间内高胜率 | 仅range regime+宽度≥2.5ATR |

## 术语确权（防止 LLM 冒用 Brooks 术语）

18→19 个键里，只有经过知识库确认定义的才能标 strict：

- **strict**：H1/H2/L1/L2（bar-counting 硬触发）
- **降级为 CONTEXT_FACTOR**：eighty_twenty（80/20 是区间语境因子，不是独立信号）
- **定位为 measurement_tool**：measured_move（测量工具，算目标用）
- **形态表达归并**：double_bottom/top → H2/L2 的形态表达（且已被回测证伪，disabled）
- **PARTIAL_MATCH**：wedge/climax（部分匹配，需 qualification 补充）

## 措辞约束示例

- tr_fade：允许"交易区间反转策略（原tr_fade）"；禁止将其称为孤立形态信号
- breakout：允许"精选突破（精选标准：收在前高之上+区间扩张+收在极端）"；**禁止"把所有突破都当信号（75%突破会失败，仅做精选）"**
- L2 strict：允许"严格 Brooks L2 第二次向下尝试成立"；禁止"把 lower-high proxy 称为 Brooks L2"

## 报告路由（report_signal_filter.py）

```
brooks_production    → 主报告（Focus v1 五结构）
legacy_proxy         → 附录（H1/L1 等降级代理）
strict_research_only → 研究区（未实现 strict 键）
not_entry_signal     → 不作为信号出现（形态/语境/目标工具）
```
