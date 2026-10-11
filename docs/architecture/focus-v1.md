# 聚焦架构 v1 — 双核四结构 + 区间开关（A股30m专用）

- 日期：2026-10-11
- 决策人：用户拍板（方案A + 只做A股 + 只做30分钟）
- 依据：wiki/sources/article-20200818-brooks-10-best-pa-patterns.md + encyclopedia-al-10-best-setups.md
- 性质：架构级收敛（11 live信号 → 5结构6键），非增量优化

## 一、为什么聚焦

旧架构 11 个 live 信号 + 18 键注册表 + 多市场多时间框架，维护面太大、信号定位模糊。
Brooks 10 大形态的底层只有两种力量：**延续**与**反转**。聚焦后每个信号有明确的
概率-盈亏比定位，其余全部降级为工具/过滤/研究层。

## 二、新信号面（5 结构 / 6 registry 键）

| 核 | 结构 | registry键 | 概率定位 | 入场逻辑 |
|----|------|-----------|---------|---------|
| 延续核 | H2牛旗/L2熊旗 | H2, L2 | 高胜率延续 | 回调后第二信号棒，顺势 |
| 延续核 | 突破 | breakout(新增) | 确认后≥60% | 大区间棒收在前高上方+区间扩张>1.2ATR+收在棒极端（精选标准，过滤75%假突破） |
| 反转核 | 楔形三推 | wedge | 40%胜率换≥2:1 | 三推至通道线，TBTL最小目标 |
| 反转核 | 最终旗形 | final_flag | 40%胜率换≥2:1 | 趋势末端旗形，TBTL最小目标 |
| 区间核(开关) | 区间反转 | tr_fade | 区间内高胜率 | 仅range regime+区间宽度≥2.5ATR才激活 |

## 三、降级/砍掉

| 旧信号 | 处置 | 理由 |
|--------|------|------|
| H1/L1 | 降级：不出信号（保留bar-counting研究） | Brooks：首次回调概率低，H2/L2才是经典入场 |
| climax_reversal | 降级 | 反转核已由wedge+final_flag承担，重叠 |
| double_bottom/top | 保持disabled | 自迭代#1已证伪（13/13亏损-10.4R） |
| measured_move | 工具层：只算目标价，不生成信号 | KB确认为measurement_tool |
| MTR/Magnets | 工具层 | 算目标位用，不是独立入场信号 |
| eighty_twenty | 保持disabled(CONTEXT_FACTOR) | 已是上下文因子 |
| 开盘反转 | 不实现 | 日内形态，A股T+1不适配 |
| 加密货币2只 | config清空 | 只做A股 |
| 通用fallback提示 | 删除 | 无形态=观望，不造噪音信号 |

## 四、Channel 过滤器（75%规律）

通道线触碰75%反转/25%突破成功 →
1. 突破信号只做"精选突破"（区间扩张+收在极端+越过前高），等价于只做那25%
2. 强趋势期(confidence≥0.7)禁止非楔形/非最终旗形的逆势信号（H2/L2本就顺势，tr_fade本就range门控，此条防未来漂移）
3. wedge/final_flag的反转入场天然发生在通道线极端，与75%规律同向，不拦

## 五、 enforcement 设计

- 新增 src/focus_config.py：单一事实源（LIVE_SIGNALS集合+过滤器开关+市场/时间框架声明）
- signal_registry.py：enabled标志与focus_config对齐，自检校验
- signal_predictor.py：候选池由focus_config驱动；tr_fade加宽度门控；新增_is_breakout_entry；删fallback
- run_strategy.py：加密货币watchlist清空后循环自然跳过（保留代码路径）
- config.json：watchlist.加密货币=[]（大盘指数sh.000001保留为市场环境上下文，非交易标的）

## 六、验收标准

1. registry enabled集合 == {H2,L2,wedge,final_flag,tr_fade,breakout}
2. predict_signals不再产生fallback信号、measured_move信号、H1/L1信号
3. tr_fade在窄区间(<2.5ATR)不触发
4. breakout检测：强突破合成数据触发；弱突破(收盘不极端)不触发
5. 既有测试套件不红（依赖旧信号的测试按新口径更新）
