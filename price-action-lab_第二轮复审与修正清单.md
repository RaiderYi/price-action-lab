# Price Action Lab 第二轮复审与修正清单

审阅日期：2026-10-12（上海时间）  
审阅提交：`b412e1a0113b9678898831e424a2cc472b558423`  
提交时间：2026-10-12 22:02:50 +08:00  
对照基线：`02154d7327530f699be23017534d6157bd646f5a`  
审阅范围：最新实现、任务状态、默认测试及针对性反例；不修改仓库业务代码。

## 1. 当前结论

**这轮开发完成了相当数量的基础组件，但还没有完成一个可端到端运行的选股交易研究系统。当前可以继续开发和测试，尚不具备据此评价策略超额收益的条件。**

这不是仅缺真实行情的问题：结构定义、数据完成状态、订单终态、仓位限制、发布门禁仍存在可复现错误；新增决策、撮合、组合与账本之间也缺少实际调用链。仅接入行情不能解决这些问题。

| 层面 | 本次核验结论 |
|---|---|
| 代码建设 | 相比基线144个文件发生变化，新增pal分层包、数据对象、结构定价、账户和研究组件，方向正确 |
| 默认测试 | 本次实跑 **428 passed**，不是照抄开发记录 |
| 测试范围 | `pyproject.toml` 默认排除 `tests/integration`，其中有53个测试文件；428通过不能表述为全部功能/全部集成测试通过 |
| 信号主链 | engine只有wait/reject，未完成后续TRIGGERED→订单→成交→组合账本链路 |
| 回测 | 独立单票回放器，外部传入信号索引，未调用新决策内核和统一撮合/组合风控 |
| 数据 | 已有数据协议和部分工具，真实供应商、历史股票池及行情未接入；部分时点逻辑还需修正 |
| 产品 | CLI目前只有doctor；每日计划渲染已有组件，scan/backtest/paper完整入口未交付 |
| 实证 | 没有新增真实市场样本外回测、组合超额或前向paper证据 |
| 验收 | 不接受“S0—S6全部完成”的总体结论；应逐项改为已验证/部分实现/阻塞/未开始 |

## 2. 应当保留的进展

1. 新增`pyproject.toml`与pal包，工程组织比原来清晰；默认测试可以运行。
2. 旧突破收盘位置阈值已经修正，原始负收益证据没有被删除。
3. Candidate、Bar、DecisionSnapshot、启发式分数与经验概率分离等对象为继续整合提供了基础。
4. 结构价格模块对空证据抛错，已经改善原来无条件百分比兜底问题；但具体定价公式仍有错误，见下文。
5. 账户组件已能处理基础现金、佣金、部分T+1批次场景；不能因此推定所有入口已经强制执行这些约束。
6. 研究状态明确区分PASS/FAIL/INCONCLUSIVE，且开发记录主动承认数据未接入、费率未核验、私有包未取得及S9未开始，这些诚实边界应保留。

不要推倒重来。下一轮应聚焦修正关键不变量、补上真实调用链与更有约束力的验收。

## 3. 按影响排序的问题

P0＝阻断可信研究/执行闭环；P1＝在相应功能启用前必须修复。代码链接全部固定到本次审阅提交。

### R01 / P0：决策引擎没有完成可执行信号链路

位置：[signals/engine.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/signals/engine.py#L57)、[pal_cli.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal_cli.py)。

源码确认：

- 引擎最多把setup推进到ARMED，输出wait；没有后续条件触发处理和订单派发。
- `candidate`虽然传入，但没有参与候选代码匹配、可用时间、eligible_from和过期校验。
- 日线regime会计算出来，但没有成为H2或breakout资格控制；`h2_min_trend_quality`传入后也未使用。
- setup注册时`expires_at=asof`，未建立合理触发窗口；引擎没有推进`on_bar`检查到期。
- 同一个引擎对相同数据重复evaluate，第一次输出一个决策，第二次输出零个；这不是“重复下单”，但与“纯函数式、同事实同决策”的当前声明不一致。应分开确定性决策与幂等事件写入。
- CLI只有doctor；没有真正连接数据、候选、引擎与账户的scan/paper入口。

复现：传入**明日才可用、且证券代码与被分析股票不同**的候选，日线数据为空，仍得到`regime=unknown、armed=1、decisions=1`。

修复要求：构建明确的批次编排器；验证候选身份/时间/新鲜度；将规则配置真正用于准入；实现条件确认和到期；将产生订单意图与确认成交严格分开。没有行情时也应能用合成事件序列跑通一条完整交易链。

### R02 / P0：回放器绕过决策、撮合与组合层

位置：[research/replay.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/research/replay.py#L42)。

`SinglePositionReplayer`接受外部`entry_signal_idx`，直接用该索引bar的close买入；按初始现金50%定仓，止损止盈由固定比例生成。没有调用`DecisionEngine`、`PortfolioConstraints`、Order状态机或公共fill models。

主要后果：

- 信号时间与成交时间协议不明确。如果索引代表本bar收盘才确认的信号，不能无延迟默认成交于同一收盘。
- 价格、仓位和退出规则与新引擎可以不同，不能用它声称测到了完整新策略。
- `nav_series`定义了但从未写入；无法从这条路径得到连续净值、回撤和日超额。
- 成交量为0仍会买入；参与率函数没有接入这里。
- `decompose_diff`只是把调用者传来的四个数字包装成表，没有实际运行四个对照，不能称已完成收益归因实验。

复现：三根零成交量bar，`entry_signal_idx=[1]`，仍持有5000股；`nav_series=[]`。

修复要求：回放器只负责按时钟投递数据与执行事件，共用真实决策、价格、风险、撮合和账本；将现有独立回放器标为研究辅助/legacy，不视作S5-08验收产物。

### R03 / P0：未完成的日线被标记为完成；证券数据还可能混合

位置：[data/bars.py:resample_30m_to_daily](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/data/bars.py#L89)。

函数按日期聚合所有完成的30m bar，**未检查该交易日是否完整，也没有按传入instrument_id过滤输入**。默认Bar.is_final=True，所以一根09:30—10:00数据即可生成当日已完成日线。

复现结果：`n=1、timeframe=1d、is_final=True、bar_end=10:00`。

这不代表函数凭空取得下午价格，而是把“上午局部日线”误称“最终日线”，会破坏日线特征和时点合并的语义。

修复要求：以交易日历/时段确定预期bar集合，严格按证券及周期分组；不足则不产final日线，或以明确partial通道输出；测试单根bar、午间、缺尾棒、停牌/特殊时段以及多股票混合输入。

### R04 / P0：所谓strict H2仍未接入严格计数和三层过滤

位置：[signals/engine.py:strict_h2_verdict](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/signals/engine.py#L182)。

新逻辑检查“至少两个低点、后低点高于前低点、至少一个高点、当前收盘高于后低点”，没有调用原有bar_counting/qualification/actionability；注释所述“此前H高于更早H”也未实现。

`min_trend_quality`参数完全未使用。最小输入只有L9→H12→L9.5和当前close10，把最低质量要求设为1.1，仍返回非空H2结果。这证明趋势门未被使用，不是说1.1是合理生产配置。

修复要求：先固定H2的计数定义，区分原著转述与本项目工程变体。若采用原有严格计数，实际调用并对账；若采用摆点近似，改名并标为proxy，不可仅因为增加一个低点就冠以strict。用无趋势、连续满足条件、孕线、外包线、两次尝试间隔和失效反例验收。

### R05 / P0：新突破服务把“本棒突破”当成“下一棒跟随”

位置：[signals/breakout.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/signals/breakout.py#L34)。

`confirm_follow=True`时，`follow=last.close > breakout_level`，本质上与`crossed`是同一个条件。第一根突破棒立即获得`follow_through=True`及`actionable_strong=True`；新服务也没有继承刚修好的极端收盘质量条件。

复现：前21棒high10.2，最后棒high11、low9.9、close10.4；收盘位置约45.45%，首次突破仍输出`strong/True/True`。

引擎又只检查`crossed_level`，即使strength=weak也可ARMED。即使将服务修正，引擎若不核验强度，门控仍不生效。

修复要求：存储突破发生的bar ID与冻结突破位；之后已完成bar才能确认跟随；配置明确哪些策略需要跟随/极端收盘；引擎执行相应准入条件。若不需要跟随，应显式使用另一策略版本，不将本棒突破命名为后续确认。

### R06 / P0：撤销订单可以被apply_fill直接复活

位置：[execution/market_rules.py:Order.apply_fill](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/execution/market_rules.py#L128)。

`transition`有合法状态表，但`apply_fill`绕过状态检查直接改数量与状态。

最小复现：

```python
o = Order('o', 'p', 'buy', 'limit', 100, limit_price=10)
o.transition(OrderState.CANCELLED)
o.apply_fill(100, 10)
# 当前结果：state=FILLED, filled_qty=100
```

修复要求：在模拟模型中，只有合法待成交状态可应用fill；加入fill_id幂等及事件时间。如果未来接真实券商，需要专门处理“撤单回报前已经发生但延迟到达的成交”，不能用无时间戳的终态复活代替。另需覆盖未提交订单、REJECTED、重复fill和多次partial fill。

### R07 / P0：单票仓位上限没有扣除已有持仓

位置：[portfolio/risk.py:size_position](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/portfolio/risk.py#L48)。

输入有`instrument_value`，但函数未使用；新增仓位上限按`NAV×10%`计算，没有减已有仓位。

复现：NAV100万元、该股已有9万元、entry10、stop9、cash91万元；允许再买2400股，持仓达到11.4%，突破配置的10%。

修复要求：新增额度=`max(0, NAV×单票上限－已有持仓市值－未成交买单占用)`。持仓数量、行业、总仓位、资金和在途订单一起纳入批量分配，而不是每只股票独立获得同一份现金。

### R08 / P0：研究发布门允许缺置信区间、超回撤和NaN通过

位置：[research/framework.py:release_gate](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/research/framework.py#L205)。

三项问题已复现：

1. `ci_lower=None`时跳过统计检查，主指标达标、样本量达到设定即可PASS。
2. `max_drawdown_tolerance`虽为预注册必填，却未用于结果判定；设容忍15%、结果90%仍PASS。
3. 主指标和置信下界为NaN时，数值比较不会触发拒绝，仍PASS。

修复要求：关键指标必须存在且有限；G0工程证据、成本口径、主基准、经济阈值、置信区间、回撤及失败条件分别验证；缺证据INCONCLUSIVE，违反风险/经济条件FAIL。此门修好前不得用PASS提升任何策略。

### R09 / P1：定价出现多头止损高于入场，以及人为抬高目标

位置：[pricing/structure_prices.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/pricing/structure_prices.py#L36)。

- `price_final_flag_reversal`注释称多头反转，实际要求`entry<stop`。输入flag_high11、failure_low10、measured_target12，得到entry10、stop11、target12、status=structured。
- `price_h2_long`用`max(prior_high, entry+2R)`，会把结构空间不足直接改成至少2R。例如HL2=9、signal_bar_high=10、prior_high=9.5，仍得到target12、RR2。

最终旗形当前默认研究使用，故不描述为已经进入实盘的错误，但必须在启用前修复。H2影响首期结构。

修复要求：StructuredPricePlan自身验证方向关系；结构目标和“固定2R退出策略”分开命名、分开实验；不能为通过RR门把真实障碍位推远。入场/止损触发边界及tick buffer需显式定义。

### R10 / P1：T+1、移动止损和供应商延迟在边界层未强制

涉及多个可独立修复的边界，不能仅由注释或调用者保证。

| 位置 | 复现/源码结果 | 要求 |
|---|---|---|
| `ledger/positions.py:buy` | 将`t1_next_trading_day`传为买入当日后，当日买卖往返成功 | 由交易日历/规则计算sellable_from；非法调用必须拒绝。正常replay路径另有日期检查，因此不能据此断言其已实际发生同日卖出 |
| `portfolio/risk.py:update_trailing` | `effective_at_next_session=True`仍立即把state.stop从9改9.8 | active与pending stop分开，按事件时钟激活，不能用本棒更新后的价位回判本棒 |
| `context/swings.py:detect_swings` | available_at直接等于确认棒bar_end，未传递供应商延迟 | 应至少为参与证据bar的最大available_at；所有as-of工具遵守同一可用时钟 |
| `context/regime.py:assess_trend_regime` | 30根close都为10的数据，ma20=10、ma60=5 | MA60数据不足要unknown或采用明示缩短窗口，不能始终除60 |

摆点延迟反例：确认棒bar_end11:30，供应商available_at12:30，检测结果却宣称摆点11:30可用。在DecisionEngine当前先过滤bar的路径中有一层保护，但直接全量检测再swings_asof的公开组合会过早暴露，因此模块协议仍需修复。

### R11 / P1：五模型桥接格式与仓库已有对接说明不一致

位置：[selection/providers.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/src/pal/selection/providers.py#L85)。

原整合文档描述顶层JSON含`rows`，行字段包括`code/bucket/sources`。当前解析器要求每个块顶层有`symbol/direction/models/asof`。基于已公布rows契约构造的合成样本被拒绝，报缺symbol/direction/models。

这不是对真实私有包运行失败的断言：本次依然没有取得该包。可确定的是实现没有忠实覆盖仓内写明的契约，因此S3-02也不能以“协议就绪”完整验收。

另有源码问题：默认exchange_of全部返回SSE；candidate转换只保留direction等少量信息，原stop/target/bucket未完整映射；解析器并未显式拒绝未知schema版本或重复块。

修复要求：以用户实际脱敏产物确定schema；保留JSON中原字段、来源价格、概率标记与时间；证券身份来自主数据；不要通过编造一种更容易测试的输入格式完成验收。

### R12 / P1：测试“全覆盖”结论超出了脚本证明能力

位置：[.audit/scenario_coverage.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/.audit/scenario_coverage.py)、[tests/pal/test_engine_patterns.py](https://github.com/RaiderYi/price-action-lab/blob/b412e1a0113b9678898831e424a2cc472b558423/tests/pal/test_engine_patterns.py)。

自查脚本是人工场景名称→测试node ID的映射，某node通过即标COVERED。它不验证该测试是否真正覆盖整个场景；27项还是重新编排的映射，不能直接替代原任务书场景逐项验收。

具体例子：

- `test_engine_never_sees_future`只断言`r.asof == asof`，没有修改未来数据并比较过去决策。
- “现金只够部分标的”的场景映射到单票现金约束测试，不是多票争夺资金的批量执行验收。
- “成本/撮合变化与账本一致”映射到普通买卖现金守恒，不是改变成本与撮合条件的对照实验。
- 测试`apply_fill`只测正常路径和超量，没有验证撤销后成交，导致R06漏检。
- 突破测试接受本棒突破为跟随，意味着测试把错误业务语义固定成了预期。

修复要求：场景→输入→预期业务不变量→真实调用路径→证据产物逐项对应；覆盖报告区分unit/integration/end-to-end。默认排除的53个仓外集成测试可以继续明确隔离，但不应把未测能力标DONE。

## 4. 任务书完成状态建议纠偏

这里不报一个缺乏逐项充分验证的“完成百分比”。有代码、单测通过、主链可用、真实市场验证是不同状态。

| 原阶段 | 当前合适状态 | 主要依据 |
|---|---|---|
| S0 | 大部分完成，部分验收待补 | 已有包和默认测试；未见依赖锁文件，doctor主要检查旧模块，不覆盖新交易链 |
| S1 | 部分完成 | 对象和注册表已建；并非所有协议完整落地；严格信号定义仍有偏差 |
| S2 | 部分完成，真实输入阻塞 | 数据工具存在，但日线完成状态、延迟传播有漏洞，真实供应商尚无 |
| S3 | 部分完成 | 透明基线/排序/去重有实现；真实五模型未验、桥接契约偏差 |
| S4 | 部分完成，不通过阶段出口 | H2/突破语义与实际触发链未完成，regime/candidate门未生效 |
| S5 | 部分完成，不通过阶段出口 | 账户和撮合工具已有，订单终态漏洞、回放不共用主链、无NAV序列 |
| S6 | 部分完成 | 风险函数有实现；单票上限失效、批量资金分配未接入、退出生效时序需修复 |
| S7 | 研究辅助组件已建，正式实验未完成 | gate可误PASS；只有指标函数与变体枚举，没有真实实验结果 |
| S8 | 计划渲染组件已建 | CLI只有doctor，完整选股/持仓/研究产品尚无 |
| S9 | 未开始 | 状态文件也已明确承认 |

需要纠正的重点不是任务数量，而是`IMPLEMENTATION_STATUS.md`把一些“函数存在”写成了“业务验收通过”。例如S5-08需要新旧结果差异实验，不能用四个输入数字相加代替；S6-05需要持仓行为验证，不能用函数固定返回1代表完成。

## 5. 下一轮具体修正顺序

建议按以下小批次推进，每批先建立能暴露当前错误的反例，再修实现。不要先扩展形态、接LLM或做收益优化。

| 完成 | 批次 | 范围 | 出口标准 |
|---|---|---|---|
| [ ] | A：纠正状态与验收 | R12；将不满足验收的DONE改为PARTIAL/BLOCKED；保存本审阅提交 | 状态逐任务有真实证据，不再以映射脚本等价全覆盖 |
| [ ] | B：关键数据与资金不变量 | R03、R06、R07、R08；R10中的T+1边界 | 缺日线不能final；终态订单不能无时序复活；既有/在途仓位计入上限；缺CI/超回撤/NaN不PASS |
| [ ] | C：信号和定价语义 | R04、R05、R09、R10其余 | H2计数可审计；跟随只能来自后续bar；结构目标不强抬；延迟和移动止损时间明确 |
| [ ] | D：接通最小完整系统 | R01、R02 | 一条合成数据链跑通Candidate→Decision→Trigger→Order→Fill→Ledger→NAV→Report，并有预期无成交路径 |
| [ ] | E：真实数据与接口 | R11；数据供应商、主数据、交易日历、现行/历史规则核验 | 真实冻结快照可读取；来源规则带版本；未核验规则不可用于正式结果发布 |
| [ ] | F：重新运行研究验收 | 时间切分、变体、净值、成本压力、统计区间 | 真实U0/S0/B0—B3等同口径实验；有JSON/CSV净值及交易明细；证据不足输出INCONCLUSIVE |

### 最小端到端验收包

下面的合成数据只能验证工程，不得当作收益证据。

1. **有成交场景**：候选先可用，结构后确认，未来bar再触发；订单受理后合法成交；T+1可卖后退出，资金/费用/NAV能手算核对。
2. **无成交场景**：有setup但永不触发，最终过期，现金不变且有明确原因。
3. **成交受阻场景**：零成交量/价格限制导致未成交；后续允许部分成交并正确保留剩余量。
4. **多票争资场景**：多只股票同时满足条件，但现金或行业额度不足；排序与分配确定，不能共同使用同一份现金。
5. **持仓上限场景**：原有9%单票仓位，新订单最多使用剩余1%，包含在途订单。
6. **重放一致场景**：相同快照得到相同决策；重复导入同一fill不重复记账；恢复后继续运行一致。
7. **未来扰动场景**：改t之后的行情、候选和供应商延迟，t之前决策/订单不变。
8. **研究门禁场景**：缺CI、NaN、超回撤、未核验数据各自阻止正式PASS。

以上须从产品/CLI入口运行到最终产物，不得绕过引擎手工把entry_signal_idx塞入回放器。

## 6. 可直接交给开发 AI 的指令

```text
请对照《price-action-lab_第二轮复审与修正清单.md》继续修正。
审阅基线为 b412e1a0113b9678898831e424a2cc472b558423；若HEAD更新先对比差异。

当前默认428项测试通过，但这不等于80项任务已完成。
不要扩展新功能，不要调参追收益，也不要把缺数据作为所有未完成项的理由。

1. 先纠正IMPLEMENTATION_STATUS：按真实验收将未完成项改PARTIAL/BLOCKED，
   不删除历史记录，另写状态纠偏说明。
2. 按本复审第5节A—F批次实施，每个R编号保留最小错误复现和修复后预期。
3. 强制修复：不完整日线、撤单后apply_fill、已有持仓被忽略、
   gate无CI/超回撤/NaN仍PASS；随后修复H2定义、突破跟随和结构价格。
4. 接通一个真实调用链：候选→决策→触发→订单→撮合→账户→连续NAV→报告。
   历史回放和paper共用内核，不再各自实现另一套交易逻辑。
5. 在无真实数据时完成合成端到端验收，产出仅标“工程验证”。
   真实行情和五模型样例取得后再运行真实接口与样本外研究。
6. 每次完成说明必须附命令、输入版本、实际结果和输出路径。
   “函数返回1”“注册了9种变体”“映射到某测试通过”不能替代业务验收。
7. 不复制私有包进公开仓库，不进行实盘下单。

第一批从A和B开始，完成后先输出差异与验收证据，再继续C和D。
```

## 7. 本次验证记录与限制

### 默认测试命令

本次在独立审阅工作树中运行，临时安装pytest依赖，不改变项目业务代码。

```bash
PYTHONPATH=/workspace/scratch/3a2d88fc4d01/review-python-deps python -m pytest -q
```

实得：`428 passed in 0.92s`。这是当前机器的结果，耗时不作为性能承诺。

### 补充反例结果摘要

| 反例 | 当前结果 |
|---|---|
| 一根上午30m聚合日线 | 生成is_final=True、bar_end10:00的日线 |
| 首次大棒突破、收盘位置45.45% | strong、follow=True、actionable=True |
| 明日且异股票候选、无日线环境 | unknown环境仍ARMED |
| 同一引擎重复相同evaluate | 第一次1条decision，第二次0条 |
| 两低一点高、质量阈值1.1 | H2非空，参数未约束 |
| CANCELLED订单apply_fill | 变为FILLED |
| 买入传当日sellable_from | 当日买卖成功 |
| 已有9%单票仓位再定仓 | 允许新增2.4%，合计11.4% |
| 无CI且回撤90%、阈值15% | PASS |
| 主指标/置信下界NaN | PASS |
| 多头final_flag entry10/stop11 | structured成功 |
| H2 prior_high9.5低于entry10 | target强抬12、RR2 |
| 零成交量回放 | 买入5000股，NAV序列为空 |
| 下一时段生效的移动止损 | 当前state立即改变 |
| 摆点确认棒供应商延迟60分钟 | 摆点available_at未延迟 |
| 30根价格10的bar | MA60错误为5 |
| 基于文档rows契约的合成JSON | 拒绝，要求另一组顶层字段 |

本次未取得私有包与真实行情，没有完成真实新回测，也没有量化每一处错误对收益的影响。不把合成反例得出的工程缺陷夸大为已经发生的实盘损失；但这些缺陷足以阻断“可用交易系统已全部完成”的验收结论。

下一次复审应首先看端到端事件产物和上表反例的修复证据，再看测试数量和收益曲线。
