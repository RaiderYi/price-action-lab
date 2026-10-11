# Bar Counting 严格计数规则

> 来源：`src/bar_counting_detector.py`（Phase 4.1，零生产依赖）、`knowledge/concepts/h2-l2-signal.md`、`knowledge/concepts/h2-l2-state-machine.md`

## 核心定义（KB 确认版）

**H1/H2**（多头回调中的计数）：
- **H1** = bull pullback 中第一次 `high > prior_bar.high` 的K线（自然前一根，不跳过 inside bar）
- **H2** = 第二次满足条件的K线（两次尝试之间需有间隔，防连续触发多计）
- 计数方向由 context 决定（bull pullback 只数 H）

**L1/L2**（空头反弹中的计数）：
- **L1** = bear rally 中第一次 `low < prior_bar.low`
- **L2** = 第二次满足条件的K线

**关键规则**：
- outside bar → context-directed 单向计数
- 无硬性触发过期（no hard trigger expiry）
- H4+ → extended_count_warning（过度计数=趋势过强，回调入场风险大）
- 触发判定用 **high/low**（bar counting），非 close-based

## 为什么 H2/L2 是唯一 strict 血统

Brooks："市场制造混乱→两次反转尝试失败→原趋势恢复→逆势方快速退出→顺势加速。"

- **首次尝试（H1/L1）胜率不足**——大多数回调在一次反转尝试后就恢复，H1 给出的入场点质量不稳定
- **第二次尝试（H2/L2）是经典入场**——两次失败后逆势方认输，顺势方加速
- 所有小型双顶/双底本质上是 L2/H2（形态只是计数的表达）

Focus v1 决策：H1/L1 降级不出信号（保留研究层），**H2/L2 是延续核的唯一 strict 入场**。

## 状态机

```
趋势(up) → bull_pullback → H1 → (未失效) → H2 → 触发: 突破H2信号棒高点
                              ↓ 失效
                          H2信号棒低点被破 → 计数作废, 回到 context 判定
```

## 测试数据铁律

连续满足条件的 bar 会自然累积计数（bar2=L1, bar3=L2...），L2 trigger 会立即触发。
**测试数据中 L1/L2 的 low 序列必须设计间隙**（bar2 low > bar1 low，bar3 low < bar2 low 且中间至少1根不满足条件的 bar），否则预期计数值会因连续触发+多计而偏离。
