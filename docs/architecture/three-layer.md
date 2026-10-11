# 三层架构：bar-counting → qualification → actionability

> 来源：`src/strict_pa_detector.py`、`src/strict_pa_qualification.py`、`src/strict_pa_actionability.py`
> 设计评审：Phase 4.2-4.8（`data/reviews/` 原始档案）

## 为什么需要三层

Proxy（LLM 凭 swing 结构报信号）看着丰富，但 strict 对比后大量是低质量噪音。
三层架构的目标：**每个进入生产的信号都能回答"它在哪根bar、为什么成立、什么情况下失效"**。

```
raw K线
  │
  ▼ ① bar-counting（纯数学）
  │   H1/H2/L1/L2 计数, prior_bar=自然前一根
  │   零生产依赖: 不 import 任何生产模块
  │
  ▼ ② qualification（资质审核）
  │   direction arbitration   方向互斥（同bar双向信号只能留一个）
  │   pullback significance   回调深度 ≥ 0.3×ATR 才算显著
  │   range middle demotion   所有phase下, 区间中段信号降级
  │   bar size / doji         信号棒过小/doji 扣分
  │   H1-H2 intervening       H1与H2之间需有真实间隔
  │   ⚠ 不修改 bar counting 定义, 只做过滤
  │
  ▼ ③ actionability（可执行性, 9维打分）
      triggered=+8 / boundary=+6 / signal_bar_strength / momentum
      quality / recency / count / middle_penalty=-4 / doji_penalty=-2
      KB 裁决:
        same-direction triggered > waiting (hard)
        strong_breakout → direction hard rule
        weak_breakout   → bonus only
        failed_breakout_risk → prefer reverse
        two-sided range → ≥3 margin 才 scored single actionable
        tie / transition → manual_review（宁可不出信号）
```

## Proxy vs Strict 对比结论（Phase 4.2-4.6）

- Proxy 信号量 >> Strict 信号量，但四象限分析显示大量 proxy 信号在 strict 口径下无 bar-counting 支持
- Qualification 过滤后信号量下降约一半，质量提升
- Actionability 层后，20 个 M8 actionable 候选因 base_regime=transition 被阻塞——**这是设计出来的保守，不是 bug**

## 防幻觉设计（系统事实约束 LLM）

1. **系统价格层接管 entry/stop/TP**（`system_price_builder.py`）：LLM 不再是价格源；6 种信号类型各有独立定价规则
2. **结构点验证**（`system_structure_builder.py`）：swing 高低点从真实 K 线检测，LLM 伪造结构点偏差 >30% → 置零
3. **报告措辞约束**：TRADE_READY=0 时禁止无条件动作指令（"轻仓试多"被自动改写为条件式）
4. **证据 schema**：每种信号必须提供结构证据字段（L2 需 LH1/LH2，wedge 需 push_1/2/3，tr_fade 需 range_high/low/position）
