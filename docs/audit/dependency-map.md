# S0-02 依赖/入口/缺文件地图

编制：2026-10-12（实施 AI 按 S0-02 执行）。方法：AST 扫描全部 src/ 与 tests/
的 import 语句，逐模块解析可得性（仓库内 / 标准库 / site-packages / 缺失）。
复现命令：`python .audit/scan_missing_deps.py`。

## 1. 资产清单（提交 02154d7）

- src/ 核心模块：11 个 py 文件（全部自有，无外部私有依赖）
- scripts/：backtest_focus_random5.py（legacy 回测入口）
- tests/：62 个测试文件
- data/reviews/：1 个冻结结果 JSON
- knowledge/：1029 个 Markdown（概念页 241，任务书口径）
- 行情 CSV：**不在仓库**（.gitignore 挡 *.csv；D30 目录路径硬编码在脚本中）

## 2. src/ 模块分类（11/11 自有）

| 模块 | 状态 | 外部私有依赖 |
|---|---|---|
| bar_counting_detector.py | 自有核心 | 无 |
| focus_config.py | 自有核心 | 无 |
| market_analyzer.py | 自有核心 | kb_rules（可选，已改 capability 门控） |
| signal_predictor.py | 自有核心 | 无 |
| signal_registry.py | 自有核心 | 无 |
| strict_breakout_strength.py | 自有核心 | 无 |
| strict_pa_detector.py | 自有核心 | 无 |
| strict_pa_qualification.py | 自有核心 | 无 |
| strict_pa_actionability.py | 自有核心 | 无 |
| system_price_builder.py | 自有核心 | 无 |
| report_signal_filter.py | 自有核心 | brooks_ontology_registry（必需，缺失时报明确错误 F12） |

新增（S0）：pal_cli.py（CLI 入口）、pal_capabilities.py（能力注册表）。

## 3. 缺失外部模块与测试归类（54→53 移入 tests/integration/）

核心结论：**62 个测试中 53 个依赖仓库中不存在的模块**，属于仓外集成测试，
已移至 tests/integration/（未删除、未 skip）。核心套件 192 项可独立运行。

缺失模块频次（按被依赖的测试数）：

| 缺失模块 | 依赖测试数 | 判定 |
|---|---|---|
| rule_guardrail | 22 | 外部私有（不擅自恢复，S1 起重建自有版本） |
| kb_rules | 9 | 外部私有（market_analyzer 已门控降级） |
| system_structure_builder | 6 | 外部私有（S4 pricing 重建） |
| signal_maturity | 5 | 外部私有（S1-02 registry 重建） |
| brooks_ontology_registry | 2 | 外部私有（F12 已显式报错） |
| strict_paper_tracker / strict_paper_price_model | 3 | 外部私有（S5 ledger 重建） |
| evidence_verifier | 3 | 外部私有（S1-08 决策快照重建） |
| candidate_pool | 2 | 外部私有（S3 selection 重建） |
| signal_fingerprint | 2 | 外部私有（S1-07 identity 重建） |
| wiki_assembler | 3 | 外部私有（knowledge 重建） |
| proxy_context_gate / proxy_paper_simulator | 2 | 外部私有 |
| signal_performance_report / signal_upgrade_backlog | 2 | 外部私有 |
| tr_fade_replay / wedge_replay / report_fact_renderer / strategy_generator / run_strategy / market_config | 各1 | 外部私有 |
| scripts/run_strict_shadow.py（文件缺失） | 1 | 仓外脚本（test_strict_shadow_output） |

处置原则（任务书 §2.1）：不虚构私有源码、不将缺口描述为已修复、不删除测试。
后续阶段按目标架构在 src/pal/ 下重建自有实现，重建后逐批把对应 integration
测试迁回或重写。

## 4. 运行入口地图

| 入口 | 状态 | 说明 |
|---|---|---|
| `pal --help` / `pal doctor` | 新增（S0-03） | 安装后任意目录可用；报告核心模块与能力缺口 |
| `python -m pytest tests` | 核心套件 | 192 passed；integration 默认排除 |
| `python -m pytest tests/integration --continue-on-collection-errors` | 集成套件 | 需私有模块，当前环境必然 error（预期） |
| `python scripts/backtest_focus_random5.py` | legacy 入口 | 需 D30 行情 CSV（不在仓库）；无 CSV 时报错退出 |

## 5. 环境锁定现状

- 开发环境：Python 3.14.0（Windows）、pytest 9.0.3、pandas/numpy 已装
- pyproject.toml 已声明 dependencies（pandas>=1.5, numpy>=1.24）与 dev extra（pytest）
- 完整锁文件（uv.lock / requirements.txt 带 hash）待首个稳定批次后生成，
  此时先不锁中间态版本
