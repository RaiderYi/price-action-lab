---
title: "Playbook 六种玩法状态"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, failed-breakout]
tags: [playbook, 等待, 区间边缘, 楔形, 是否允许]
difficulty: intermediate
related: [playbook-engine, trend-strength-filter, tri-push-background, range-zone-positioning, article-background-v3-upgrade]
char_count: 1582
---
# Playbook 六种玩法状态

## 一句话定义
背景层 v3 的核心枚举——6 种互斥的玩法状态，告诉执行层当前应优先寻找哪类信号结构。

## 核心要点

### 状态编码
| 状态 | 含义 | 优先看 |
|------|------|--------|
| 0 等待/观望 | 没有清晰背景，任何方向风险都高 | 不交易 |
| 1 趋势突破延续 | 新突破、动能新鲜、趋势未成熟 | 突破后 follow-through、小回调后再破 |
| 2 顺势回调再进入 | 通道阶段、趋势健康、回调到合理位置 | H2/L2 |
| 3 区间边缘反转 | 明确震荡、上沿/下沿、中部过滤 | 假突破失败、边缘 H2/L2、边缘楔形 |
| 4 过渡期反转 | 趋势成熟、动能减弱、三推/楔形/失败突破出现 | 楔形、三推衰竭、反转确认棒、反转后 H2/L2 |
| 5 强趋势禁逆势 | 极强趋势、紧密通道、缺口驱动 | 仅顺势信号，反转结构全部降权或屏蔽 |

### 生成优先级（固定顺序）
```
1. 极强趋势拦截 (trendBlock) → playbook=5
2. 区间判断 (phaseIsRange + not rangeMiddle) → playbook=3
3. 过渡判断 (phaseIsTransition) → playbook=4
4. 新突破判断 (phaseState==NEW_BREAKOUT) → playbook=1
5. 通道判断 (phaseState==CHANNEL) → playbook=2
6. 否则 → playbook=0 等待
```

### 对执行层的指令
| playbook | H2/L2 允许? | 楔形允许? | 三推执行? | BTC/STC 允许? |
|----------|------------|----------|----------|-------------|
| 0 等待 | 否 | 否 | 否 | 否 |
| 1 趋势突破 | 次优 | 否 | 否 | **是** |
| 2 顺势回调 | **是** | 否 | 否 | 是 |
| 3 边缘反转 | 是 | **是** | 是 | 否 |
| 4 过渡反转 | 是（反转后） | **是** | **是** | 否 |
| 5 禁逆势 | 否 | 否 | 否 | **是** |

## 与相关概念的关系
- [[playbook-engine]]：Playbook Engine 的枚举输出就是 playbookState
- [[trend-strength-filter]]：trendBlock 直接触发 playbook=5
- [[tri-push-background]]：三推出现触发 playbook 从 2→4 的切换
- [[range-zone-positioning]]：区间边缘触发 playbook=3

## 实战应用
执行层不再只问 `allowLong?` / `allowShort?`，而是问：
- 是否允许 H2/L2？→ playbook=2 或 3
- 是否允许楔形？→ playbook=3 或 4
- 是否允许三推执行？→ 不是 playbook=5 + 三推质量过关 + 玩法支持反转

## 来源支撑
- [[article-background-v3-upgrade]]

## 矛盾与待验证
- 本文为设计稿，6 种状态的互斥性和边界的完整性在代码实现前无法验证。
- playbook=3 区间边缘反转与 playbook=4 过渡期反转在区间+三推同时出现时可能有歧义——按固定优先级判断，但实际场景是否需要更精细的判断待验证。
