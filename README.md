# Price Action Lab — Al Brooks 价格行为交易系统

> A股 30 分钟 · 双核四结构 + 区间开关 · 用可审计的数学层替代 LLM 直觉层

一个基于 Al Brooks 价格行为学（Price Action）的交易研究项目。
核心思路：**把 Brooks 的 10 大交易形态收敛为 5 个结构**，用严格的 bar-counting → qualification → actionability 三层架构保证信号可审计，用独立 paper mode / 回测验证是否真的有超额收益。

## ⚠️ 当前结论（诚实声明）

**截至 2026-10，本系统未证明存在超额收益。** 随机 5 股 30m walk-forward 回测（34 笔交易）：

- 平均超额收益 **-0.87%**（5 只中 3 只跑输买入持有）
- 信号分层：H2 主力信号 39% 胜率，强趋势股有效、震荡股反复止损
- 结论：**管道可运行、架构可审计，但策略设计层面存在问题**——趋势信号在震荡环境被反复止损，regime 识别是下一个关键改进点

本项目保留全部证据链（含负面结果），供后续迭代。

## 项目结构

```
price-action-lab/
├── README.md                  # 本文件
├── docs/
│   ├── methodology/           # 方法论：Brooks PA 体系整理
│   │   ├── 10-best-patterns.md        # 10 大形态精要（含概率数据）
│   │   ├── tbtl-and-probability.md    # TBTL 铁律与概率-盈亏比权衡
│   │   └── bar-counting.md            # H1/H2/L1/L2 严格计数规则
│   ├── architecture/          # 信号架构
│   │   ├── three-layer.md             # 三层架构（bar-counting→qualification→actionability）
│   │   ├── focus-v1.md                # Focus v1：双核四结构收敛决策
│   │   └── signal-registry.md         # 信号注册表与措辞约束
│   └── backtest-evidence/     # 回测证据
│       └── random5-walkforward.md     # 随机5股回测报告（含负面结果）
├── knowledge/                 # Brooks Wiki 知识库（241 概念页 + 来源文献）
│   ├── concepts/              # 概念页（h2-l2-signal, wedge, final-flag...）
│   ├── sources/               # 来源文献（书籍/文章 ingest 摘要）
│   └── overviews/             # 方法论总览
├── src/                       # 核心代码
│   ├── focus_config.py        # 【单一事实源】生产信号面 + 过滤器阈值
│   ├── signal_registry.py     # 信号注册表（定义/规则/措辞约束）
│   ├── bar_counting_detector.py   # 严格 bar counting（零生产依赖）
│   ├── signal_predictor.py    # Focus v1 信号预测器
│   ├── strict_pa_detector.py  # Strict PA 检测器
│   ├── strict_pa_qualification.py # 资质审核层
│   ├── strict_pa_actionability.py # 可执行性层
│   ┌── market_analyzer.py     # 市场结构分析
├── scripts/                   # 回测与扫描脚本
│   └── backtest_focus_random5.py    # 随机5股 walk-forward 回测
├── tests/                     # 测试套件（889 通过）
└── data/reviews/              # 设计文档与回测 JSON 证据
```

## 快速开始

```bash
# 回归测试
python -m pytest tests/ -q

# 随机 5 股回测（需要 data/market_data/30m/*.csv）
python scripts/backtest_focus_random5.py

# 信号面自检
python -c "from src.focus_config import LIVE_SIGNALS; print(sorted(LIVE_SIGNALS))"
```

## 五结构信号面（Focus v1）

| 核 | 结构 | 概率定位 | 入场逻辑 |
|----|------|---------|---------|
| 廔续核 | **H2/L2** | 高胜率延续 | 回调后第二信号棒，顺势 |
| 廔续核 | **breakout** | 确认后≥60% | 收破前高+收在极端+区间扩张≥1.2ATR（精选标准） |
| 反转核 | **wedge** | 40%胜率换≥2:1 | 三推至通道线，TBTL 最小目标 |
| 反转核 | **final_flag** | 40%胜率换≥2:1 | 趋势末端旗形，TBTL 最小目标 |
| 区间核(开关) | **tr_fade** | 区间内高胜率 | 仅 range regime 且宽度≥2.5ATR |

降级处置：H1/L1（首次回调概率低）、climax_reversal（与反转核重叠）、measured_move/MTR/Magnets（工具层，只算目标价）、double_top/bottom（回测证伪：13/13 亏损）、开盘反转（A股 T+1 不适配）。

## 三层架构

```
raw K线
  → bar-counting      纯数学计数（H1/H2/L1/L2），零生产依赖
  → qualification     资质审核：方向互斥、回调≥0.3ATR、区间中段降级、doji 扣分
  → actionability     9 维优先级打分；transition 基调宁可不出信号
```

设计原则：**LLM 表达市场判断，系统事实决定操作层级**。TRADE_READY=0 时报告禁止无条件动作指令；LLM 伪造结构点偏差>30% 置零；entry/stop/TP 由系统价格层计算，LLM 不再是价格源。

## 证据链

| 证据 | 位置 | 结果 |
|------|------|------|
| 随机5股回测 | `docs/backtest-evidence/random5-walkforward.md` | 无超额收益（-0.87%），H2 强趋势股有效/震荡股亏损 |
| double_top/bottom 证伪 | `docs/backtest-evidence/` | 13/13 亏损 -10.4R，已从信号面移除 |
| 信号面收敛决策 | `docs/architecture/focus-v1.md` | 11 live → 6 键/5 结构 |

## License

MIT
