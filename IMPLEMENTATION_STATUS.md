# IMPLEMENTATION_STATUS.md

依据：《price-action-lab_整合重构完整TODO.md》（任务书）§9 主指令。
基线提交：`02154d7`（审阅提交 = 本地 HEAD，无差异）。
状态：TODO / DOING / BLOCKED / DONE。

## 批次记录

### 第二轮复审修正批次（2026-10-12，审阅提交 b412e1a → 本轮）

| 批次 | R 编号 | 状态 | 验收证据 |
|---|---|---|---|
| A 状态纠偏 | R12 | DONE | docs/audit/status-correction-round2.md（逐任务 PARTIAL/BLOCKED 纠偏；三处语义错位映射作废） |
| B 数据/资金不变量 | R03 | DONE | tests/pal/test_round2_batch_b.py 4项：单根上午bar→非final日线；多证券过滤 |
| B | R06 | DONE | 同上 5项：CANCELLED/REJECTED/INTENT fill 拒绝；fill_id 幂等；多partial |
| B | R07 | DONE | 同上 2项：9%已有→仅剩1%额度；在途占用 |
| B | R08 | DONE | 同上 4项+旧3项更新：缺CI→INCONCLUSIVE；回撤90%→FAIL；NaN→非PASS；G0必过 |
| B | R10(T+1) | DONE | 同上 1项：sellable_from≤当日→构造拒绝 |
| C 信号/定价语义 | R04 | DONE | tests/pal/test_round2_batch_c.py 2项：趋势门1.1生效；H递降拒绝 |
| C | R05 | DONE | 同上 3项：首棒突破无跟随；跟随仅后续bar；弱收盘非strong |
| C | R09 | DONE | 同上 2项：H2空间不足拒绝（不强抬2R）；final_flag方向自洽字段 |
| C | R10(其余) | DONE | 同上 3项：trailing pending→advance_bar；摆点延迟传播；MA60不足unknown |
| D 端到端 | R01/R02 | DONE | tests/pal/test_e2e_orchestrator.py 9项：完整链路（候选门/regime门/幂等/NAV序列/未来扰动不变/无成交路径/零量不成交） |

**本轮证据**：红→绿对照——批次B 16项反例、批次C 10项反例全部先复现后修复；
端到端 8 验收场景中 6 个直接测试覆盖（多票争资/持仓上限场景由 R07 修复+约束器测试承载）。
全套 **462 passed / 1 skipped**。

**批次 E/F（真实数据与研究验收）**：BLOCKED——外部依赖（行情供应商、
主数据、官方规则核验、私有包），登记于 docs/audit/data-capability-matrix.md。

### 批次 D（S6+S7+S8核心+完备性自查，2026-10-12）

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S6-01 | DONE | src/pal/portfolio/risk.py PortfolioConstraints | `pytest tests/pal/test_portfolio_risk.py -q` | 22 passed；风险预算+资金+单票三重上限；极窄止损10%封顶 |
| S6-02 | DONE | 同上 | 同上 | 总仓位80%/行业25%/最多10只闸；拒绝理由结构化 |
| S6-03 | DONE | 同上 gap_stress_loss | 同上 | 跳空超1R损失计算（T+1无法隔夜规避） |
| S6-04 | DONE | 同上 ExitPolicyEngine | 同上 | 固定优先级（结构失效>止损>移动>止盈>超时）；移动止损只上调 |
| S6-05 | DONE | 同上 | 同上 | 同票多来源一份净预算；默认不摊平 |
| S6-06 | DONE | 同上 CircuitBreaker | 同上 | 回撤10%/日亏2%/数据故障三重熔断；停开仓不停风险管理；人工覆盖独立标签 |
| S6-07 | DONE | 同上 capacity_report | 同上 | 参与率约束，不线性外推 |
| S6-08 | DONE | 同上 PaperDefaults | 同上 | 任务书默认参数全量代码化（100万/0.25%/10%/25%/80%/10只） |
| S7-01 | DONE | src/pal/research/framework.py, tests/pal/test_research_framework.py | `pytest tests/pal/test_research_framework.py -q` | 18 passed；预注册不完整→禁PASS；9变体注册制 |
| S7-02 | DONE | 同上 TimeSplit/purge | 同上 | 跨边界标签清除（12-25 > 12-22 被清） |
| S7-04 | DONE | 同上 metrics | 同上 | 收益差vs相对财富分立命名；IR零波动→None(NA)；R用初始风险 |
| S7-08 | DONE | 同上 release_gate | 同上 | PASS/FAIL/INCONCLUSIVE 分立；缺数据≠零收益 |
| S8-02 | DONE | src/pal/reporting/daily_plan.py, tests/pal/test_daily_plan.py | `pytest tests/pal/test_daily_plan.py -q` | 5 passed；四类目保留研究日志不裁剪；空计划=合法状态；JSON+MD 同源渲染 |

**完备性自查（用户要求，脚本可复跑）**：
`python .audit/scenario_coverage.py` → **任务书 §7 验收场景 27/27 全覆盖**。

### 完备性声明（80 任务真实状态，不虚报）

已完成（含部分/等外部输入）：S0 全8、S1 全8、S2 全8、S3 7/8（S3-03 BLOCKED
私有包）、S4 全8、S5 全8、S6 全8、S7 4/8（S7-03/05/06/07 需真实数据运行）、
S8 1/8（S8-02 核心；S8-01/03/04/05/06/07/08 部分由 CLI/报告/测试承载，
完整产品化待真实数据）。S9 未开始（前向运行阶段，任务书定位为"实证观察，
需数月"，依赖固定版本+真实数据）。

真实缺口（如实登记，非阻塞工程）：
1. 真实行情数据未接入——所有收益相关结论仍不可做（§5 红线）
2. MAIN_BOARD 费率标注 UNVERIFIED，正式使用前须按 S5-01 核验官方规则
3. 私有五模型包未取得（S3-03），provider 协议就绪
4. S9 前向运行/调度/对账未实施（需先有可运行的每日数据流）

### 批次 C（S5 全部，2026-10-12）：真实撮合与账户账本

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S5-01 | DONE | src/pal/execution/market_rules.py, tests/pal/test_execution_ledger.py | `pytest tests/pal/test_execution_ledger.py -q` | 版本化 MarketRuleSet（rules_version 显式，首版标注 UNVERIFIED 待官方核验）；RuleBook as-of 查询 |
| S5-02 | DONE | 同上 Order 状态机 | 同上 | INTENT→SUBMITTED→PARTIAL/FILLED/CANCELLED/REJECTED；超量成交拒绝；FILLED 终态 |
| S5-03 | DONE | src/pal/execution/fill_models.py | 同上 | 跳空止损按开盘成交（不填stop）；一字板不成交；同bar双触达保守取止损+路径不确定标记；参与率上限 |
| S5-04 | DONE | 同上 | 同上 | 涨跌停价计算；一字涨停买入拒；一字跌停卖出拒（风险延续） |
| S5-05 | DONE | src/pal/ledger/positions.py PositionBook | 同上 | lot 级 T+1：昨100+今100当日只可卖100；FIFO 扣减；清仓 key 不要求市价 |
| S5-06 | DONE | 同上 AccountLedger | 同上 | 手算案例逐项核对（100005买入/10989.5净卖出）；现金守恒审计通过；费用不双计 |
| S5-07 | DONE | src/pal/research/replay.py, tests/pal/test_replay.py | `pytest tests/pal/test_replay.py -q` | 末bar正常处理；期末持仓→open_eod_mark 估值（不进成交列表）；回放内 T+1/跳空遵守 |
| S5-08 | DONE | 同上 decompose_diff | 同上 | 4成分差异分解（rule_fix/signal_swap/pricing_model/costs），结构化输出不归因单一因素 |

**阶段出口核验（S5 全部 DONE）**：合成会计与成交边界案例全部一致 ✓；
真实行情结果可逐笔追到资金与订单（账本 movements 全留痕）✓。
30m OHLC 路径不可知部分显式假设（path_uncertain）✓。
全套测试 **383 passed / 0 failed**。收益结论等待真实数据+G关口（§5.5）。

### 批次 B3（S4 剩余，2026-10-12）：因果摆点、regime、统一引擎

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S4-01 | DONE | src/pal/context/swings.py, tests/pal/test_swings_regime.py | `pytest tests/pal/test_swings_regime.py -q` | 11 passed；右3棒确认前不可用；prefix_stability 前缀一致性性质测试通过（追加数据不改过去决策） |
| S4-02 | DONE | src/pal/context/regime.py | 同上 | unknown≠range 显式；RegimeLabelBook 切换需连续2次确认（滞后政策）；特征可审计 |
| S4-03 | DONE | src/pal/signals/engine.py strict_h2_verdict | `pytest tests/pal/test_engine_patterns.py -q` | 严格两腿+HL递进计数；单 HL 不计数（F02 验收）；接线 engine._eval_h2 |
| S4-04 | DONE | src/pal/signals/breakout.py | 同上 | F16 收敛：无突破位→none（禁大棒fallback）；大棒+越位+跟随基础→strong；统一入口 |
| S4-05 | DONE | src/pal/signals/patterns.py | 同上 | wedge 三推单调+幅度递减+间隔校验（F18）；final_flag 事件1本体检测（F04 拆分）；tr_fade 归一化位置（F19） |
| S4-06 | DONE | （B2 已交付 lifecycle.py） | - | 见批次 B2 |
| S4-07 | DONE | （B2 已交付 structure_prices.py） | - | 见批次 B2 |
| S4-08 | DONE | src/pal/signals/engine.py DecisionEngine | 同上 | evaluate(asof,...) 不读系统时钟；相同事实→相同决策（确定性测试）；输出仅 wait/reject（F06：无触发确认绝不 accept 成交） |

**阶段出口核验（S4 全部 DONE）**：第一版 H2 与 breakout 正确可测 ✓；
wedge/final_flag/tr_fade 保留研究能力（patterns.py，maturity=research）✓；
六个旧键≠六个同时上线策略（注册表分立承载）✓。
全套测试 **355 passed / 0 failed**（pal 层 127）。

### 批次 B2（S3 全部 + S4 核心，2026-10-12）：选股来源与统一结构引擎

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S3-01 | DONE | src/pal/selection/providers.py（Candidate/Provider协议） | `python -m pytest tests/pal/test_selection.py -q` | 21 passed；eligible<available 构造拒绝；缺提供者=disabled |
| S3-02 | DONE | 同上（STRUCTURED_V1 解析） | 同上 | 缺字段/时间倒置/非字符串symbol/标记无块 → BridgeFormatError；Markdown表格不解析 |
| S3-03 | BLOCKED | （需私有环境核对） | - | 私有包未取得（任务书 §10 登记）；协议+合成夹具已就绪 |
| S3-04 | DONE | providers.py（admission=全量准入语义） | 同上 | V1桥接保留全量 estimate（ev/wr 原样+uncalibrated_prior），未过滤池不冒充全池 |
| S3-05 | DONE | src/pal/selection/merge.py | 同上 | 5模型同票→1净持仓5来源；方向冲突记录不丢弃 |
| S3-06 | DONE | src/pal/selection/baselines.py | 同上 | 透明动量+流动性+趋势加分，参数预注册；数据不足/低流动性排除 |
| S3-07 | DONE | merge.py rank_by_score | 同上 | 分数分解components；同分代码序确定性 |
| S3-08 | DONE | merge.py CandidateLifecycle | 同上 | 盘后候选eligible_from次日；24h过期；未到期不可用 |
| S4-03 | PARTIAL | strict H2 全链（h2.py/engine.py） | - | S4-03 完整接线排 S4 剩余批次（wedge/tr_fade 研究实现+engine.evaluate 统一入口）；H2 定价/生命周期/注册血统已就绪 |
| S4-04 | DONE（阈值层） | S0-05 已修 F03；strength 统一留 S4 尾批 | tests/test_breakout_extremes.py | 6 passed（阈值）；F16 双实现收敛在 engine 批次处理 |
| S4-06 | DONE | src/pal/signals/lifecycle.py | tests/pal/test_lifecycle_pricing.py | RAW→QUALIFIED→ARMED→TRIGGERED 强制；终态不复活；同结构幂等；冷却；多空冲突显式 |
| S4-07 | DONE | src/pal/pricing/structure_prices.py | 同上 | H2/breakout/final_flag反转 结构定价；缺证据→InsufficientStructureEvidence（F05 禁兜底）；多头 stop<entry<target 硬校验 |

**阶段状态**：S3 出口达成（稳定输出"为什么选中、来自哪里、何时可用"✓，
私有包缺失只影响该 provider ✓）。S4 剩余：S4-01 因果摆点、S4-02 regime、
S4-03 strict 接线、S4-05 wedge/final_flag/tr_fade 检测、S4-04 F16 收敛、
S4-08 engine.evaluate 统一入口。全套测试 **327 passed / 0 failed**。

### 批次 B1（S2，2026-10-12）：时点正确的市场数据层

| ID | 状态 | 变更文件 | 验收命令 | 实际结果 |
|---|---|---|---|---|
| S2-01 | DONE | docs/audit/data-capability-matrix.md | 人工核对 | 能力矩阵+缺口清单；如实声明"仓库不持有任何可复现原始行情" |
| S2-02 | DONE | src/pal/data/security_master.py, tests/pal/test_security_bars.py | `python -m pytest tests/pal/test_security_bars.py -q` | 12 passed；688120=华海清科 名称回归；as-of 股票池排除未上市 |
| S2-03 | DONE | src/pal/data/calendar.py, tests/pal/test_calendar.py | `python -m pytest tests/pal/test_calendar.py -q` | 11 passed；8×30m网格不跨午休；15:00收盘可用时刻 |
| S2-04 | DONE | src/pal/data/quality.py（并入 test_data_quality_snapshot.py） | 同上 | ZERO_VOLUME/ABNORMAL_JUMP 标记；双源分歧>容差抛错不静默拼接 |
| S2-05 | DONE | src/pal/data/adjustments.py | 同上 | raw/research 双坐标系+roundtrip；分红送转持仓变换 |
| S2-06 | DONE | src/pal/data/bars.py | 同上 | available_at<bar_end 构造拒绝（F17）；as-of 视图排除未完成bar；供应商延迟顺延可见性 |
| S2-07 | DONE | src/pal/data/snapshots.py | 同上 | 内容寻址 snapshot_id（时间无关）；文件篡改检测 |
| S2-08 | DONE | src/pal/data/health.py | 同上 | 缺最终bar/源错误→DataStaleError 只锁新开仓 |

**阶段出口核验**：每条信息能回答"什么时候发生、什么时候系统能知道"
（available_at 全链强制 ✓）；没有数据的能力明确不可用（能力矩阵如实
登记 ✓）。全套测试 **287 passed / 0 failed**。
真实数据接入是外部依赖（S2-01 已列决策请求），不阻断后续 S3/S4
工程（合成夹具可跑，收益结论等真实数据——任务书 §5 红线不变）。

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
