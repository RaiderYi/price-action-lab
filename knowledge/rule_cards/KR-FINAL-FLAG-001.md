# 知识规则卡：Final Flag 语义拆分（S1-05，F04/F21）

card_id: KR-FINAL-FLAG-001
status: AUDITED（已审核；实现必须按本卡拆分语义，F04 裁定）
created: 2026-10-12
audit_scope: knowledge/concepts/final-flag.md, final-flags.md, signal_predictor.py

## 定义（来源锚定）

> "A final flag is a small trading range that forms late in a trend,
> representing the last pause before the trend reverses or accelerates
> into a climax." — knowledge/concepts/final-flag.md

> "Breakout from final flag usually fails quickly"
> "One of the best reversal setups when combined with other signals"
> — knowledge/concepts/final-flag.md Core Points

## 语义拆分（F04 裁定：三个不同事件，禁止混在同名信号）

| 事件 | 名称（工程键） | 语义 | 交易含义 |
|---|---|---|---|
| 1. 旗形本体形成 | `final_flag_formation` | 趋势末端 3-5 根小实体紧凑区间 | 只观察，不出信号 |
| 2. 顺势突破发生 | `final_flag_breakout_with_trend` | 旗形向原趋势方向突破 | 事件记录；**知识库明示此类突破通常快速失败**，不能当作延续信号入场 |
| 3. 突破失败后反转 | `final_flag_failed_breakout_reversal` | 顺势突破失败（跌回旗形/反向走出）后的反转 | Brooks 定位的"best reversal setups"；**未经确认不得直接反向下单**（任务书 F04 动作项） |

## 冲突与裁决

- **代码 vs 知识**：`signal_predictor._is_final_flag` 检测"向趋势方向突破"
  并发 final_flag 信号 → 实际捕获的是事件2；但知识库把 final flag 定位为
  **反转**结构（事件3）。旧回测 JSON 中 final_flag 计数语义不明，归因失真。
- **裁决**：事件2/事件3 是不同信号；旧数据按事件2 解释；S4-05 拆分实现
  后，`final_flag` 旧键冻结为 legacy 事件2，新键分别登记注册表。

## 反例（实现必须拒绝）

- 趋势中段（非末端）的普通旗形 → 不是 final flag
- 事件2（顺势突破）当作反转入场依据 → 拒绝（语义混用）
- 事件3 无失败确认（价格未跌回旗形下沿/无反向棒）→ 不得开反向仓
