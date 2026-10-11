---
title: "布鲁克斯信号类型系统"
phase: [trend, range, breakout, transition]
signal_types: [h2-entry, l2-entry, wedge, pullback-entry, reversal-entry, flag]
tags: [bear, brooks, 信号, diff, 多头]
difficulty: intermediate
related: [h1-l1-signal, h2-l2-signal, btc-stc, wedge-signal, wedge-flag, post-climax-reversal, tbtl, double-pattern, tr-fade, atr-scaling, bar-close-position, trading-range-quality, wedge-gravity-dual-core, fsm-market-cycle, article-brooks-pa-verification, README-summary, guide-btc-backtest, article-huangzongprice-pa-shape-audit]
char_count: 2000
---
# 布鲁克斯信号类型系统

## 一句话定义
Al Brooks 价格行为学中定义的趋势/区间/反转三类 16 种可编程入场信号。

## 核心要点
- 分三大类：趋势延续信号（H1/H2/L1/L2）、反转信号（楔形/高潮/双底双顶）、区间信号（TR Fade）
- 严格多空对称设计：每个多头信号对应一个空头版本
- 代码实现中仅包含 16 种白名单信号（`VALID_PA_SIGNAL_VALUES`），Brooks 原著的 High 4 / Low 4 / Trouble Top 等**尚未代码化**
- 所有信号均可追溯至 Brooks 原著定义，本文档仅覆盖已实现的子集

## 趋势延续信号

| 多头 | 空头 | 核心逻辑 |
|------|------|---------|
| [[h1-l1-signal|bull_h1]] | bear_l1 | 趋势回调/反弹中第一根突破前高/前低的K线 |
| [[h2-l2-signal|bull_h2]] | bear_l2 | 两腿回调/反弹后更高低点/更低高点，收盘须符合方向 |
| [[btc-stc|bull_btc]] | bear_stc | AIL/AIS确认后连续强趋势K线，收盘近端点 |

## 反转信号

| 多头 | 空头 | 核心逻辑 |
|------|------|---------|
| [[wedge-signal|bull_h3_wedge]] | bear_l3_wedge | 三推后楔形顶/底，信号K近EMA |
| [[wedge-flag|bull_wedge_flag]] | bear_wedge_flag | 旗杆+楔形收敛，近EMA |
| [[post-climax-reversal|bull_post_climax]] | bear_post_climax | 高潮K后反转，需[[tbtl|TBTL]]完成确认 |
| [[double-pattern|bull_double_bottom]] | bear_double_top | 两底/两顶价差≤0.5 ATR，H2/L2变体 |

## 区间信号

| 多头 | 空头 | 核心逻辑 |
|------|------|---------|
| [[tr-fade|bull_tr_fade]] | bear_tr_fade | 达标后，在第3–4次边界测试时逆势入场 |

## 与相关概念的关系
- [[atr-scaling]]：所有信号的深度/价差阈值均以ATR归一化
- [[bar-close-position]]：H2/L2、BTC/STC、双底/双顶均校验收盘位置
- [[tbtl]]：Post Climax 的唯一确认机制
- [[trading-range-quality]]：TR Fade 的前置条件
- [[wedge-gravity-dual-core]]：本信号体系在 WG V1.5 脚本中的量化实现——双核架构（硬规则+软评分）
- [[fsm-market-cycle]]：FSM 四状态周期判定是 Brooks「市场阶段」理论的量化版本

## 实战应用
实盘中通过 `GET /api/pa_signal_types` 获取白名单；前端对未知信号类型输出 `[PA校验]` 警告，仅白名单内信号进入历史扫描和实时面板。

## 来源支撑
- [[article-brooks-pa-verification]]
- [[README-summary]]（MES 5分钟策略的 7 大入场信号，存在映射关系）
- [[guide-btc-backtest]]（BTC 回测指南 — 7 大信号在 BTC 市场的实操参数和优先级）
- [[article-huangzongprice-pa-shape-audit]] — 20 种信号的书-码 5 维度对照验证，标注了每类信号的 major_diff/minor_diff 等级

## 矛盾与待验证
- Brooks 原著的 High 4 / Low 4（第4次测试）在当前代码中**未实现**，与 [[tr-fade|TR Fade]]（第3–4次测试）存在概念重叠但未被代码覆盖
- Trouble Top 等其他 Brooks 原著信号类型未找到代码对应，可能被合并到其他信号或刻意省略
- **全量形态审计（major_diff × 14, minor_diff × 2）**： 对本 catalog 中全部 16 种信号进行了 5 维度"书本 vs 实现"对照，发现所有形态均存在差异。见 [[article-huangzongprice-pa-shape-audit]] 了解每项信号的详细对照。
