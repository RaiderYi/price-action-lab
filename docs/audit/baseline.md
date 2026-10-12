# S0-01 Legacy 基线冻结与口径审计

冻结日期：2026-10-12（实施 AI 按《price-action-lab_整合重构完整TODO.md》S0-01 执行）
审阅/冻结提交：`02154d7327530f699be23017534d6157bd646f5a`（与本地 HEAD 一致，无后续差异）

## 1. 目的

Legacy 回测结果（FOCUS_V1 随机5股）是本仓库唯一的量化证据。按任务书 F01/F09：
冻结旧结果与旧口径，禁止覆盖，新实验输出到独立目录。本文档说明每个旧收益指标
的计算方式，使后续重构能与旧结果做对照，而不是让旧数字无据可查。

## 2. 冻结产物清单（SHA256 全量见 legacy_freeze_manifest.json）

| 文件 | sha256 前12位 | 说明 |
|---|---|---|
| scripts/backtest_focus_random5.py | 4abf41bbcf1a | legacy 回测脚本（冻结时点） |
| data/reviews/FOCUS_V1_BACKTEST_RANDOM5_20261011.json | 9cc6fc581fcf | 34 笔交易结果 |
| docs/backtest-evidence/random5-walkforward.md | a49d6b51045c | 旧回测报告 |
| docs/integration/INTEGRATION_PLAN_20261012.md | 7da1663adcdc | 原整合方案 |
| README.md | 07f166f26980 | 仓库说明 |

注意：冻结 hash 对应提交 02154d7 时点。S0-06 已对回测脚本做了"取消静默异常"
修改（不影响已存 JSON 结果——该 JSON 由旧脚本产出且已冻结，不重算、不覆盖）。

## 3. 旧指标口径（复算确认）

**主指标（README 引用的"平均超额收益"）**：
```
per-stock: diff_i = (strat_ret_i - bh_ret_i) × 100   # 百分点
headline:  mean(diff_i) over 5 stocks
```
- 复算值：**-0.8681 个百分点**（5 股、34 笔）
- 与任务书 §1 复算值一致

**口径限制（F09，必须随引用声明）**：
- `strat_ret = Σ(exit-entry) / 区间起点价`——固定股数累计价差，不是满仓复利账户净值
- 无费用、无滑点、无资金约束、无组合层面风险调整
- 5 股为 seed=20261011 随机抽样，n=5 无统计意义
- 属于**开发数据**（已被反复查看），不能再充当样本外测试集（任务书 §5.4-1）

**允许的用途**：legacy vs corrected 的差异分解（任务书 S5-8）。
**禁止的用途**：任何"系统有效/无效"的正式结论、README 宣传口径。

## 4. 每股明细（冻结复算）

| sym | trades | winrate | avgR | sumR | strat_ret | bh_ret | diff(pp) |
|---|---|---|---|---|---|---|---|
| 688120 | 11 | 54.5% | 0.98 | 10.80 | +13.78% | +3.45% | +10.33 |
| （其余4股见 legacy_freeze_manifest.json per_stock 节） | | | | | | | |

## 5. 新实验输出目录约定

- 新回测/新实验一律写入 `data/experiments/<run_id>/`，带 RunManifest（任务书 §4）
- `data/reviews/` 只存放已冻结的历史产物，不追加新文件
- 复现本审计：`python .audit/freeze_legacy.py`（重算并覆盖写 manifest，脚本本身已提交）
