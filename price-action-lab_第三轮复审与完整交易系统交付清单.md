# price-action-lab 第三轮复审与完整交易系统交付清单

审阅日期：2026-10-12。审阅提交：`feb364158d612ee9ba2e26973f8d96bd5f15c5d7`，提交时间 2026-10-12 22:40:19 +08:00。对比基线：`b412e1a0113b9678898831e424a2cc472b558423`。

仓库：https://github.com/RaiderYi/price-action-lab

本次只读审查、运行测试及外置反例脚本，没有修改仓库业务代码。下述“复现”均指本地检出该提交后的实际执行结果；“代码检查”不等同于真实市场运行。未取得真实行情快照、私有五模型包、券商连接或线上运行记录，因而不对这些外部能力作已完成判断。

## 1. 结论：新增了编排雏形，尚未完成交易闭环

这一轮确有进展：增加 `SessionOrchestrator`，修补了若干领域不变量，并纠正部分原先过度乐观的任务状态。但以“完整交易系统”为目标，本次验收仍不通过。当前更准确的定位是：**有较完整的模块分层和单元测试，有单票编排原型，核心成交与退出语义仍存在阻断性错误。**

最关键的实际结果：

- 默认测试：**462 passed、1 skipped**；另有 **53 个 integration 测试文件被默认配置排除**，不包含在这个 skip 中。
- 唯一 skip 原因：`tests/pal/test_engine_patterns.py:177` 的夹具未构成 H2，摆点不足。
- 复用新增的 `test_full_fill_path` 夹具逐棒执行：**0 个事件、0 个决策、0 持仓、现金仍为 1,000,000**。该测试通过不能证明发生过交易。
- 实际引擎面对弱突破、空日线会生成 ARMED；重复提交同一根已处理 K 线后，会买入 **10,000 股**。
- 注入已成立计划测试执行边界：零成交量仍成交 **2,400 股**；另一个案例买入后，次日价格跌破止损仍无退出事件。

**工程正确、业务闭环、可持续运行、统计上有超额收益，是四个独立的验收层次。** 目前不能用单测数量替代其中任何后三项。完整系统也不等于必然赚钱；超额收益必须由冻结规则下的样本外证据支持。

## 2. 本轮修复应该如何认定

| 上轮事项 | 本轮真实进展 | 当前认定 |
|---|---|---|
| R01 决策到执行断开 | 新增会话编排，候选身份与时点检查接入 | 部分完成；同棒重放成交、regime 默认放行、family 错标仍在 |
| R02 回放绕过业务内核 | 新编排器开始调用风险、撮合、账本并记录 NAV | 部分完成；旧回放器未迁移，新编排缺退出绑定、完整订单记录和报告出口 |
| R03 日线聚合 | 排除异票、少于 8 根标 partial、传播最大 available_at | 部分完成；仍仅按条数认定完整，重复记录能伪造完整日线 |
| R04 H2 结构 | 增加至少两个 H、H 递进和趋势质量阈值 | 部分完成；尚未证明与原 bar-counting 三层定义一致，正例端到端验收缺失 |
| R05 突破跟随 | 新增显式 follow-bar 评估函数 | 部分完成；主引擎没有调用新函数，仍只检查 crossed_level |
| R06 撤单后成交 | apply_fill 增加终态保护与 fill_id 字段 | 原撤单复活反例已修；完整回报幂等与账本幂等未完成 |
| R07 单票额度 | 扣除已有持仓及传入的在途委托额度 | 组件修复；编排器没有传入真实在途订单，缺多票分配与组合快照 |
| R08 研究放行 | 新增 G0、CI、有限值检查，以及显式回撤比较 | 部分完成；不传 realized_max_drawdown 仍可 PASS |
| R09 定价 | H2 不再人为抬高目标到 2R；旗形止损方向修正 | 对应定价组件有进展；不是整条退出链验收 |
| R10 时序 | 拒绝当日可卖日期、trailing pending、摆点延迟、MA 不足处理 | 部分完成；真实日历、退出状态和事件推进尚未贯通 |
| R11 五模型接口 | 状态纠偏承认 BLOCKED | 诚实登记；真实协议兼容仍未交付 |
| R12 场景验收 | 新增 E2E 文件 | 未通过业务意义验收，存在恒真断言与无事件正例 |

本轮共变更 23 个文件，新增 1,498 行、删除 123 行。以上认定不否定已有组件价值，但不能把“新增函数”直接记作“系统可用”。

## 3. 阻断性发现与证据

### F01 / P0：买入后没有自动绑定退出计划

位置：`src/pal/pipeline/orchestrator.py`，`_try_fill`、`_manage_exit`、`bind_position_plan`。

买入完成只更新账本并从 armed 删除 setup。退出逻辑读取 `_active_stop/_active_target/_entry_date`，这些字段只能由 `bind_position_plan()` 设置，仓库内没有调用该方法的业务链。

复现：计划 entry=10、stop=9、target=12，成交 2,400 股；次日 O=8.5/H=8.8/L=8/C=8.2，返回事件 `[]`，持仓仍为 2,400 股，`_active_stop` 不存在。

影响：正常使用 on_bar 不能自动完成买入→止损退出。即使外部手工绑定，当前字段仍是会话级标量，不能安全管理多票或多个买入批次；退出使用 total_qty，在新旧批次可卖量不同的情况下会产生数量问题。

要求：成交事件必须原子地建立 position/lot 与对应退出策略；卖出走订单、成交、账本同一链；按可卖量管理，未卖部分继续承担风险。不能把“调用方记得手工补绑定”作为验收条件。

### F02 / P0：buy-stop 触发被当成限价买单撮合

位置：`orchestrator.py:_try_fill` 与 `execution/fill_models.py:match_buy_limit`。

ArmedSetup 明确写 entry 是 buy-stop；触发检查为 high>=entry，但随后提交 limit 单并调用 `min(open, entry)` 定价。

实际反例：

| 已有计划 | 行情 | 实际结果 | 问题 |
|---|---|---|---|
| 升破 10 买入 | O=9/H=10.5/L=8.9/C=10.2 | `FILL:2400@9` | 使用升破发生前的开盘价作为触发后的成交价 |
| 升破 10 买入 | O=11/H=11.5/L=10.8/C=11.2 | NO_FILL / price_not_touched | 实际执行成了等待回落到 10 的限价语义 |

要求：明确 stop-market、stop-limit、普通 limit 的不同语义及适用市场。研究撮合必须匹配真实订单意图，跳空、同棒路径、滑点和价格限制均需显式规则。若券商不支持原生条件单，应用层条件触发应转换为真实支持的订单，并记录延迟与限制。不得假设一个不被实际执行机制支持的订单行为。

### F03 / P0：零成交量和容量上限没有进入成交决策

位置：`execution/fill_models.py:match_buy_limit`、`participation_cap_qty` 与 `orchestrator.py:_try_fill`。

match_buy_limit 不检查 volume；参数 max_participation_pct 没有参与计算。独立的 participation_cap_qty 没有被编排器调用；FillResult.qty=0，而编排器直接按 rd.max_qty 全量成交。

复现：非一字棒 O=10.1/H=10.5/L=9.8/C=10.2、volume=0，仍成交 `2400@10`。

要求：成交数量来自撮合结果；零量为零成交；低量为部分成交或无成交，剩余委托占用资金；明确数据源成交量单位，不能默认“股/手”相同。停牌、价格限制与流动性信息进入同一检查链。

### F04 / P0：重复事件改变交易状态，并允许使用信号棒成交

位置：`orchestrator.py:on_bar`。

没有已消费事件键、没有单调时钟检查，也没有 `bar.available_at > setup.armed_at` 等时序约束。重复一根 K 线会增加 bars_since_armed 和 NAV 记录。

实际复现：

1. 使用合法交易时段的 22 根 K 线，真实 DecisionEngine 第一次调用生成弱突破 setup。
2. 原样再次调用同一根 K 线，返回 `FILL:setup_e2160d118331:10000@10`。
3. 一个尚未触发的计划，对同一根棒调用 8 次，即返回 EXPIRED，NAV 出现 8 条重复记录。

影响：数据重传能改变成交、持有期和策略收益；收盘才知道的信号可能成交在同一信号棒的早先价格。

要求：定义可重放事件协议、同一市场事件只推进一次；区分信号产生时间、订单激活时间、行情事件时间和数据接收时间。历史回放与 paper 使用一致约束；重复投递不增加订单/成交/费用/NAV/持有时钟。延迟行情不能替代当时可交易的实时事件。

### F05 / P0：主引擎仍绕过突破资格，regime 可默认绕过

位置：`signals/engine.py:_eval_breakout`、`signals/breakout.py:assess_with_follow_bars`、`orchestrator.py:on_bar`。

- 新跟随函数没有被主引擎使用，主引擎仍只要求 crossed_level。
- `regime_kind=None` 直接放行，未使用本次 `res.regime` 作强制资格裁决。
- 编排器创建所有 ArmedSetup 时把 family 写成 H2，包括 breakout。
- 风控及资格检查主要在新候选评估处，已有 armed 的触发在其之前执行，缺少成交时的统一再校验。

复现：空日线、没有传 regime、weak 突破，实际产生 ARMED；决策 detail strength=weak，保存的 family=H2。

要求：业务内核统一计算资格；缺必要上下文须明确拒绝或采用单独注册的策略模式，不能因可选参数省略而放行。突破棒、跟随棒、入场激活时间分离，family/source/evidence 保真。触发时重查数据健康、证券可交易性、风险与计划有效性。

### F06 / P0：完整成交测试实际没有成交

位置：`tests/pal/test_e2e_orchestrator.py`。

`test_full_fill_path` 只要求 NAV 非空、`len(decisions_log)>=0`、现金守恒等。真实复用夹具结果为：events=[]、decisions=0、qty=0、cash=1000000。

零量测试只在有 ARMED 时进入部分断言，没有强制构造“已触发但因零量被拒”的场景。报告测试从一个新建空编排器手工拼装 DailyPlanEntry，没有检验实际运行输出。原测试的未来扰动只改变从未传入运行的后段数据，不足以证明完整数据管道隔离正确。H2 正例还存在因结构不足而 skip。

要求：业务正例必须断言关键事件及数值，而非仅有接口和容器。测试能在删除成交绑定、关闭流动性门、绕过 regime 等错误实现下失败，才算有效保护。

### F07 / P1：日线完整性仍能被重复数据伪造

位置：`data/bars.py:resample_30m_to_daily`。

目前仅用 len(chunk)>=8 判断完整，没有在聚合入口强制周期、时间网格、唯一槽位和收盘覆盖。

复现：同一根 09:30–10:00 棒重复 8 次，输出 is_final=True、bar_end=10:00、volume=800000。

要求：依赖版本化交易日历，验证准确槽位集合及数据类型；重复、错周期、午休/非交易时段、缺末棒不能构成 final 日线。下游不得因为绕过另一个校验器而接收伪 final。

### F08 / P1：研究 gate 缺回撤仍可 PASS

位置：`research/framework.py:release_gate`。

在 G0=True、样本量达标、主指标及 CI 合格时：

- 不提供 realized_max_drawdown → PASS。
- result_metrics 中 max_drawdown=0.90、计划容忍 0.15，但省略独立参数 → PASS。
- 显式传 realized_max_drawdown=0.90 → FAIL。

要求：使用唯一的、经过 schema 验证的研究结果对象；所有必需指标缺失一律 INCONCLUSIVE，越界为 FAIL。禁止同一指标多处传值却只检查其中一处；计划本身的有限值、范围和样本量也需验证。G0 应引用本次 run 的验收产物，不能只有调用者传入一个 True。

### F09 / P1：模块仍未接成统一、可恢复、多票系统

这是代码路径检查结论：

- `pal_cli.py` 仍只提供 doctor；没有面向使用者的 scan/backtest/paper/report/reconcile 工作流。
- `research/replay.py:SinglePositionReplayer` 仍使用外部 entry_signal_idx、自带固定止盈止损和定仓，未复用 SessionOrchestrator，nav_series 仍没有写入路径。
- 编排器每次估值只传一只股票的价格；PositionBook 对其他持仓缺报价会抛错。注释提及的 PortfolioAllocator 未发现实现。
- CircuitBreaker、ExitPolicyEngine、participation_cap_qty 仍未被编排主链调用；最大持仓数、行业风险、数据故障等没有形成完整统一强制门。
- 成交订单只存在局部对象中，setup 随即被删除，没有持久化订单/成交事件链。退出直接调用 ledger.sell，未经过统一卖出订单及成交记录。
- T+1 使用自然日 +1，未调用已有 TradingCalendar.next_trading_day。
- daily_plan 是渲染函数，编排器没有调用；缺少从实际决策、订单、持仓和拒绝原因生成报告的入口。

完整交易系统需要“可运行且可恢复”的闭环；不能以这些函数分别存在作为完成证据。

### F10 / P1：真实输入与五模型协议仍是后续交付依赖

`selection/providers.py` 仍要求 symbol/direction/models/asof；仓内整合文档 §1.6 描述的是 rows 下的 code/bucket/sources 等。默认证券交易所仍为 SSE。此次没有获得真实私有样本，因此不能宣称已完成兼容。

应先交付公开基线选股器加真实行情的完整路径；私有五模型适配作为清晰可替换的 provider 接入，不让私有包缺席阻断其他可交付工作。真实来源和数据许可未确定的部分登记依赖，不用合成数据冒充市场验证。

## 4. 完整交易系统的目标边界

目标应明确为：**可追溯的数据 → 可交易股票池 → 候选筛选 → 策略决策 → 组合分配 → 委托与成交 → 持仓及退出 → 账本与净值 → 报告、监控、对账及恢复**，并在其上验证是否存在可实现的超额收益。

| 层次 | 必须具备的验收结果 | 当前状态 |
|---|---|---|
| 研究与决策内核 | 信号、价格、因果时序一致；真实正反例 | 部分具备 |
| 历史多票回放 | 单一业务内核、真实成本、逐日 NAV、可重现成交 | 未完成 |
| 日常选股分析 | 真实数据输入、scan 命令、候选及拒绝解释、计划报告 | 未完成 |
| 持续 paper 交易 | 自动生命周期、持久化、重启恢复、对账、异常停开仓 | 未完成 |
| 超额收益证据 | 冻结配置、多阶段样本外、成本压力、组合基准比较 | 未完成 |
| 实盘执行 | 同一内核、券商适配、真实回报对账、操作控制及小规模验收 | 尚未交付；本次未连接或下单 |

不要求先建设复杂微服务或漂亮界面。第一版可以是单进程应用、事务数据库、文件快照和命令行；关键是交易行为正确、状态可靠、每一步可解释。

## 5. 给执行 AI 的完整下一轮任务

所有任务默认未完成。建议按下列依赖顺序交付，不再一次性给全部条目勾 DONE。每个 PR/批次记录：基线提交、修改范围、精确运行命令、实际产物、失败场景、已知限制。

### 批次 A：先让单笔交易真正闭环

- [ ] **T01 / P0：建立不会空跑通过的验收夹具**
  - 范围：`tests/pal/test_e2e_orchestrator.py` 及相关 H2/突破测试。
  - 工作：分别构造真实引擎能产生 H2、突破信号的有效交易时段输入；生成手工可复算的事件和现金/股数/费用/NAV 预期。
  - 验收：Candidate→QUALIFIED→ARMED→TRIGGERED→Order→Fill→Position→次交易日 Exit→Ledger→Report 每环有确定断言；无信号不能通过有成交用例；有效 H2 正例不 skip。
  - 先保留当前失败结果，再由后续任务修复；不得降低断言迁就现实现。

- [ ] **T02 / P0：重写事件推进和幂等契约**
  - 范围：编排器、SetupBook、事件标识、订单与账本接口。
  - 工作：分开可重算的决策结果与事件提交；建立 event_id、event_time、received_at、effective_at；阻止重复推进与逆序污染；明确数据修订策略。
  - 验收：同棒 1 次或 100 次输入状态相同；断点恢复后重放尾部事件不多买、不多扣费、不多写 NAV；信号棒不可回填成交到信号生效之前。
  - 依赖：T01。

- [ ] **T03 / P0：统一订单意图与真实撮合语义**
  - 范围：订单模型、fill_models、编排器。
  - 工作：实现明确的 buy-stop/stop-limit/limit 路径、触发状态与成交状态；接入成交量参与率、可交易状态、价格限制、滑点和部分成交；执行价格变化后重算风险与可用现金。
  - 验收：F02/F03 全部反例失败变通过；同棒路径不确定须有可审计规则；部分成交留下剩余量和资金占用，撤单释放对应占用；拒单无账本变动。
  - 依赖：T02。实际市场规则须有版本及官方依据，不能把示例常量视为已核验规则。

- [ ] **T04 / P0：把入场、持仓计划和所有退出自动绑定**
  - 范围：Position/lot、ExitPolicyEngine、AccountLedger、卖出订单链。
  - 工作：成交时保存初始风险和 plan_id；按持仓或 lot 保存止损/目标/超时/trailing 状态；统一卖出意图→撮合→账本；引入交易日历而非自然日近似。
  - 验收：不用手工 bind 就能自动止损/止盈/超时；跳空按规则执行；同日不可卖；新旧批次只卖可卖部分；卖不出继续挂风险；移动止损下一事件生效；期末未平仓只估值。
  - 依赖：T03。

- [ ] **T05 / P0：收拢策略资格和证据链**
  - 范围：DecisionEngine、H2、breakout、regime、规则卡与注册表。
  - 工作：明确 H2 计数规范并接入/替代旧三层实现，提供与规范一致的标注序列；新突破跟随评估进入正式入口；使用实际 regime 结果；从源对象传播 family，不得硬编码。
  - 验收：弱突破、缺跟随、跟随失败、未知上下文分别有确定裁决；H2 的相似非 H2 结构不误报；同证据多次评估可解释且不会重复发单；已有 armed 在风险或数据状态变坏时不得开仓。
  - 依赖：T02，可与 T03/T04 的实现分批进行，最终统一验收。

### 批次 B：单票升级为组合交易内核

- [ ] **T06 / P1：强制行情及交易日历完整性**
  - 范围：data/calendar、bars、quality、health、security_master。
  - 工作：精确校验证券、周期、槽位唯一性和交易时段；final 日线只由完整有效槽位形成；记录供应商延迟、复权坐标和缺数策略。
  - 验收：重复 8 根早盘棒不能成为 final；跨午休、错周期、混票、缺尾棒被拒或 partial；节假日和周末可卖日期正确；数据失效只阻止不安全的新风险，已有持仓按预定降级流程管理。

- [ ] **T07 / P1：实现多票统一组合分配**
  - 范围：PortfolioAllocator、账户级行情快照、风险预算和在途委托。
  - 工作：同一时点收集候选并确定排序/配额，维护全持仓 marks 和行业信息；冻结待成交现金及风险；强制单票、行业、总仓位、数量和跳空风险上限；接入熔断。
  - 验收：至少 3 只股票争夺不足现金，固定输入得到固定分配；换事件到达顺序不应无解释改变批次结果；同票多源不重复预算；部分成交/撤单后额度正确；缺一票报价显式降级而不在部分写账后崩溃；熔断停止新仓而不停止退出。
  - 依赖：T03/T04/T06。

- [ ] **T08 / P1：实现订单、成交、账本的持久化和恢复**
  - 范围：事件仓库、事务边界、订单/成交/持仓标识、checkpoint、reconcile。
  - 工作：保存完整因果关联 run→candidate→setup→plan→order→fill→lot→exit；订单及成交具有唯一约束；费用与现金采用确定精度和舍入规则；失败时不能出现订单已成交但账本未落地的半状态。
  - 验收：在下单前/成交后/记账中/保存 checkpoint 前注入进程中断，重启状态与不中断运行一致；重复成交回报不抛出破坏处理链的异常、不重复记账；错序/撤单与成交竞态按真实事件规则处理；每天订单、成交、现金和持仓可以对账。
  - 注意：当前 apply_fill 先检查终态再检查 fill_id，FILLED 后重复同一 fill 会抛错；而订单对象去重也不能代替账本去重。此处须一并设计。
  - 依赖：T02/T03/T04。

- [ ] **T09 / P1：让 backtest 和 paper 使用同一内核**
  - 范围：research/replay、SessionOrchestrator、时钟及 execution adapter。
  - 工作：回放只提供时点化数据和模拟执行适配，移除或明确隔离 entry_signal_idx 的独立交易路径；产出包含初始点、持仓、现金、费用及每日收盘点的 NAV。
  - 验收：同一冻结事件流在历史模式和模拟实时模式下，决策/订单/成交/账本一致；最后一棒处理、未平仓估值、分红送转与原始/复权坐标行为可复算；不再有未写入的 nav_series；差异归因来自真实对照运行而非任意四个输入数字。
  - 依赖：T04/T06/T07/T08。

### 批次 C：交付每天能使用的选股及模拟系统

- [ ] **T10 / P1：接入真实数据和完整股票池**
  - 范围：至少一个可用行情 provider、证券主数据、股票池和数据快照。
  - 工作：落实数据来源/权限/字段单位/交易日历版本；支持增量拉取、失败重试、校验和冻结快照；历史池包含当时上市/退市、ST/停牌等有效状态，不能直接拿当前存活名单回测。
  - 验收：一个明确日期范围的真实数据，从干净环境可重复获得或读取同 hash 快照；缺失退市、行业历史等信息必须列为能力限制；未经校验数据不能悄悄进入交易。
  - 外部源不可用时，仍交付 provider 接口、契约测试及显式 BLOCKED，不用伪数据填充“真实收益”。

- [ ] **T11 / P1：交付真实候选来源与五模型桥接**
  - 范围：公开可解释基线 provider、selection merge、STRUCTURED_V1 适配。
  - 工作：首先让公开基线在真实股票池上产生候选；用真实脱敏样例确认 rows/code/bucket/sources 等结构和时间单位；保留来源价格/目标及未校准概率标签；用证券主数据判定交易所。
  - 验收：同票来源合并不丢证据；盘后候选不会提前用于当天交易；错误版本、缺时间、模糊代码被拒；私有 provider 不可用仍可运行基线模式，并在报告清晰标记。
  - 依赖：T06/T10。真实私有样例是五模型支路的明确外部依赖。

- [ ] **T12 / P1：交付统一 CLI、报告和运行说明**
  - 建议入口：`pal data sync`、`pal scan`、`pal backtest`、`pal paper run`、`pal report`、`pal reconcile`、`pal doctor`；具体语法可调整，业务能力不可省略。
  - 工作：命令加载同一配置和快照、进入同一业务内核；日报由真实状态投影生成，包含候选/拒绝原因、待触发、委托、成交、持仓、退出、现金、风险、成本、净值和数据健康。明确“可观察、可触发、已委托、已成交”的差别。
  - 验收：干净环境按 README 一组命令完成从数据到报告；不得让用户写 Python 拼对象才能日常使用；每个结果含 run_id、commit、config/data/calendar/rule 版本；无行情、无候选、无交易、运行失败各有不同状态与退出码。
  - 依赖：T09/T10/T11。

- [ ] **T13 / P1：完成持续运行与故障演练**
  - 范围：调度、进程锁、健康检查、告警、备份、恢复、操作手册。
  - 工作：明确盘前同步、盘中推进、盘后对账流程；处理断网、延迟、重复进程、数据源切换、停牌/复牌和人工停止开仓；告警渠道可配置，实测发送需授权。
  - 验收：建议至少连续 20 个交易日 paper 作为第一轮运维门槛，并覆盖重启、断网、重传、部分成交、拒单等演练；所有差异解释并处理。20 日只是运维样本，不能作为收益有效性的证明。
  - 依赖：T08/T12。

### 批次 D：证明是否值得承担真实资金风险

- [ ] **T14 / P1：修复统计裁决并开展可复现超额收益研究**
  - 范围：研究结果 schema、release_gate、实验运行器、指标与基准。
  - 工作：缺关键指标禁 PASS；研究计划先冻结主指标、基准、成本、容忍回撤、样本量和失败条件；预注册选择器/门控/执行消融对照；统一在组合逐日 NAV 上计算超额，报告交易成本、换手、容量、敞口及行业/风格影响。
  - 验收：训练/验证/最终留出明确隔离，涉及持有期的标签正确 purge/embargo；选参不能查看最终留出；CI 计算方法考虑收益序列相关性；报告不同市场阶段、成本/滑点压力和参数稳定性；没有足够数据时输出 INCONCLUSIVE，不能把测试通过翻译成盈利证明。
  - 原始基准策略、基线选股、五模型候选及逐门变体须公平比较，避免把市场暴露或选股池变化错误归为价格行为信号贡献。
  - 依赖：T09/T10/T11，经济性裁决需引用该 run 的工程与数据验收证据。

- [ ] **T15 / P2：为实盘交付券商适配和操作控制**
  - 范围：BrokerAdapter、账户与订单同步、回报映射、权限、密钥外置及人工操作入口。
  - 工作：确认目标券商与其真实支持的委托类型、费率、限制和接口；先接仿真/只读对账，再验证拒单、超时、部分成交、撤单竞态、断线恢复；策略和风控复用已验收内核。
  - 验收：内部与券商资金/持仓/订单/成交对账闭合；未知委托状态禁止盲目重发；风险停止和恢复有可审计操作。涉及真实账户权限和资金执行必须由账户所有者明确授权，完成小规模运行验收后才扩大规模。
  - 依赖：T13/T14。若收益研究 FAIL，不得通过换一份报告或静默改阈值放行；新策略版本需要重新冻结和验证。

- [ ] **T16 / 全程：维护真实完成状态与回归门**
  - 工作：采用 PLANNED / IMPLEMENTED / COMPONENT_TESTED / E2E_VERIFIED / PAPER_VERIFIED / LIVE_VERIFIED，外加 BLOCKED，替代含混 DONE；不把收益结论与工程状态混写。
  - 验收：每项状态绑定命令、产物、commit、数据/配置版本；53 个隔离文件的能力归属和运行条件明示；交易关键正例不得 skip；自动化检查不只统计测试数量，还必须执行约定闭环及反例集。

## 6. 阶段验收门与交付包

| 门 | 完成条件 | 应提交产物 |
|---|---|---|
| M1 正确单笔闭环 | T01–T05 及必要数据校验通过 | 有成交、无成交、阻塞成交、止损/止盈/超时的事件链及数值账本 |
| M2 完整组合内核 | T06–T09 通过 | 多票争资、部分成交、故障恢复、模式一致性、连续净值 |
| M3 日常 paper 可用 | T10–T13 通过 | 真实 scan、paper、日报、对账和运维演练记录 |
| M4 经济有效性可判定 | T14 完成；结果可为 PASS/FAIL/INCONCLUSIVE | 冻结计划、数据 manifest、样本外组合结果、成本压力及可复现命令 |
| M5 实盘系统交付 | 前序必要门通过，T15 授权验收 | 券商适配、真实对账、风控操作、恢复证据及运行手册 |

每个批次建议提交同构 evidence 目录：run_manifest、decisions、orders、fills、positions、cash_movements、nav、risk_events、daily_report、reconciliation、test_results。格式可为 JSONL/Parquet/JSON/Markdown，但同一 run 的关联键必须一致。缺某项必须说明其为何不适用，不能空文件充数。

**下一次复审最值得交付的是 M1+M2 的可复现运行包，而不是再增加一批只有孤立单元测试的模块。** 随后完成真实数据及日常 paper，再进入经济性与实盘验收。最终目标始终是完整交易系统。

## 7. 本次复现方法与结果

默认测试命令：在仓库根目录安装项目及 dev 依赖后执行 `python -m pytest -q -rs`。本审查环境使用外置 pytest 依赖目录，未更改项目依赖文件。

以下脚本可放到仓库根目录，以 `PYTHONPATH=src python review3_checks.py` 执行。它输出当前行为，不是通过就代表正确的回归测试。前半部分显式注入 ArmedSetup，目的是隔离执行边界；弱突破部分调用真实引擎，并使用合法交易时段；最后一项直接复用仓内完整成交测试的夹具。

```python
import json, runpy
from datetime import datetime, timedelta, date
from pal.data.bars import Bar, resample_30m_to_daily
from pal.data.calendar import TZ, TradingCalendar
from pal.pipeline.orchestrator import SessionOrchestrator, OrchestratorConfig, ArmedSetup
from pal.signals.engine import EngineConfig
from pal.ledger.positions import AccountLedger
from pal.research.framework import PreregisteredPlan, release_gate
from pal.context.regime import RegimeKind
from pal.selection.providers import Candidate

IID='SSE.600519'
T=datetime(2026,10,13,9,30,tzinfo=TZ)
def bar(t=T,o=10.1,h=10.5,l=9.8,c=10.2,v=100000):
    return Bar(IID,'30m',t,t+timedelta(minutes=30),t+timedelta(minutes=30),o,h,l,c,v)
def orch():
    return SessionOrchestrator(OrchestratorConfig(EngineConfig('review3',enabled_families=('breakout',))),AccountLedger(1_000_000))
def arm(q, at=T-timedelta(minutes=30), entry=10):
    q.armed['s']=ArmedSetup('s',IID,'breakout',entry,9,12,at)
out={}
q=orch(); arm(q)
out['buy_stop_uses_prior_open']=q.on_bar(IID,bar(o=9,h=10.5,l=8.9,c=10.2),[],[],None)
q=orch(); arm(q)
out['zero_volume_fill']=q.on_bar(IID,bar(v=0),[],[],None)
out['zero_volume_qty']=q.ledger.positions.total_qty(IID)
q=orch(); arm(q)
out['entry']=q.on_bar(IID,bar(),[],[],None)
out['nextday_below_stop_events']=q.on_bar(IID,bar(t=T+timedelta(days=1),o=8.5,h=8.8,l=8,c=8.2),[],[],None)
out['nextday_remaining_qty']=q.ledger.positions.total_qty(IID)
out['position_plan_bound']=hasattr(q,'_active_stop')
q=orch(); arm(q)
out['gap_above_buy_stop']=q.on_bar(IID,bar(o=11,h=11.5,l=10.8,c=11.2),[],[],None)
q=orch(); arm(q,entry=12)
for _ in range(8):
    ev=q.on_bar(IID,bar(),[],[],None)
out['same_bar_8_times']={'last_events':ev,'nav_rows':len(q.nav_series),'remaining_setups':len(q.armed)}
q=orch(); arm(q,at=bar().available_at)
out['same_timestamp_fill']=q.on_bar(IID,bar(),[],[],None)
partial=resample_30m_to_daily([bar()]*8,IID)[0]
out['duplicate_bars_daily']={'is_final':partial.is_final,'bar_end':str(partial.bar_end),'volume':partial.volume}
p=PreregisteredPlan('review3','alpha','benchmark',0.001,max_drawdown_tolerance=.15,planned_sample=30,variants=('B4',))
out['gate_missing_drawdown']=release_gate(p,{'alpha':.01},30,ci_lower=.005,g0_engineering_passed=True).value
out['gate_metrics_dd90pct']=release_gate(p,{'alpha':.01,'max_drawdown':.9},30,ci_lower=.005,g0_engineering_passed=True).value
out['gate_explicit_dd90pct']=release_gate(p,{'alpha':.01},30,ci_lower=.005,realized_max_drawdown=.9,g0_engineering_passed=True).value
# Use real engine, weak breakout and no supplied regime; historical bars can span
# multiple days here. This probes engine/orchestrator contracts, not market data quality.
q=orch()
calendar=TradingCalendar(tuple(date(2026,10,d) for d in (13,14,15)), 'review3-fixture')
starts=[s for d in calendar.trading_days for s,e in calendar.bars_for_day(d)]
hist=[bar(t=starts[i],o=9.5,h=10,l=9,c=9.6) for i in range(21)]
last=bar(t=starts[21],o=10,h=10.3,l=9.8,c=10.01)
cand=Candidate('cand',IID,('static_pool',),starts[16],starts[16],None)
out['weak_breakout_no_daily']=q.on_bar(IID,last,hist,[],cand)
out['weak_breakout_decisions']=[d.detail for d in q.decisions_log]
out['weak_breakout_family']=[s.family for s in q.armed.values()]
out['real_engine_repeat_same_bar']=q.on_bar(IID,last,hist,[],cand)
# Exactly reproduce existing full-fill fixture and count actual events.
ns=runpy.run_path('tests/pal/test_e2e_orchestrator.py')
q,led=ns['new_orch'](); bars=ns['make_h2_bars'](); ev=[]
for i in range(1,len(bars)):
    ev+=q.on_bar(IID,bars[i],bars[:i],ns['trend_daily'](),ns['mk_cand'](),RegimeKind.UPTREND)
out['existing_full_fill_test']={'events':ev,'decisions':len(q.decisions_log),'qty':led.positions.total_qty(IID),'cash':led.cash}
print(json.dumps(out,indent=2,ensure_ascii=False))

```

实际输出：

```json
{
  "buy_stop_uses_prior_open": [
    "FILL:s:2400@9"
  ],
  "zero_volume_fill": [
    "FILL:s:2400@10"
  ],
  "zero_volume_qty": 2400,
  "entry": [
    "FILL:s:2400@10"
  ],
  "nextday_below_stop_events": [],
  "nextday_remaining_qty": 2400,
  "position_plan_bound": false,
  "gap_above_buy_stop": [
    "NO_FILL:s:('price_not_touched',)"
  ],
  "same_bar_8_times": {
    "last_events": [
      "EXPIRED:s"
    ],
    "nav_rows": 8,
    "remaining_setups": 0
  },
  "same_timestamp_fill": [
    "FILL:s:2400@10"
  ],
  "duplicate_bars_daily": {
    "is_final": true,
    "bar_end": "2026-10-13 10:00:00+08:00",
    "volume": 800000
  },
  "gate_missing_drawdown": "PASS",
  "gate_metrics_dd90pct": "PASS",
  "gate_explicit_dd90pct": "FAIL",
  "weak_breakout_no_daily": [
    "ARMED:setup_e2160d118331"
  ],
  "weak_breakout_decisions": [
    {
      "entry": 10.0,
      "stop": 9.8,
      "target": 11.0,
      "strength": "weak"
    }
  ],
  "weak_breakout_family": [
    "H2"
  ],
  "real_engine_repeat_same_bar": [
    "FILL:setup_e2160d118331:10000@10"
  ],
  "existing_full_fill_test": {
    "events": [],
    "decisions": 0,
    "qty": 0,
    "cash": 1000000.0
  }
}

```

## 8. 交给下一位 AI 的执行指令

> 请以本报告指定提交为审查基线，先读取项目约束与原任务书，再按 T01–T16 推进。最终目标是完整交易系统，不能把只有研究函数、空跑测试或手工拼装组件称为完成。先落实 M1、M2，复现本报告反例并加入有效回归，统一历史回放和 paper 内核，交付能运行、能恢复、能对账的事件闭环。后续接入真实数据和候选提供者，完成日常 CLI、报告、持续 paper 与样本外超额收益研究。私有包、行情权限及券商依赖如实登记；可独立完成的公开基线路径继续推进。不得通过删除反例、放松断言、增加 skip、修改收益阈值或把合成数据当实证来宣布完成。每批提交真实运行命令、关联产物、结果和限制。用户未授权真实账户执行前，不下真实订单。
