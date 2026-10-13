# price-action-lab 第四轮代码审查与交易系统成熟度分析报告

**审查日期：2026-10-13（北京时间）**  
**审查提交：`fb5dbee1e547838ec5b7d46fd81aa9c23ff3c9f4`**  
提交时间：2026-10-13 09:15:20 +08:00。对比上轮基线：`feb364158d612ee9ba2e26973f8d96bd5f15c5d7`。

[审查版本](https://github.com/RaiderYi/price-action-lab/tree/fb5dbee1e547838ec5b7d46fd81aa9c23ff3c9f4) · [本轮变更](https://github.com/RaiderYi/price-action-lab/compare/feb364158d612ee9ba2e26973f8d96bd5f15c5d7...fb5dbee1e547838ec5b7d46fd81aa9c23ff3c9f4)

## 一、审查结论

**本轮修复有效，系统接入仍未完成。项目已经具备更多可用组件及局部交易闭环，但尚不能作为完整选股、回测和持续交易系统验收。**

这一轮应当肯定的变化，是上一轮多个精确反例已经被消除：buy-stop 不再按触发前开盘价成交、零量买入被拦截、成交后能自动绑定止损、同棒重复处理不再重复买入、重复 K 线不能伪造完整日线、缺回撤不再直接 PASS。新增组合分配器、事件仓库、回放器与 CLI，也是向完整系统推进的正确方向。

但实际运行表明，**新增模块尚未形成一条统一且可靠的业务路径**：CLI 没有向策略提供候选和日线背景；默认环境评估会吞掉有效信号；回放不保留跨日历史；组合分配和事件仓库没有接入交易；已有持仓时多票行情会报错，甚至可能先买错股票再报错。因此，`IMPLEMENTATION_STATUS.md` 中“T07/T08/T09/T12 DONE”和“M2 工程部分达成”目前证据不足。

我的验收判断是：

| 目标 | 本轮判断 | 原因 |
|---|---|---|
| M1 正确单笔闭环 | **部分通过，尚不能整体通过** | 已验证部分买入→自动止损；默认信号路径、跟随资格、实际成交风险及退出流动性仍有缺陷 |
| M2 完整组合内核 | **不通过** | 多票执行、组合风控、持久化恢复和回放历史均有实际断点 |
| M3 日常 paper 可用 | **未达到** | CLI 已有框架；scan/backtest 空跑，paper 恒定 BLOCKED，无法形成自产交易数据的对账闭环 |
| M4 超额收益证据 | **未建立** | 无可验收的真实样本外组合交易结果；当前零事件、平净值不能用来评价策略收益 |
| M5 实盘系统 | **尚未交付** | 应在统一内核、持续 paper、经济性和执行适配验收后推进 |

下一阶段最有价值的工作，是打通一条**不手工注入交易计划、从命令行启动、能真实产生成交与退出、可重启恢复及对账**的完整运行链。真实供应商与私有五模型尚未确定，不妨碍先用冻结输入完成这项工程验收。

## 二、审查范围与验证方法

本次从远端获取最新提交，建立独立只读审查工作副本；没有修改、提交或推送仓库业务代码，也没有连接交易账户或执行真实订单。

本轮新增 3 个提交：

| 提交 | 内容 |
|---|---|
| `e6b0c60` | 第三轮任务 T01–T05：单笔闭环修复 |
| `bf08d81` | T06–T09：日历、组合分配、事件仓库、回放器 |
| `fb5dbee` | T12：统一 CLI 与 run 产物 |

变更总计：19 个文件，新增 2,493 行、删除 157 行。

实际执行：

- 默认测试：`python -m pytest -q -rs`，结果 **519 passed，0 skipped**。
- `tests/integration` 下 **53 个测试文件**仍由默认 pytest 配置排除。这些文件没有计入“0 skipped”，不能视为已验证。
- 重新运行上一轮反例脚本，核验修复行为，而非只查看新增测试名称。
- 构造冻结合成行情，实际调用当前 DecisionEngine、SessionOrchestrator、BacktestRunner、PortfolioAllocator、EventStore 及 CLI。
- 额外验证：默认/显式环境对照、多票错配、风险预算、部分成交、零量退出、供应商延迟、失败重试与事件恢复。

附录提供本轮完整反例脚本与实际输出。合成数据仅用于工程验证。部分执行边界案例明确注入 ArmedSetup，以隔离撮合及账本问题；这些案例不冒充候选选股或策略盈利证据。强突破环境对照使用真实决策引擎，回放历史检查只记录传入真实引擎的窗口长度，没有伪造决策。

## 三、上一轮问题的实际修复结果

| 上轮反例 | 最新实际结果 | 认定 |
|---|---|---|
| 升破 10，O=9，却成交 @9 | 现成交 `2400@10` | 原定价错误已修复 |
| 跳空 O=11>entry=10 却 NO_FILL | 现成交 `2400@11` | 触发语义已修复；跳空后的风险重算未完成 |
| 零成交量买入 2,400 股 | NO_FILL，持仓 0 | 买入侧原反例已修复 |
| 买后次日跌破 stop 没有退出 | `EXIT_STOP:2400@8.5`，持仓归零 | 自动止损绑定已生效 |
| 同棒重复 8 次导致过期、重复 NAV | 仅 1 条 NAV，setup 保留 | 内存内正常重复投递已修复；失败重试及重启恢复另见下文 |
| 信号棒重复投递后买入 | 重复调用不成交 | 原反例已修复 |
| 重复早盘棒 ×8 形成 final 日线 | is_final=False，并去重成交量 | 原重复数据反例已修复 |
| 缺回撤 / metrics 中 90% 回撤未检查 | 分别 INCONCLUSIVE / FAIL | 原 gate 漏检已修复 |
| 弱突破 + 空日线仍 ARMED | REGIME_BLOCK:unknown | 原组合反例已拦截 |
| 原完整成交夹具全程 0 事件 | 新夹具已出现 ARMED、FILL、T+1 阻塞事件 | 比上轮明显进步；该测试仍未断言完整退出与自动环境路径 |

最后一项此次实际得到 `ARMED → FILL:1800@11.62 → EXIT_BLOCKED_T1`。这说明不能继续简单复述“所有成交测试都空跑”；应准确区分已有局部正例和仍缺失的全链验收。

## 四、本轮主要发现

严重程度口径：**P0 为阻断交易系统验收的业务正确性或核心路径问题；P1 为必须补齐的约束、恢复或证据问题。** 这不是安全漏洞评级。

### A01 / P0：默认环境评估吞掉有效信号

**位置：** `src/pal/pipeline/orchestrator.py:191–200`。

当 regime_kind 未显式传入时，编排器先调用一次 `engine.evaluate()` 获取 regime，随后在允许交易时再次调用 `evaluate()` 获取决策。但引擎内部有 SetupBook 状态，第一次评估已经把 setup 从 QUALIFIED 推进至 ARMED，第二次不会再次返回该 setup。第一次输出却被丢弃。

**实际对照：** 同一组强突破行情、60 根合成历史日线，内部评估环境为 RANGE：

- 显式传入 RANGE：返回 `ARMED:setup_e2160d118331`。
- 使用默认自动环境：返回 `[]`。
- 默认路径内部 SetupBook 已有 armed，外部 `orch.armed` 为空。

**影响：** 正常使用者依赖的自动路径会漏掉本来符合当前引擎规则的信号，且没有明确拒绝原因。这是新接入造成的状态副作用，不能靠增加行情数据修复。

**验收要求：** 一次事实输入只计算一次可复用的评估结果，资格判定与状态提交分开；自动环境与相同显式环境产生一致计划；被环境拒绝的信号不能静默消耗未来合法的状态迁移。

### A02 / P0：scan/backtest 的成功输出没有执行选股策略

**位置：** `src/pal_cli.py:_cmd_scan`、`_cmd_backtest`。

- scan 对每根棒调用 `on_bar(..., bars_30m=[b], daily_bars=[], candidate=None)`。没有候选时，决策分支不会运行，也没有调用现有 baseline_rank/provider 产生候选。
- backtest 构建 `BacktestDay(d, tuple(v))`，未传 candidates 或 daily_bars；没有加载这两类输入的代码路径。
- scan 把没有进入策略判断的标的输出为 watch/NO_SIGNAL，不能区分“未评估”和“评估后无信号”。

**实际运行：** 对包含可供直接引擎生成强突破的 22 根行情执行 CLI：

| 命令 | 退出码 | 实际结果 |
|---|---:|---|
| scan | 0 | 准入 0、待触发 0、观察 1、拒绝 0 |
| backtest | 0 | 3 日、0 事件、现金和净值均为 1,000,000 |
| paper --events ... --state ... | 3 | 恒定输出“需要实时行情事件流”，未读取输入事件文件 |
| reconcile --run 本次 backtest 目录 | 3 | 缺 events.jsonl |

输出文件只有 backtest.json 和 run_manifest.json，没有交易事件或账本快照。

**影响：** 用户可以得到格式正确的报告，却没有运行候选筛选与交易策略。它属于已实现的命令框架，尚不是可用的选股/回测入口。

**验收要求：** 明确 snapshot schema，载入候选、日线背景或从冻结股票池生成基线候选；缺必要输入必须报告未执行的能力。无候选、无信号、无交易与执行失败用不同结构化状态表示。CLI 必须有一个非手工武装的正例产生确定的决策及买卖事件。

### A03 / P0：回放历史每日清空，跨日结构无法完整识别

**位置：** `src/pal/research/backtest_runner.py:72–84`。

传给引擎的 bars_30m 仅来自当前 BacktestDay，前一交易日的行情没有保留。对于当前约定的标准 30m 日内网格，每票单日最多 8 根，而 breakout 入口要求至少 22 根。

**复现：** 跨 3 个交易日的 22 根输入，真实引擎收到的最大历史窗口只有 **8 根**，回放事件为 `[]`，净值为初始资金。

即使先修好 CLI 候选输入和 A01，这个独立问题仍会阻断跨日突破识别及其他需要更长历史的结构。

另有两个代码级边界需要同时修复：注释说按 available_at 投递，实际按 bar_start 排序；结尾估值按照传入 days/bars 的原始顺序覆盖 marks，未严格取各票最后时点。前者可能让延迟数据与单调时钟发生冲突，后者可能在输入乱序时选错期末价格。本次没有把这两项描述为已经运行的市场反例。

**验收要求：** 每票维护跨日历史窗口；用实际可知时间推进时钟；历史数据按 available_at 裁切；期末估值取明确的最后有效报价。多日整批、逐日增量和合法分块输入结果一致。

### A04 / P0：多票路径存在错票成交和部分写账后报错

**位置：** `orchestrator.py:172–185、225、243–251`；BacktestRunner 共用一个 SessionOrchestrator。

触发循环遍历全部 armed，没有检查 `setup.instrument_id == bar.instrument_id`。同时每次 NAV 只提供当前一只股票的报价。

**实际反例：**

1. 账本已有 A 股持仓，输入 B 股行情：抛出“无 A 市价，NAV 无法计算”。
2. 仅为 A 预先武装计划，输入 B 股行情：先按 B 的价格为 A 买入 **2,400 股**，随后计算 NAV 才报同样错误。
3. 失败行情已经记入 consumed 集合，重复输入返回 `[]`。

**影响：** 这是错误证券交易和非原子账本变更，不只是多票功能暂缺。虽然 SessionOrchestrator 的注释写“单票”，但公开 on_bar/BacktestRunner 接受多票，现有代码没有强制单票边界。

**验收要求：** 为每票隔离信号与历史状态，并使用账户级统一报价和组合事件协调；至少在单票内核边界拒绝异票输入且保证零副作用。三票运行不能依赖外部手工拆账户或分别拥有一份初始资金。

### A05 / P0：跳空成交未重算风险，配置上限可以被突破

**位置：** `orchestrator.py:_try_fill`，按 setup.entry 定仓后直接使用 fill.price 买入。

**复现配置：** 初始资金 100 万，单笔风险预算 0.25%=2,500，单票上限 10%=100,000。计划 entry=10、stop=9.9，实际跳空在 11 成交。

实际买入 **10,000 股 @11**：

- 买入名义金额 **110,000**，超过原 10 万单票预算。
- 到计划止损的价格风险 **11,000**，是原单笔预算的 **4.4 倍**，尚未计费用和滑点。

这些数字是对项目自身配置的检验，不涉及对当前市场交易规则的外部断言。

**验收要求：** 撮合/提交前用可执行价格或保守价格上界重算现金、风险、敞口和 RR；超范围时缩量或放弃。不能用更差成交价买入原计划数量后，才计算实际风险。

### A06 / P0：部分成交、退出流动性和持仓计划还不完整

**位置：** `orchestrator.py:261–280、_manage_exit`。

**已运行反例：**

- volume=2,500、参与率=10%，得到 **250 股**买入。当前 MarketRuleSet 的 lot_size=100，但最终成交数量未再按该配置取整。
- 编排器把 250 直接作为订单 qty，状态记为 FILLED，并删除 setup。原风险定仓可买的剩余数量没有作为剩余委托保存，也没有部分成交订单状态或资金占用。
- 次日止损棒 volume=0，仍全量 `EXIT_STOP:2400@8.5`；买入侧零量修复没有覆盖卖出侧。

**代码检查补充：** 止盈直接调用 ledger.sell，没有建立卖出 Order；position_plans 以 instrument_id 单值保存，后续同票买入会覆盖旧计划；超时、移动止损等退出组件尚未进入该业务路径。

**验收要求：** 统一订单意图、原委托量、累计成交量、剩余量、撤单和占用；若业务选择“仅提交容量允许数量”，应明确为缩量新单，不宣称实现了部分成交生命周期。买卖两侧共用流动性及规则校验；按策略定义管理多批持仓退出，不得静默覆盖；止损、止盈、超时、trailing 均进入可审计卖出链。

### A07 / P0：事件仓库没有接入交易，且不能接受同单第二笔成交

**位置：** `src/pal/pipeline/event_store.py`；CLI reconcile 是其目前的业务读取入口。

主编排器没有 EventStore 依赖，也没有把订单、成交、账本变更、计划状态和 consumed bar 写入仓库。新增 replay_events 计算了独立 cash/positions 摘要，但没有重建一个可继续交易的 SessionOrchestrator。sellable 字段存在却没有更新逻辑，计划、T+1 lot、引擎状态与在途委托也没有恢复。

**实际反例：**

- 先写入 fill_id=f1、order_id=o1 的成交，再写不同 fill_id=f2、相同 order_id=o1 的第二笔成交，抛出 `EventConflictError: 重复事件: fill|o1`。
- 原因是所有 fill 的 order_id 都被当成唯一键，一单多笔成交自然会冲突。
- 输入含 sellable_from 的买入事件，恢复态 sellable 仍为 `{}`。
- 实际 backtest 产物不能直接执行 reconcile，因为没有自动生成 events.jsonl 和 ledger_snapshot.json。

**验收要求：** 以同一业务事件更新持久化与内存状态；每笔成交以 fill_id 去重，order_id 是可重复关联键；订单状态更新不能被“订单唯一”阻断。恢复后继续处理下一根行情，与不中断运行逐项一致。仅手工写入几条成交再核对算术，不足以证明系统恢复成功。

### A08 / P0：事件先标已消费，失败后无法安全重试

**位置：** `orchestrator.py:161–162` 在交易逻辑之前写 consumed/last_clock。

**复现：** 提供仅含当前交易日的日历，触发买入时查不到下一交易日，on_bar 抛 KeyError。随后补齐日历并重投同一根行情，返回 `[]`，仍然没有买入，因为该行情已被记为处理完成。

A04 的案例进一步表明，某些异常发生在现金/持仓已经改变之后。内存变量同时更新，不等于事务意义上的原子性；正常重复去重也不等于故障恢复幂等。

**验收要求：** 区分接收、处理中、业务提交、完成；在一致的事务或可恢复事件提交点标记完成。对校验失败应零副作用；对已提交事件重传应幂等。测试必须真实注入日历错误、磁盘错误或中途异常，再恢复运行验证。

### A09 / P0：日历聚合重新引入提前可见数据

**位置：** `src/pal/data/bars.py:142–145`。

当传入 calendar 时，聚合日线的 available_at 被固定成收盘时刻，没有取输入 K 线最大 available_at。

**复现：** 最后一根 30m 棒于 **15:07** 才可用，聚合 final 日线却标为 **15:00** 可用，提前 7 分钟暴露收盘数据。

当前完整性检查主要比较 bar_start.time 集合，也没有完整比较每个槽位的结束时刻。这属于需要补齐的代码边界，不能仅靠“有 8 个正确起点”代表完成网格正确。

**验收要求：** 最终可知时间至少为 `max(交易日正式收盘可用时刻, 所有输入 available_at)`；完整性比较准确的开始与结束槽位、时区和交易日。端到端 as-of 测试中，15:00 不能看到 15:07 才到的数据。

### A10 / P1：组合分配器自身仍漏算已有行业暴露及持仓数

**位置：** `src/pal/portfolio/allocator.py:106、125–149`。

行业视图从空字典开始，只加本批批准额度及当前请求股票的既有市值，没有完整的已有持仓→行业映射。配置中的 max_positions 没有进入 allocate 检查。在途占用是方法内临时值，下一次调用不会保留真实未完成委托。

**复现：** 已持有同一行业 A 市值 240,000，申请买入 B。分配器仍批准 B **9,900 股 @10**，该行业市值达到 **339,000**，账户 NAV=999,940，约 **33.90%**，超过配置的 25%。

另将 max_positions 设为 1、账户已有一只股票，仍批准第二只股票。

**影响：** 即便下一步把分配器接入主链，也不能直接认为组合风险已合格。当前主链尚未调用它，其内部熔断亦未形成实际交易保障。

**验收要求：** 账户持仓、行业归属、已挂单、部分成交与撤单共同形成持久的风险视图；所有配置项要么真实生效，要么显式不支持。批次之间也要共享真实资金和风险占用。

### A11 / P1：跟随确认与成交前资格再检查仍未落实

**位置：** `signals/engine.py:_eval_breakout` 与 `orchestrator.py:on_bar`。

模块注释声称 assess_with_follow_bars 已接入，但主引擎实际仍调用 assess_breakout_strength，只新增 weak 过滤。`assess_with_follow_bars` 没有业务调用。armed 的执行条件是 high>=entry，早于后面的候选/regime 分支，且不受传入 DOWNTREND 约束。

**复现：** 强突破计划已 ARMED，下一棒收盘跌回突破位以下，并在 on_bar 显式传 DOWNTREND，仍买入 `8300@10.2`。

仅凭棒末收盘失败并不能断言棒内曾触价的止损买单绝对不该成交；这里真正的问题是**系统没有兑现自己宣称的“跟随确认后交易”策略，也没有规定环境变更在何时生效**。若采用预先激活的 intrabar buy-stop，应明确这是另一种策略时序，不能冒用需要后续完成棒确认的证据。

**验收要求：** 冻结突破棒、跟随条件、确认时点及订单生效时点；跟随失败与单纯触价分开。对已 ARMED 计划，在执行前按当时已知的环境、数据质量、证券状态和风险重新裁决；日后才可知的收盘条件不能回溯改变已发生的成交。

### A12 / P1：测试与版本产物仍不足以支撑 DONE

**位置：** `tests/pal/test_e2e_orchestrator.py`、`test_round3_t01/t08/t09/t12.py`、`src/pal_cli.py:_manifest`、`IMPLEMENTATION_STATUS.md`。

具体观察：

- 原 full_fill_path 仍保留 `len(decisions_log)>=0` 等不验证业务的断言，且显式传 regime，绕过 A01 默认路径。
- 新“完整路径”测试注入 ArmedSetup，能保护买卖执行边界，却未覆盖候选→真实引擎→计划这段。
- 参与率测试 volume=1,000、配置10%，实际只断言 qty<=1,000，而非<=100，无法识别一部分超量实现。
- family 测试遍历 possibly-empty armed；无计划时可直接通过。
- backtest/paper 一致性测试主要比较两次 BacktestRunner，并没有运行实际 paper 命令；paper 目前恒定 BLOCKED。
- 恢复测试手工拼事件并检查计算值，没有中断/恢复实际交易进程。
- run_manifest 仅存 run_id、时间、commit、config_version 字符串及 kernel；没有实际输入快照 hash、完整参数 hash、日历/规则版本绑定。_load_snapshot 只读 JSON，未验证文件内容与冻结清单一致。
- README 仍主要描述旧入口，新的命令及快照契约未形成完整日常操作说明。

**验收要求：** 将 COMPONENT_TESTED 与 E2E_VERIFIED 分开；每个“完成”引用同一 run 的可重放输入、决策、订单、成交、账本和对账产物。CLI 冒烟 exit=0 只说明命令返回成功，不能替代交易业务验收。

## 五、为什么会持续出现“单测全过、系统仍不通”

这几轮的共同原因是：修复围绕上一轮的具体反例增加组件与测试，而缺少一个真正代表用户使用方式的强制验收入口。

例如，撮合修复后新增了成功买入案例，但风险定仓仍采用旧触发价；组合分配器有独立测试，但编排器根本不调用；事件仓库能落盘，但实际成交不向它写入；CLI 能产出文件，但未加载候选，所以策略根本不运行。每个函数看似改善，组合后的行为仍可能错误。

建议下一轮把交付组织方式改成：**每个批次必须从同一个公开入口贯穿到可核对的业务结果，新增模块必须由该入口实际调用。** 对固定且可复现的场景，应该先写下订单、成交、现金和持仓的精确期望，再检查实现是否满足。

这并不要求增加复杂基础设施。一个进程、一个可靠的事务存储、文件快照和 CLI 足以完成首版；必须优先明确领域状态、时间、风险和提交边界。

## 六、对第三轮 T01–T16 的重新认定

| 原任务 | 本轮认定 | 仍需处理 |
|---|---|---|
| T01 有效验收夹具 | COMPONENT_TESTED，部分 E2E | 默认入口、跨日、多票、恢复及精确账本正例 |
| T02 事件幂等 | PARTIAL | A01/A08；重启后的消费进度与交易状态 |
| T03 撮合语义 | PARTIAL | A05/A06；真实订单生命周期、实际价格风险和双边流动性 |
| T04 自动退出 | PARTIAL | 单笔自动止损有效；止盈订单、批次计划、超时/trailing 尚缺 |
| T05 资格链 | PARTIAL | A01/A11；默认评估副作用、跟随确认与成交前复核 |
| T06 行情/日历 | PARTIAL，出现回归 | A09；主输入路径也需要强制校验 |
| T07 多票组合 | COMPONENT_TESTED，未 E2E | A04/A10；已有行业风险、数量、在途额度及主链接入 |
| T08 持久化恢复 | COMPONENT_TESTED，未 E2E | A07/A08；一单多 fill、可继续交易的恢复态、事务 |
| T09 同核回放 | PARTIAL | 已调用同一类；历史、时钟、多票和 paper 接口尚未通过 |
| T10 真实数据 | BLOCKED，登记属实 | 外部来源未定；离线完整快照适配仍可先做 |
| T11 五模型桥接 | BLOCKED/PARTIAL | 私有样例外部依赖；公开基线接入 CLI 不需要等私有包 |
| T12 CLI | PARTIAL | 命令框架可用；选股和交易输入、paper、自产对账闭环未完成 |
| T13 持续运行 | 未交付验收证据 | 先完成离线故障演练，再做真实时段持续 paper |
| T14 统计验证 | gate 局部修复，研究未完成 | 真实多阶段样本外组合结果及经济性裁决 |
| T15 券商适配 | 尚未交付 | 待前序验收及账户授权，不属于本次代码审查的执行动作 |
| T16 真实状态门 | 未落实到完成标准 | 保留历史记录，给出当前逐项权威状态及证据引用 |

不建议用一个“完成百分比”概括以上状态。缺失默认信号路径、组合账本或恢复能力中的任意一项，都足以阻断完整系统上线。

## 七、下一轮执行清单：保留已有成果，优先贯通主链

以下任务对应本报告 A 编号，不替代原 T01–T16 的最终目标；它们是下一轮最应收敛的具体工作。

### 包 1：建立真正运行策略的统一入口

- [ ] **N01：冻结离线输入与输出契约**。规定 bars、日线背景、交易日历、证券/行业信息、候选、配置与 hash 的格式；选定一个包含至少三票、多日、足够历史的固定验收包。合成包用于工程验收，真实包后续用于策略研究。输出必须包含决策、订单、成交、持仓 lot、现金、NAV、风险事件与对账。
- [ ] **N02：修复自动评估副作用**。消除 double evaluate；按一次评估结果完成资格判断和计划提交。验收自动环境与等价显式环境一致、默认入口出现至少一个真实引擎计划、环境拒绝不污染后续状态。对应 A01。
- [ ] **N03：接通 scan/backtest/paper**。scan 由公开基线或输入候选实际评估；backtest/paper 复用同一运行服务。先让 paper --events 消费离线事件并支持 state，再接实时行情。不要把本可离线完成的接线工作全部登记为真实数据依赖。对应 A02。
- [ ] **N04：维护跨日历史与因果时钟**。每票历史可跨日、增量积累；按 available_at 与显式事件优先级推进；聚合传播供应商延迟；完整网格验证起止时刻；日历包含回放期末买入所需的下一交易日。对应 A03/A09。

**出口：** 不注入 ArmedSetup，从 CLI 载入固定输入，自动产生可复核的计划，并明确区分 NO_CANDIDATES、NO_SIGNAL、NO_TRADES、BLOCKED、FAILED。单独用空跑退出码不得通过。

### 包 2：统一组合与成交风险

- [ ] **N05：隔离单票状态、建立账户级批次协调**。所有 armed、history、position plan 按证券归属；维护全持仓行情快照；同一时点候选统一提交给分配器。异票行情不改变他票信号或成交，缺价时按事先定义的降级规则处理。对应 A04。
- [ ] **N06：让组合约束实际执行**。加入已有持仓行业映射、持仓数量、在途现金/风险、费用预算；实际调用熔断与健康门；部分成交/撤单改变占用；跨批次不丢占用。对应 A10。
- [ ] **N07：按实际执行价格复核并实现完整订单生命周期**。统一 buy/sell、整手约束、容量、部分成交、撤单、拒单、委托余量；跳空使用实际可执行价格或保守上界重新定仓。对应 A05/A06。
- [ ] **N08：收拢计划退出与资格时序**。明确突破与跟随策略版本；成交前重查当时可知的约束；同票多批计划不静默覆盖；止损/止盈/超时/trailing 经同一卖出链；零量或无法卖出持续保留风险。对应 A06/A11。

**出口：** 三票争资及同票多源、多批买入、跳空、低量部分成交、零量退出、数据失效和熔断均可精确复算。配置上限在真实执行路径有效。

### 包 3：可恢复、可对账、可持续运行

- [ ] **N09：把持久化置于业务提交边界**。事件仓库/事务数据库与实际交易链共用同一组领域事件；fill_id 去重、order_id 关联；恢复 armed、退出计划、T+1 lot、订单、资金占用、时钟和消费进度。对应 A07/A08。
- [ ] **N10：实现失败恢复与自动对账**。至少在校验前、订单提交后、成交后、记账中、保存进度前注入故障；恢复后与不中断基准逐项相同。系统自身输出 events 和 ledger snapshot，让 reconcile 直接运行，无需手工构造文件。
- [ ] **N11：修正完成状态和验收强度**。为每个 N/T 项记录实际入口、精确产物和失败边界；关键正例不允许靠 skip 或空循环通过；把“文件存在”“两次空结果相等”从业务验收条件中移除。新增命令、输入 schema 和恢复流程写入 README。对应 A12。

**出口：** 同一冻结输入，backtest、离线 paper、故障恢复 paper 的交易结果一致；报告和 reconcile 引用同一 run；持仓及现金无无法解释的差异。

### 包 4：真实市场验证与最终交付

- [ ] **N12：推进真实来源、候选和运维**。确认可用行情源与版本化快照，接通完整可交易股票池及公开基线；私有五模型使用真实脱敏契约样例单独验收。开展真实时段 paper、异常监控、定时任务与日终对账，积累连续运维证据。
- [ ] **N13：开展超额收益研究**。冻结规则、主基准、成本/滑点、样本划分、最大回撤与失败条件；在组合净值而非零交易摘要上比较选股、环境、结构、执行和退出的增量贡献。最终留出不可用于调参；多策略试验需记录选择过程；容量、行业/风格敞口及不同市场阶段单独报告。缺数据用 INCONCLUSIVE，不将修复带来的收益变化解释为已发现 alpha。
- [ ] **N14：交付实际执行适配与操作手册**。在前序门满足后，完成目标券商支持的委托/回报模型、对账、停开仓/恢复及未知订单状态处理；真实账户和资金执行由账户所有者明确授权。完成小规模验收后再决定是否扩大。

真实行情可得性、私有包契约和券商权限属于明确外部依赖；N01–N11 的主要工程工作不应因此停摆。阶段性 paper 稳定运行只能证明运维可靠，不能单独证明长期超额收益。

## 八、下一次复审必须提交的验收矩阵

| 场景 | 入口与必需断言 |
|---|---|
| 默认环境生成信号 | 真实引擎、自动 regime；与显式等价环境一致，ARMED 数量和证据精确匹配 |
| 跨日结构形成 | 至少三日足够历史；交易计划出现在正确可知时点，不能因日界清空 |
| 单笔完整买卖 | 候选→计划→触发→委托→成交→持仓→次交易日退出→报告，精确核对股数、价格、费用及现金 |
| 无交易 | 确实完成策略评估且无计划，现金/NAV 合理；不是 candidate=None 绕过评估 |
| 三票组合 | 三票共用一个账户；异票行情不触发他票；行业、数量、总敞口及现金占用有效 |
| 跳空风险 | 成交价改变后单笔风险、单票市值仍在配置内，或有明确拒绝记录 |
| 部分成交 | 同一 order_id 多个不同 fill_id 正常处理，剩余量/费用/资金占用正确 |
| 无流动性退出 | 零量不能卖出；持仓、未完成订单和风险保留，不虚构止损成功 |
| 供应商延迟 | 15:07 可用的输入不在 15:00 的日线/信号中出现 |
| 中途失败重试 | 异常不永久吞掉行情；已提交成交不重复记账；未提交状态可重试 |
| 进程重启 | 真正关闭并重建运行实例；恢复后继续交易，与连续基准一致 |
| CLI 对账 | 使用系统自产 run 目录运行 reconcile；余额、持仓 lot、订单及成交吻合 |
| 版本追溯 | 输入 hash、配置、规则、日历和代码版本绑定；篡改输入后不得仍称同一冻结运行 |

建议下一次只在 **N01–N11 和上述矩阵有完整证据**后声明 M1/M2 通过。复审仍会保留真实数据、研究与实盘的后续目标，不把“研究组件库”当作终点。

## 九、代码定位索引

所有位置均指本报告固定提交，行号只用于定位，后续修改会变化。

| 文件 | 关键位置 |
|---|---|
| `src/pal/pipeline/orchestrator.py` | 161 消费标记；172 armed 遍历；191 自动环境；225/243 单票 NAV；245 计划价定仓；261 数量；274 计划覆盖；_manage_exit 退出 |
| `src/pal_cli.py` | 58 manifest；136 快照读取；174 scan；208 无候选调用；245 backtest；276 空默认上下文；309 paper；340 reconcile |
| `src/pal/research/backtest_runner.py` | 72–84 回放时钟与当日窗口；89–91 期末 marks |
| `src/pal/portfolio/allocator.py` | 106 行业初值；125–149 暴露和额度计算 |
| `src/pal/pipeline/event_store.py` | 57/76–85 唯一字段；137 sellable；155 replay_events |
| `src/pal/data/bars.py` | 135–145 槽位与可知时间 |
| `src/pal/signals/engine.py` | _eval_breakout 中 weak 过滤与跟随注释 |
| `IMPLEMENTATION_STATUS.md` | 第三轮批次 A/B/C-1 的 DONE 与阶段门声明 |

## 附录 A：可复现检查脚本

在审查版本仓库中安装项目运行依赖后，以 `PYTHONPATH=src python review4_checks.py` 执行下列脚本。脚本的 OUT 只用于审查临时产物，可改为本机目录；所有行情均为合成输入。若用于回归测试，请把这里的观察结果转换成符合本报告验收要求的断言，不要把错误现状写成“应当成功”的固定结果。

```python
import json, runpy, subprocess, sys
from pathlib import Path
from dataclasses import replace, asdict
from datetime import date, datetime, time, timedelta
from pal.data.bars import Bar, resample_30m_to_daily
from pal.data.calendar import TZ, TradingCalendar
from pal.pipeline.orchestrator import SessionOrchestrator, OrchestratorConfig, ArmedSetup
from pal.pipeline.event_store import EventStore, replay_events
from pal.signals.engine import DecisionEngine, EngineConfig
from pal.context.regime import RegimeKind, assess_trend_regime
from pal.ledger.positions import AccountLedger
from pal.execution.market_rules import MAIN_BOARD
from pal.portfolio.allocator import PortfolioAllocator, AllocationRequest
from pal.portfolio.risk import PaperDefaults
from pal.selection.providers import Candidate
from pal.research.backtest_runner import BacktestDay, BacktestRunner

OUT=Path('review4_evidence'); OUT.mkdir(exist_ok=True)
IID='SSE.600519'; B='SZSE.000001'
CAL=TradingCalendar(tuple(date(2026,10,d) for d in (13,14,15,16)), 'review4-fixture')
starts=[s for d in CAL.trading_days for s,e in CAL.bars_for_day(d)]
T=starts[0]
def bar(t=T,o=10,h=10.5,l=9.8,c=10.2,v=100000,iid=IID):
    return Bar(iid,'30m',t,t+timedelta(minutes=30),t+timedelta(minutes=30),o,h,l,c,v)
def orch(cal=CAL):
    return SessionOrchestrator(OrchestratorConfig(EngineConfig('review4',enabled_families=('breakout',)),calendar=cal),AccountLedger(1_000_000))
def arm(q, sid='s',iid=IID,entry=10,stop=9,target=12,at=T-timedelta(minutes=30)):
    q.armed[sid]=ArmedSetup(sid,iid,'breakout',entry,stop,target,at)
def attempt(f):
    try: return f()
    except Exception as e: return {'error':type(e).__name__,'message':str(e)}
out={}
# Actual engine: strong breakout, valid historical daily context.
hist=[bar(t=starts[i],o=9.5,h=10,l=9,c=9.6) for i in range(21)]
sig=bar(t=starts[21],o=9.9,h=11,l=9.7,c=10.9)
daily=[]
d=date(2026,10,12)
while len(daily)<60:
    if d.weekday()<5:
        s=datetime.combine(d,time(9,30),tzinfo=TZ); e=datetime.combine(d,time(15),tzinfo=TZ)
        daily.append(Bar(IID,'1d',s,e,e,10,10.1,9.9,10,100000))
    d-=timedelta(days=1)
daily.reverse()
cand=Candidate('c',IID,('static_pool',),starts[16],starts[16],None)
out['context_kind']=assess_trend_regime(daily).kind.value
qe=orch(); qa=orch()
out['explicit_regime']=qe.on_bar(IID,sig,hist,daily,cand,RegimeKind.RANGE)
out['automatic_regime']=qa.on_bar(IID,sig,hist,daily,cand)
out['automatic_internal_setups']=[{'id':s.setup_id,'state':s.state.value} for s in qa.engine.book.active_setups()]
out['automatic_external_armed']=list(qa.armed)
follow=bar(t=starts[22],o=10.2,h=10.4,l=9.6,c=9.8)
out['failed_follow_still_fills']=qe.on_bar(IID,follow,hist+[sig],daily,None,RegimeKind.DOWNTREND)
# Cross-day history length, using a recording subclass of the real engine.
class RecordingEngine(DecisionEngine):
    def __init__(self,cfg): super().__init__(cfg); self.lengths=[]
    def evaluate(self,asof,bars_30m,daily_bars,**kw):
        self.lengths.append(len(bars_30m))
        return super().evaluate(asof,bars_30m,daily_bars,**kw)
cfg=OrchestratorConfig(EngineConfig('review4',enabled_families=('breakout',)),calendar=CAL)
runner=BacktestRunner(cfg,1_000_000); rec=RecordingEngine(cfg.engine); runner.orch.engine=rec
allbars=hist+[sig]
days=[]
for d in sorted({b.bar_start.date() for b in allbars}):
    at=datetime.combine(d,time(9,30),tzinfo=TZ)
    cd=Candidate(str(d),IID,('static_pool',),at,at,None)
    days.append(BacktestDay(d,tuple(b for b in allbars if b.bar_start.date()==d),tuple(daily),(cd,)))
res=runner.run(days)
out['runner_history']={'total_bars':len(allbars),'max_history_supplied':max(rec.lengths),'events':res.events,'final_nav':res.final_nav}
# CLI: real commands, frozen synthetic input, no source tree changes.
snap=OUT/'snapshot'; snap.mkdir(exist_ok=True)
(snap/'manifest.json').write_text(json.dumps({'asof_date':'2026-10-15','snapshot_id':'review4-synthetic','calendar_version':'review4-fixture'}))
(snap/'bars_main.jsonl').write_text('\n'.join(json.dumps(asdict(b),default=str) for b in allbars))
cli={}
for cmd in ('scan','backtest'):
    dest=OUT/cmd
    p=subprocess.run([sys.executable,'src/pal_cli.py',cmd,'--snapshot',str(snap),'--out',str(dest)],capture_output=True,text=True)
    cli[cmd]={'exit':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}
cli['scan_summary']=json.loads((OUT/'scan/daily_plan.json').read_text())['summary']
bt=json.loads((OUT/'backtest/backtest.json').read_text())
cli['backtest_values']={k:bt[k] for k in ('n_events','final_nav','final_cash')}
cli['backtest_files']=sorted(p.name for p in (OUT/'backtest').iterdir())
for name,args in [('paper',['paper','--events',str(snap/'bars_main.jsonl'),'--state',str(OUT/'paper')]),('reconcile',['reconcile','--run',str(OUT/'backtest')])]:
    p=subprocess.run([sys.executable,'src/pal_cli.py',*args],capture_output=True,text=True)
    cli[name]={'exit':p.returncode,'stdout':p.stdout.strip()}
out['cli']=cli
# Two-stock main path with an existing holding.
q=orch(); q.ledger.buy(IID,100,10,date(2026,10,12),MAIN_BOARD,t1_next_trading_day=date(2026,10,13))
b=bar(iid=B)
out['two_stock_mark_failure']=attempt(lambda:q.on_bar(B,b,[],[],None))
out['retry_failed_bar']=attempt(lambda:q.on_bar(B,b,[],[],None))
out['failed_bar_consumed']=q._bar_key(b) in q._consumed_bars
# Wrong-symbol trigger can alter A before B's NAV fails.
q=orch(); arm(q)
out['foreign_bar_trigger']=attempt(lambda:q.on_bar(B,b,[],[],None))
out['foreign_bar_bought_A']=q.ledger.positions.total_qty(IID)
# Gap risk: stop 9.9, entry10, fill11 => planned risk x11, position cap breached.
q=orch(); arm(q,stop=9.9)
ev=q.on_bar(IID,bar(o=11,h=11.1,l=10.8,c=11),[],[],None)
qty=q.ledger.positions.total_qty(IID)
out['gap_risk']={'events':ev,'qty':qty,'gross':qty*11,'nominal_stop_risk':round(qty*(11-9.9),2),'configured_risk_budget':2500,'configured_position_cap':100000}
# Participation quantity is not rounded and is treated as a fully-filled order.
q=orch(); arm(q)
ev=q.on_bar(IID,bar(v=2500),[],[],None)
plan=q.position_plans.get(IID)
out['odd_lot_partial']={'events':ev,'qty':q.ledger.positions.total_qty(IID),'lot_size':MAIN_BOARD.lot_size,'order_qty':plan.order.qty,'state':plan.order.state.value,'remaining_setups':list(q.armed)}
# Exit liquidity ignores volume.
q=orch(); arm(q); q.on_bar(IID,bar(),[],[],None)
out['zero_volume_stop_exit']=q.on_bar(IID,bar(t=starts[8],o=8.5,h=8.8,l=8,c=8.2,v=0),[],[],None)
# Supplier availability regression introduced by calendar-based resampling.
bs=[bar(t=s) for s,e in CAL.bars_for_day(CAL.trading_days[0])]
bs[-1]=replace(bs[-1],available_at=bs[-1].bar_end+timedelta(minutes=7))
agg=resample_30m_to_daily(bs,IID,calendar=CAL)[0]
out['daily_delay']={'last_input_available':str(bs[-1].available_at),'output_available':str(agg.available_at),'final':agg.is_final}
# Quantity risk allocator and existing sector exposure.
led=AccountLedger(1_000_000)
led.buy('SSE.600001',24000,10,date(2026,10,12),MAIN_BOARD,t1_next_trading_day=date(2026,10,13))
alloc=PortfolioAllocator(); req=AllocationRequest(B,'new',10,9.9,12,industry='same-sector')
r=alloc.allocate([req],led,{'SSE.600001':10,B:10})[0]
out['sector_existing_exposure']={'approved_qty':r.qty,'post_sector_value':240000+r.qty*10,'nav':led.nav({'SSE.600001':10,B:10}),'cap_pct':.25}
small=PortfolioAllocator(replace(PaperDefaults(),max_positions=1))
out['max_position_count']=asdict(small.allocate([req],led,{'SSE.600001':10,B:10})[0])
# Event store blocks a second partial fill of the same order.
es=EventStore(); es.append('session_init',{'initial_cash':10000})
payload={'fill_id':'f1','order_id':'o1','side':'buy','qty':100,'price':10,'instrument_id':IID,'commission':5,'sellable_from':'2026-10-14'}
es.append('fill',payload)
out['second_partial_fill']=attempt(lambda:es.append('fill',dict(payload,fill_id='f2')).to_json())
out['recovered_sellable']=replay_events(es.events()).sellable
# Calendar exhausted consumes a failed event before retry can succeed.
q=orch(TradingCalendar((date(2026,10,13),),'last-day')); arm(q)
out['end_calendar_failure']=attempt(lambda:q.on_bar(IID,bar(),[],[],None))
q.cfg.calendar=CAL
out['retry_after_calendar_fix']=q.on_bar(IID,bar(),[],[],None)
out['retry_after_calendar_qty']=q.ledger.positions.total_qty(IID)
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
(OUT/'results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str))

```

## 附录 B：本次实际输出

run_id 使用运行环境时钟；报告日期及提交时间以本报告首页的北京时间为准。下列绝对路径仅标识此次临时审查输出。

```json
{
  "context_kind": "range",
  "explicit_regime": [
    "ARMED:setup_e2160d118331"
  ],
  "automatic_regime": [],
  "automatic_internal_setups": [
    {
      "id": "setup_e2160d118331",
      "state": "armed"
    }
  ],
  "automatic_external_armed": [],
  "failed_follow_still_fills": [
    "FILL:setup_e2160d118331:8300@10.2"
  ],
  "runner_history": {
    "total_bars": 22,
    "max_history_supplied": 8,
    "events": [],
    "final_nav": 1000000.0
  },
  "cli": {
    "scan": {
      "exit": 0,
      "stdout": "scan OK: run=run_20261012_222215_146162 准入0 待触发0 观察1 拒绝0\n  report: /workspace/scratch/3a2d88fc4d01/review4_evidence/scan/daily_plan.json\n  report: /workspace/scratch/3a2d88fc4d01/review4_evidence/scan/daily_plan.md",
      "stderr": ""
    },
    "backtest": {
      "exit": 0,
      "stdout": "backtest OK: run=run_20261012_222215_d8b407 days=3 events=0 final_nav=1000000.0\n  report: /workspace/scratch/3a2d88fc4d01/review4_evidence/backtest/backtest.json",
      "stderr": ""
    },
    "scan_summary": {
      "admitted": 0,
      "awaiting_trigger": 0,
      "watch": 1,
      "rejected": 0
    },
    "backtest_values": {
      "n_events": 0,
      "final_nav": 1000000.0,
      "final_cash": 1000000.0
    },
    "backtest_files": [
      "backtest.json",
      "run_manifest.json"
    ],
    "paper": {
      "exit": 3,
      "stdout": "paper: BLOCKED —— 需要实时行情事件流（T10 外部依赖）\n  已交付内核与事件仓库：pal.pipeline.event_store + SessionOrchestrator（同一内核）"
    },
    "reconcile": {
      "exit": 3,
      "stdout": "BLOCKED: run 目录无 events.jsonl（scan 模式不产生交易事件）"
    }
  },
  "two_stock_mark_failure": {
    "error": "DomainValidationError",
    "message": "无 SSE.600519 市价，NAV 无法计算"
  },
  "retry_failed_bar": [],
  "failed_bar_consumed": true,
  "foreign_bar_trigger": {
    "error": "DomainValidationError",
    "message": "无 SSE.600519 市价，NAV 无法计算"
  },
  "foreign_bar_bought_A": 2400,
  "gap_risk": {
    "events": [
      "FILL:s:10000@11"
    ],
    "qty": 10000,
    "gross": 110000,
    "nominal_stop_risk": 11000.0,
    "configured_risk_budget": 2500,
    "configured_position_cap": 100000
  },
  "odd_lot_partial": {
    "events": [
      "FILL:s:250@10"
    ],
    "qty": 250,
    "lot_size": 100,
    "order_qty": 250,
    "state": "filled",
    "remaining_setups": []
  },
  "zero_volume_stop_exit": [
    "EXIT_STOP:2400@8.5"
  ],
  "daily_delay": {
    "last_input_available": "2026-10-13 15:07:00+08:00",
    "output_available": "2026-10-13 15:00:00+08:00",
    "final": true
  },
  "sector_existing_exposure": {
    "approved_qty": 9900,
    "post_sector_value": 339000,
    "nav": 999940.0,
    "cap_pct": 0.25
  },
  "max_position_count": {
    "instrument_id": "SZSE.000001",
    "setup_id": "new",
    "allow": true,
    "qty": 9900,
    "reason_codes": [
      "OK"
    ]
  },
  "second_partial_fill": {
    "error": "EventConflictError",
    "message": "重复事件: fill|o1（seq 2 已存在）"
  },
  "recovered_sellable": {},
  "end_calendar_failure": {
    "error": "KeyError",
    "message": "'2026-10-13 之后无交易日（日历范围外）'"
  },
  "retry_after_calendar_fix": [],
  "retry_after_calendar_qty": 0
}
```

## 附录 C：可直接交给执行 AI 的指令

> 请以 fb5dbee1e547838ec5b7d46fd81aa9c23ff3c9f4 为审查基线，先复现本报告 A01–A12，再沿 N01–N14 推进完整交易系统。保留已经修复的旧反例，不重复推翻有效组件。先完成默认 CLI→真实候选/策略评估→跨日、多票组合→订单与成交→自动退出→事务账本→恢复与对账的统一路径。禁止用手工注入 ArmedSetup 代替整个系统的正例；它只适合执行边界单测。公开基线及离线 paper 可独立完成，不等私有五模型或实时源。每个阶段提交同一 run 的冻结输入、决策、订单、成交、持仓、现金、NAV、恢复与对账证据。修正 DONE 状态，不以测试数量、空跑成功码、文件存在或两次空结果相等宣称闭环完成。最终继续完成真实市场 paper、样本外超额收益检验及经授权的实盘适配。
