# MES 实战复盘日记（2025-08 ~ 2026-03）

## 元信息
- 作者：huangzongprice
- 日期跨度：2025-08-06 ~ 2026-03-05（约 120 个交易日）
- 文件数量：~150（含 Gemini AI 辅助标注版本）
- 原始位置：`raw/books/huangzongprice/MES2*`

## 一句话摘要
huangzongprice 的 MES（Micro E-mini S&P 500）日线实战复盘日记——Brooks 价格行为学在真实市场中的每日应用记录，包含逐棒标注、MC 评分、交易执行与 R 倍数追踪，是 Brooks PA 实操层面最完整的个人交易日志。

## 核心内容

### 复盘结构（每日固定格式）
1. **日型标题**：用 Brooks 术语标注当日核心市场特征（如 "bear trend from the open then HL MTR"、"wedge bottom then HL MTR"、"trading range all day"）
2. **市场环境指标**：
   - `45minTR` / `5min-XX%TR`：多时间框架交易区间百分比
   - `ATM Straddle ~0.XX%`：ATM 跨式期权定价作为波动率代理指标（正常 0.55-0.68%，<0.4% 为 "Chop"）
3. **MC 评分流水线**：对关键棒段执行 10+2 评分
4. **逐棒标注**：B1, B2... 标注每根 K 线的 PA 解读（AIL/AIS, H1/L1, H2/L2, MC, TBTL, climax 等）
5. **交易记录**：入场棒号 + 方向 + 订单类型（STP/LMT/BTC/STC）+ R 倍数结果
6. **Gemini 补充分析**（部分文件）：AI 对关键决策点的独立分析（中英混合，标注 `gemini`）
7. **交易哲学引用**："Best Loser Wins"（Tom Hougaard）+ 马太福音 6:21

### 交易执行统计特征（跨 ~120 日样本）
- **多时间框架执行**：1min / 5min / 15min / 45min 混合使用
- **入场方式**：以 STP（Stop）为主，辅以 LMT（Limit）、BTC（Buy The Close）、STC（Sell The Close）
- **R 倍数范围**：典型单笔 -1R ~ +4R，偶有 +8R（SC2 复盘系统记录）
- **胜率模式**：符合 Brooks 40-60 规则，多数交易在 -1R/+1R/+2R 区间分布
- **连胜/连败处理**："Best Loser Wins" 哲学指导——接受小亏是大盈的前提

### MC 10+2 评分清单（出现在每日复盘中）
```
MC 10+2:
-5%  K线形态
-5%  Cprior H/L（前收盘相对位置）
-5%  十字星
-10% BO标记/市场体制
-5%  价格控制（swing point）
+5%  1ABR
+5%  时间控制（leg2 完成度 55-65%）
```
这是 Brooks 背景分析的 Pine Script 量化版在手工复盘中的对照使用。

### Gemini AI 协作模式
- **角色**：作为独立第二分析师，huangzongprice 先做标注，Gemini 再独立分析同一棒段
- **覆盖内容**：入场逻辑验证、K 线形态解读、陷阱识别（Bull Surprise/Bear Trap/Failed Breakout）
- **典型分析示例**：
  - "H1：C 收盘位置/长影线 → Rule #5 否决"
  - "B18-B22 Complex Pullback → OB H1 → Doji Outside Bar STP"
  - "B28 Leg 2 → TTR（Tight Trading Range）→ Limit Order 主导"
- **语言**：中英混合，Brooks 术语保持英文，解读用中文

## 市场分型统计（日型频率）

从标题和内容可归纳出 huangzongprice 遇到的常见日型：

| 日型 | 典型标题 | 频率感知 |
|------|---------|---------|
| 开盘趋势日 | "bull/bear trend from the open" | 高 |
| 高潮反转日 | "climactic reversal then TR" | 中 |
| 楔形反转日 | "wedge bottom/top then HL/LH MTR" | 中高 |
| 全天区间日 | "trading range all day" | 高 |
| 趋势区间混合 | "trend trading range all day" | 中 |
| 突破失败日 | "breakout then reversal" | 中 |
| 趋势恢复日 | "TR then small pullback bull trend" | 中 |
| 开盘反转日 | "opening reversal" | 低 |

> 注：以上为从文件标题和内容片段中归纳，非 huangzongprice 本人的精确统计。

## 提取出的新概念

以下概念在现有 Wiki 中未被充分覆盖，源自本复盘日记的实战观察：

- [[journal-huangzongprice-mes-reviews]] — MES 复盘方法论：每日固定流程与多时间框架标注
- [[rs-scoring]] — MC 10+2 评分清单：Brooks 背景分析的量化速查表
- [[atm-straddle-gauge]] — ATM 跨式期权作为日内波动率环境代理
- [[corpus-mes-daily-reviews]] — 日型分型：开盘趋势/高潮反转/楔形反转/全天区间/趋势区间混合
- [[emotions-trading]] — Best Loser Wins 交易哲学：接受小亏
- [[journal-huangzongprice-mes-reviews|Gemini AI copilot]] — Gemini AI 作为独立交易复盘协作者的模式

## 与现有知识的冲突

（无直接冲突——本日记是 Brooks 理论的实战验证，而非理论挑战）

## 价值评估

这是目前 Wiki 中**唯一一份完整的 Brooks PA 实战交易日志**。其他来源（课程笔记、书籍摘要、代码分析）覆盖了理论和量化实现，但缺少「在真实市场中一根一根 K 线做决策」的过程记录。核心价值：

1. **实战验证**：Brooks 理论在 MES 5-min 上的实际表现
2. **MC 评分对照**：10+2 评分清单在手工复盘中的真实使用
3. **交易心理**：R 倍数追踪 + "Best Loser Wins" 哲学的实际落地
4. **AI 协作**：Gemini 作为复盘协作者的早期实践模式
5. **时间序列**：半年连续复盘形成的市场分型直觉
