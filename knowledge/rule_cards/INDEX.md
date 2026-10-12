# 知识规则卡索引（S1-05）

规则卡是"审核后的知识"，与 knowledge/ 原始记录分离（任务书 §3.2：
knowledge Markdown 保留原始记录，新增审核后的 rule cards）。

| card_id | 主题 | 对应问题 | status |
|---|---|---|---|
| KR-H2-COUNT-001 | H2 严格计数 vs legacy 代理 | F02/F21 | AUDITED |
| KR-FINAL-FLAG-001 | final_flag 三事件语义拆分 | F04/F21 | AUDITED |
| KR-PROBABILITY-MATH-001 | 概率表"70%需1:1打平"数学错误 | F21 | AUDITED |

## 待补规则卡（后续阶段）

- KR-WEDGE-THREE-PUSH（三推单调方向/间隔校验，F18）→ S4-05 前完成
- KR-RANGE-ENTRY-NORM（区间入场归一化，F19）→ S4-05 前完成
- KR-BREAKOUT-STRENGTH（突破强度统一，F16）→ S4-04 前完成
- KR-L2-RISK-ONLY（L2 作为风险提示而非开空仓，任务书 §4）→ S4 前完成

## 引用规则

1. 工程实现（信号检测/定价/过滤）引用知识依据时**必须引用 card_id**，
   不允许直接引用 knowledge/ 原文（原文含已审核为错误/冲突的条目）；
2. RAG 检索命中 knowledge/ 原文时，若存在对应规则卡，回答必须附带
   规则卡的裁决；
3. 未审核知识不可自动转生产规则（任务书 S1-05 验收标准）。
