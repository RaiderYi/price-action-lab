# 状态纠偏说明（第二轮复审批次 A）

依据：《price-action-lab_第二轮复审与修正清单.md》（审阅提交 b412e1a）。
本文件不删除历史批次记录；在其之上逐任务纠偏。原 IMPLEMENTATION_STATUS
中标注 DONE 的条目，凡未达到"业务验收通过"标准的，改记 PARTIAL/BLOCKED。

## 纠偏原则（复审 §4）

"有代码""单测通过""主链可用""真实市场验证"是四种不同状态。此前把
前两种当成了后两种，本表纠正为复审口径。

## 逐任务纠偏表

| 原记录 | 纠偏后 | 依据（复审 R 编号） |
|---|---|---|
| S0 全8 DONE | S0-01/02/05/07/08 保持；S0-03 PARTIAL（doctor 不覆盖新交易链）；S0-04 PARTIAL（53 集成测试隔离但未测能力不得标 DONE）；S0-06 PARTIAL（legacy 路径已改，新链未强制） | R12 |
| S1 全8 DONE | S1-01/06/07/08 保持；S1-02 PARTIAL（一致性审计未全链可达）；S1-03 PARTIAL（统计分离达成，legacy 路径未迁移）；S1-05 保持（规则卡完成且被引用） | R04（strict 定义偏差影响 S1-02/03） |
| S2 全8 DONE | S2-02/03/06/07/08 保持（有反例测试）；S2-04 PARTIAL；S2-05 PARTIAL；**S2-03 PARTIAL（R03：日线聚合未检查完成/未过滤证券）**；S2-01 BLOCKED（真实供应商） | R03、R10 |
| S3 7/8（S3-03 BLOCKED） | **S3-02 PARTIAL→BLOCKED 纠偏补充（R11：桥接契约与仓内文档不一致，协议未就绪）**；S3-06/07/08 PARTIAL（合成夹具通过，未真实运行） | R11 |
| S4 全8 DONE | **S4-03 PARTIAL（R04：未接 bar_counting 三层，趋势门未使用）；S4-04 PARTIAL（R05：本棒突破误当跟随）；S4-05 PARTIAL（研究级检测存在但 R09 定价错误）；S4-01 PARTIAL（R10：摆点未传供应商延迟）；S4-02 PARTIAL（R10：MA60 数据不足错误）；S4-08 PARTIAL（R01：无 TRIGGERED 后链路，candidate 未参与）**；S4-06/07 PARTIAL（R09：定价公式错误仍存在） | R01/R04/R05/R09/R10 |
| S5 全8 DONE | **S5-02 PARTIAL（R06：撤单后 apply_fill 复活）；S5-08 PARTIAL（decompose_diff 是包装器非实验）；S5-07 PARTIAL（R02：回放器绕过决策/撮合/组合，nav_series 恒空）**；S5-01/03/04/05/06 PARTIAL（组件有单测，未在主链强制） | R02/R06 |
| S6 全8 DONE | **S6-01/02 PARTIAL（R07：单票上限未扣已有持仓）；S6-04 PARTIAL（R10：移动止损立即生效）；S6-05 PARTIAL（函数返回1≠持仓行为验证）**；S6-03/06/07/08 PARTIAL（同上，未主链强制） | R07/R10 |
| S7 4/8 | **S7-08 PARTIAL→BLOCKED 纠偏（R08：gate 缺 CI/超回撤/NaN 可 PASS）；S7-04 PARTIAL（指标函数存在，无净值序列产出）** | R08 |
| S8 1/8 | S8-02 PARTIAL（渲染组件可用，无 CLI 入口）；S8-01 BLOCKED（scan/backtest/paper 未交付） | R01 |
| S9 未开始 | 保持（如实） | - |

## 已验证 vs 未验证边界（R12 落地）

- `.audit/scenario_coverage.py` 的 27/27 是**人工映射的 node 通过**，
  不是场景级业务验收。以下映射被复审指出语义错位，作废：
  - "现金只够部分标的"→单票现金测试（非多票争资批量验收）
  - "成本/撮合变化与账本一致"→普通现金守恒（非对照实验）
  - `test_engine_never_sees_future` 只断言 asof 透传（未做扰动实验）
- 53 个 tests/integration 文件仍未运行（预期），对应能力一律不得标 DONE。

## 本轮修正批次安排（复审 §5）

- 批次 A（本文件）：状态纠偏，不改业务代码
- 批次 B：R03/R06/R07/R08 + R10 T+1 边界（先反例后修复）
- 批次 C：R04/R05/R09/R10 其余
- 批次 D：R01/R02 端到端合成链
- 批次 E/F：真实数据与研究验收（外部依赖，登记不虚报）
