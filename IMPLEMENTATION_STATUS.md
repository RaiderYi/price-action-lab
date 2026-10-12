# IMPLEMENTATION_STATUS.md

依据：《price-action-lab_整合重构完整TODO.md》（任务书）§9 主指令。
基线提交：`02154d7`（审阅提交 = 本地 HEAD，无差异）。
状态：TODO / DOING / BLOCKED / DONE。

## 批次记录

### 批次 A2（S1，2026-10-12）：统一领域对象、规则与配置

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S1-01 | DONE | src/pal/domain/models.py, schemas/instrument_id.schema.json, tests/test_domain_models.py | `python -m pytest tests/test_domain_models.py -q` | 19 passed；方向三层分立/非法值构造时拒绝 |
| S1-02 | DONE | src/pal/signals/registry.py, tests/pal/test_signals_registry.py | `python -m pytest tests/pal/test_signals_registry.py -q` | 10 passed；唯一注册表 19 组合（含旧表缺失的 breakout）；与 focus_config 一致性审计通过；unknown → KeyError |
| S1-03 | DONE | src/pal/signals/legacy/__init__.py, tests/pal/test_legacy_alias.py | `python -m pytest tests/pal/test_legacy_alias.py -q` | 5 passed；legacy H2 与 strict H2 setup_id 内容 hash 不同（统计天然分离，F01/F02 验收） |
| S1-04 | DONE | src/pal/config/versions.py, tests/pal/test_config_versions.py | `python -m pytest tests/pal/test_config_versions.py -q` | 7 passed；配置快照内容寻址 hash；运行期漂移 → ConfigDriftError |
| S1-05 | DONE | knowledge/rule_cards/（3卡+INDEX） | 人工审核 + 数学复算 | H2计数/FinalFlag语义/概率表数学错误三卡AUDITED；p=0.70→b≈0.4286 复算一致 |
| S1-06 | DONE | src/pal/domain/estimates.py | （与S1-07合并测试） | HeuristicScore/EmpiricalProbability/SourceEstimate 类型分立；未校准 p_win=None 由类型强制 |
| S1-07 | DONE | src/pal/domain/identity.py, tests/test_estimates_identity.py | `python -m pytest tests/test_estimates_identity.py -q` | 10 passed；10类前缀 ID 内容寻址幂等 |
| S1-08 | DONE | src/pal/domain/decision.py, tests/test_decision_snapshot.py | `python -m pytest tests/test_decision_snapshot.py -q` | 7 passed；15个登记 reason_code；accept 必须带证据；JSON 序列化确定性 |

**阶段出口核验**：没有两个模块分别定义"什么是 H2"（唯一注册表 + 一致性
审计 ✓）；配置变更可追踪（快照 hash + 漂移守卫 ✓）。
全套测试：**250 passed / 0 failed**（核心 228 + pal 层 22）。

### 批次 A1（S0，2026-10-12）：冻结证据、恢复可运行基础

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S0-01 | DONE | docs/audit/baseline.md, docs/audit/legacy_freeze_manifest.json, .audit/freeze_legacy.py | `python .audit/freeze_legacy.py` | 复算34笔/5股/均值-0.8681pp，与任务书一致；5产物SHA256冻结 |
| S0-02 | DONE | docs/audit/dependency-map.md, .audit/scan_missing_deps.py | `python .audit/scan_missing_deps.py` | 11源文件全自有；54/62测试依赖缺失模块，逐条归类（rule_guardrail 22次最高） |
| S0-03 | DONE | pyproject.toml, src/pal_cli.py, conftest.py | 仓库外 `pal --help && pal doctor` | exit=0；10核心模块ok；3可选模块显式absent |
| S0-04 | DONE | tests/integration/（53个文件移入）, pyproject addopts | `python -m pytest tests -q` | 192 passed / 0 failed / 0 errors；集成套件单列未删除 |
| S0-05 | DONE | tests/test_breakout_extremes.py, src/signal_predictor.py | `python -m pytest tests/test_breakout_extremes.py -q` | TDD红3→修F03（多头>=0.7/空头<=0.3）→6/6绿；全套192无回归 |
| S0-06 | DONE | src/pal_capabilities.py, src/market_analyzer.py, src/report_signal_filter.py, scripts/backtest_focus_random5.py | `python -m pytest tests -q`；`py_compile` 回测脚本 | 3处kb_rules静默fallback→capability门控；F12显式ReportFilterUnavailable；回测错误计数+错误率>5%→exit 2 |
| S0-07 | DONE | README.md, docs/backtest-evidence/random5-walkforward.md, docs/audit/errata.md | 人工核验 | 688120→华海清科[勘误-1]；"889通过"→真实口径；收益口径标注；3条勘误记录 |
| S0-08 | DONE | docs/audit/repo-boundary-check.md | `git status` 核验 | 分享包/CSV/logs均被ignore；knowledge/许可未声明→移交S1-05 |

**阶段出口核验**：干净环境可启动（pal doctor ✓）、核心测试可收集（192 ✓）、
错误可解释（capability/错误计数 ✓）、历史证据冻结（manifest ✓）。
缺少私有包不阻断公开核心开发（可选模块显式absent ✓）。

## 下一批任务

- 批次 A2（S1）：S1-01 领域模型 → S1-02 注册表统一 → S1-03 legacy/strict
  信号ID分离 → S1-04 配置版本化 → S1-05 知识规则卡 → S1-06 质量分/概率
  分离 → S1-07 统一ID → S1-08 决策快照
- S1 前置已满足（S0 全部 DONE）

## 全局剩余风险登记

1. 回测脚本错误率检查用 print 输出而非结构化日志——legacy 脚本定位如此，
   新引擎（S4-08/S5）不复用该模式
2. knowledge/ 1029 篇文档许可未声明（S1-05 处理）
3. 行情 CSV 不在仓库，legacy 复跑需用户提供 D30 数据（任务书 §10 已登记）
4. tests/integration 53 个文件在私有模块恢复前无法运行（预期行为）
