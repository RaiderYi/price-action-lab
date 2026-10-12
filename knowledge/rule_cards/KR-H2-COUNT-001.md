# 知识规则卡：H2 计数（S1-05，F21）

card_id: KR-H2-COUNT-001
status: AUDITED（已审核，可作为工程实现依据）
created: 2026-10-12
audit_scope: knowledge/concepts/h2-l2-signal.md, h2-l2-state-machine.md, bar-counting.md

## 定义（来源锚定）

> "H2 (second Higher low in bull trend) and L2 (second Lower high in bear
> trend) are high-probability trend-continuation signals after a two-legged
> pullback." — knowledge/concepts/h2-l2-signal.md（转述自 Brooks 著作）

多头链：`isPL` 起步 → 破高得 H1 → 回撤后上破 H1 高 → **H2**
（h2-l2-state-machine.md 状态机口径）

**严格计数前提**：
1. 处于牛市趋势（先有趋势，后有回调，不是任何 HL 反弹）；
2. 回调为两腿（two-legged pullback）；
3. H2 是**第二次** higher low 的信号棒入场，不是第一次；
4. 入场在 H2 信号棒上方触发（buy stop），收盘跌回结构则失效。

## 冲突与裁决

| 冲突 | 位置 | 裁决 |
|---|---|---|
| "纯 H2/L2 给固定 0.55 结构分" | h2-l2-state-machine.md L25 | 0.55 是**启发式质量分**，不是胜率。工程侧已由 S1-06 HeuristicScore 与 p_win 分离承载；知识页保留原文但转述层标注 |
| 代码 `HL 出现且价格>HL×1.01` 即 H2 | signal_predictor.py `_check_h2_l2_setup` | **不满足严格计数**（第一个 HL 也放行）——这是 legacy_proxy 血统，任务书 F02 已裁定拆分。规则卡确认：该实现 = `legacy_proxy_h2`，`h2_second_entry` 严格计数必须按上述4前提实现 |

## 工程偏离登记

- legacy `_check_h2_l2_setup`：无两腿计数、无趋势前提校验、1.01 反弹阈值
  为工程魔数（无 Brooks 出处）→ 登记为 F02，S4-03 重做
- strict 链路（strict_pa_detector）存在于仓内但从未进入回测（F01）

## 反例（实现必须拒绝）

- 首个 HL 后立即反弹（只有一腿回调）→ 不是 H2
- 熊市/区间里的 HL 反弹 → 不是 H2（无趋势前提）
- 当前价虽高于 HL 但未越过 H2 信号棒高点 → setup 未触发（armed 非 triggered）
