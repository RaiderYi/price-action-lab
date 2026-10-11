# TranscriptSegment Schema 定义

> **用途**: 将 16 个 `ch37_raw.txt` ~ `ch52_raw.txt` 原始转录拆分为可检索的独立知识片段。
> **版本**: v1.0
> **日期**: 2026-05-27
> **相关计划**: `.hermes/plans/2026-05-27_kb-engine-v2-architecture.md` Phase 1

---

## 一、原始文件抽样分析

### 1.1 文件清单

| 文件 | 视频数 | 分隔符数 | 估计字符数 | 对应章节主题 |
|------|--------|----------|------------|-------------|
| ch37_raw.txt | 2 (A,B) | 4 | ~16K | 市场基础：市场在做什么、市场周期 |
| ch38_raw.txt | 4 | 8 | ~22K | 趋势/区间深入 |
| ch39_raw.txt | 4 | 8 | ~20K | 市场结构细节 |
| ch40_raw.txt | 5 | 10 | ~26K | 通道与交易区间 |
| ch41_raw.txt | 4 | 8 | ~28K | H2/L2 入场信号 |
| ch42_raw.txt | 3 (A,B,C) | 6 | ~20K | 弱势突破、高潮、微型通道 |
| ch43_raw.txt | 4 | 8 | ~22K | 突破/回调入场 |
| ch44_raw.txt | 4 | 8 | ~24K | 测量移动 |
| ch45_raw.txt | 5 | 10 | ~28K | 楔形、图表形态 |
| ch46_raw.txt | 5 | 10 | ~26K | 通道与旗形 |
| ch47_raw.txt | 4 | 8 | ~22K | 三角形、复杂形态 |
| ch48_raw.txt | 11 (A-K) | 22 | ~63K | 开盘分析（最大文件） |
| ch49_raw.txt | 5 | 10 | ~28K | 止损与风险管理 |
| ch50_raw.txt | 5 | 10 | ~30K | 仓位与盈亏比 |
| ch51_raw.txt | 4 | 8 | ~24K | 交易心理与纪律 |
| ch52_raw.txt | 2 (A,B) | 4 | ~15K | 避免大亏、环境变化 |
| **合计** | **71** | **142** | **~419K** | |

对应 4 个结构化摘要的章节划分：

| 摘要文件 | 覆盖章节 | 对应原始文件 |
|----------|----------|-------------|
| 01-market-structure.md | 37-40, 48 | ch37~ch40, ch48 |
| 02-entry-signals.md | 41-44 | ch41~ch44 |
| 03-chart-patterns.md | 45-48 | ch45~ch48 (部分) |
| 04-trade-management.md | 49-52 | ch49~ch52 |

### 1.2 文件内部结构分析

每个 `chXX_raw.txt` 的结构：

```
(空行)
============================================================
  Video 37A
============================================================
<PPT 转录内容，每行一个短句/要点>
============================================================
  Video 37B
============================================================
<PPT 转录内容...>
```

**关键特征：**

1. **分隔符**: `====...====` 包围的 `Video XX[A-K]` 行标记视频段落边界
2. **内容格式**: 每行一个中文短句（5-30 字），来源于 PPT 幻灯片逐页翻译转录
3. **无段落结构**: 所有行平铺，没有标题层级、段落合并或章节标记
4. **主题漂移**: 单个视频内通常覆盖多个子主题，靠人工或 LLM 识别边界

### 1.3 四个代表性文件详细分析

#### ch37_raw.txt (426行, ~16K chars, 2个视频)

- **Video 37A** (行3-173): 封面/致谢 → "市场在做什么？" → 多头/空头市场行情 → 交易区间 → 构建交易 → 两个时间周期
- **Video 37B** (行175-426): "使用市场周期" → 二元决策 → 多头/空头通道（紧密/宽幅）→ 交易区间做多做空区域 → 40-60 规则 → 默认目标

**结构特征**: 前几行是译者的致谢和声明（非课程内容），后续是密集的 PPT 要点。每个视频内约有 8-12 个可识别的子主题。

#### ch42_raw.txt (471行, ~20K chars, 3个视频)

- **Video 42A** (行3-173): "弱势突破意味着交易区间即将来临" → 交易区间行为 → 测量缺口 vs 衰竭缺口 → 弱势和强势的多空双方
- **Video 42B** (行175-约330): "微型通道可以是高潮" → 主要高潮反转 → 抛物线楔形
- **Video 42C** (行约331-471): 连续高潮、小高潮、交易区间突破

**结构特征**: 三个视频主题连贯，围绕"突破→交易区间→高潮"展开。每5-15行构成一个小知识点。

#### ch48_raw.txt (1578行, ~63K chars, 11个视频) — 最大文件

- **Video 48A**: 开盘反转、一天三部分、开盘突破概率
- **Video 48B**: 最重要的规则、为什么在开盘交易
- **Video 48C**: 开盘区间、早期反转
- **Video 48D**: 突破模式(BOM)、18根K线区间突破
- **Video 48E**: 昨日高低点突破、二次入场
- **Video 48F**: 早期旗形、缺口开盘
- **Video 48G**: 跳空高开/低开详细分析
- **Video 48H**: 趋势性交易区间日
- **Video 48I**: 尾盘交易策略
- **Video 48J**: 收盘买入/卖出(BTC/STC)、磁力效应
- **Video 48K**: 多头/空头陷阱、高时间周期支撑阻力

**结构特征**: 文件极长，每个视频都有明确的单一主题（标题即第一行内容），是内容最丰富的一章。片段拆分粒度需要更细。

#### ch52_raw.txt (326行, ~15K chars, 2个视频)

- **Video 52A** (行3-163): "需要有规则来避免大额亏损" → 亏损源于错误 vs 坏运气 → 三种保护类型 → 趋势最终让人失望 → 逐步加仓 → 依赖止损
- **Video 52B** (行165-326): "如果市场环境前提改变，改变交易风格" → 被套交易者 → 深度回调应对 → 强势突破的第一次回调

**结构特征**: 主题高度聚焦于交易管理和风险控制。每个视频内子主题少(3-5个)，但论述较深入。

### 1.4 内容类型总结

从抽样分析中识别出以下内容类型：

| 类型 | 示例 | 出现频率 | 处理方式 |
|------|------|----------|---------|
| 课件标题行 | "市场在做什么？" | 每视频开头 | 作为 `topic` 字段 |
| 规则性陈述 | "最重要的规则：价格即是真相" | 高频 | 核心内容，标注为 rule 类 |
| 概率数据 | "有60%的概率会先下跌X个ticks" | 中频 | 提取到 `probabilities` 字段 |
| 策略指导 | "只买入做多，尤其是在回调做多" | 高频 | 核心内容，标注为 strategy 类 |
| 概念解释 | "高潮是价格向上或向下的加速运动" | 中频 | 核心内容，标注为 definition 类 |
| 图表描述 | "16根K线的多头微型通道" | 中频 | 附带图片引用(如有) |
| 非课程内容 | 译者致谢、版权声明 | 仅 ch37 开头 | 标记为 meta，检索时排除 |
| 数字列表 | "1. 不要亏钱" | 低频 | 保留原始格式 |

---

## 二、片段拆分粒度建议

### 2.1 拆分单元

**推荐：按视频段落内的子主题拆分**，而非按视频整体拆分。

理由：
- 单个视频平均 ~6K chars (ch48 除外)，作为检索单位仍太大
- 视频内部有清晰的主题切换，天然存在子主题边界
- 检索系统需要精确匹配，300-800 chars 的片段粒度最佳

### 2.2 建议片段大小

| 粒度 | 字符数 | 适用场景 | 预估总片段数 |
|------|--------|----------|-------------|
| 细粒度（子主题） | **200-600 chars** | 精准概念检索 | ~800-1200 |
| 中粒度（主题组） | 600-1500 chars | 上下文理解 | ~350-500 |
| 粗粒度（视频段落） | 1500-5000 chars | 全量阅读 | ~130-150 |

**推荐方案**：以细粒度（200-600 chars）为主，确保每个片段聚焦单一概念或知识点。相邻片段通过 `prev_id` / `next_id` 保持连贯性。

### 2.3 拆分边界识别规则

建议使用以下启发式规则 + LLM 辅助识别子主题边界：

1. **标题行**: 以名词短语开头的独立行（如"多头市场行情：它在做什么？"）→ 新片段起点
2. **主题转折**: 连续3行以上讨论不同概念时 → 新片段起点
3. **规则列表**: "规则："、"第一步"、"第二"等显式序列标记 → 合并为一个片段
4. **对照结构**: "多头...空头..."的对照行 → 合并为一个片段
5. **最小片段**: 少于 100 chars 的片段合并到前一个或后一个
6. **最大片段**: 超过 800 chars 的片段在逻辑边界处拆分

### 2.4 预期产出

基于 71 个视频 × 平均 8-15 个子主题，预计产出 **800-1100 个 TranscriptSegment**。

---

## 三、TranscriptSegment Schema 完整定义

### 3.1 YAML Frontmatter 字段

```yaml
# ============================================================
# TranscriptSegment Schema v1.0
# 每个字段标注：(类型) 说明 [是否必填] [示例值]
# ============================================================

# --- 标识字段 ---

id: "ch42-v42b-weak-breakout"
  # (string) 唯一标识符，格式: ch{章号}-v{视频号}{字母}-{主题slug}
  # [必填] 用于数据库主键和引用链接

source_file: "ch42_raw.txt"
  # (string) 来源原始文件名
  # [必填] 用于溯源和文件定位

source_video: "Video 42B"
  # (string) 来源视频段落标识
  # [必填] 格式 "Video {数字}{字母}"

chapter: 42
  # (integer) 章节编号
  # [必填] 范围 37-52

chapter_title: "图表形态"
  # (string) 章节所属大类（对应 4 个结构化摘要的主题）
  # [必填] 枚举: "市场结构"|"入场信号"|"图表形态"|"交易管理"

segment_index: 3
  # (integer) 片段在源视频内的序号（从 1 开始）
  # [必填] 用于排序和相邻导航

line_start: 175
  # (integer) 在源文件中的起始行号
  # [选填] 方便定位原始内容

line_end: 210
  # (integer) 在源文件中的结束行号
  # [选填]

# --- 主题字段 ---

topic: "弱势突破与交易区间的关系"
  # (string) 片段主题（中文，简洁描述）
  # [必填] 15-50 字，用于列表展示

topic_en: "weak-breakout-and-trading-range"
  # (string) 主题英文 slug
  # [必填] 小写，连字符分隔，用于 URL 和程序引用

video_title: "弱势突破意味着交易区间即将来临"
  # (string) 所属视频的标题（源文件中分隔符后的第一行内容）
  # [必填] 提供更上层的上下文

content_type: "strategy"
  # (string) 内容类型分类
  # [必填] 枚举: "rule"|"strategy"|"definition"|"probability"|"observation"|"instruction"|"meta"

# --- 分类字段 ---

phase:
  - "breakout"
  - "range"
  # (array of string) 关联的市场阶段
  # [必填] 枚举(可多选): "trend"|"range"|"breakout"|"transition"|"opening"|"closing"|"any"
  # "trend" = 趋势行情, "range" = 交易区间, "breakout" = 突破, "transition" = 阶段转换
  # "opening" = 开盘阶段, "closing" = 尾盘阶段, "any" = 通用

signal_types:
  - "h2-entry"
  - "breakout-entry"
  # (array of string) 关联的信号/入场类型
  # [选填] 枚举(可多选):
  #   "h1-entry", "h2-entry", "l1-entry", "l2-entry",
  #   "breakout-entry", "pullback-entry", "reversal-entry",
  #   "limit-order", "stop-order", "scalp", "swing",
  #   "climax-reversal", "failed-breakout", "wedge-breakout",
  #   "opening-reversal", "trend-continuation", "gap-entry",
  #   "second-entry", "any-reason"

direction:
  - "long"
  - "short"
  # (array of string) 交易方向
  # [选填] 枚举: "long"|"short"|"both"|"neutral"

# --- 知识关联字段 ---

concepts:
  - "breakout-mechanics"
  - "failed-breakout-reversal"
  - "eighty-percent-rule"
  - "trading-range-dynamics"
  # (array of string) 关联的概念页文件名（不含 .md 后缀）
  # [选填] 对应 wiki/concepts/ 下的概念页面
  # 当前有 240 个概念页，选择最相关的 1-5 个

keywords:
  - "弱势突破"
  - "衰竭缺口"
  - "测量缺口"
  - "交易区间"
  - "深度回调"
  - "weak breakout"
  - "exhaustion gap"
  - "measured gap"
  - "trading range"
  # (array of string) 中英文检索关键词
  # [必填] 5-15 个关键词，覆盖中英文

related_segments:
  - "ch42-v42a-trading-range-behavior"
  - "ch48-v48d-breakout-mode"
  # (array of string) 关联的其他片段 id
  # [选填] 前置知识、后续深入、相关主题

# --- 元数据字段 ---

difficulty: "advanced"
  # (string) 难度级别
  # [必填] 枚举: "basic"|"intermediate"|"advanced"
  # basic = 新手可理解的基础概念
  # intermediate = 需要一定背景知识
  # advanced = 需要综合多个概念的深入内容

char_count: 450
  # (integer) 片段正文字符数（不含 frontmatter）
  # [必填] 自动计算

prev_id: "ch42-v42b-micro-channels"
  # (string) 前一个片段的 id（同一视频内）
  # [选填] 用于上下文导航

next_id: "ch42-v42b-climax-reversal"
  # (string) 后一个片段的 id（同一视频内）
  # [选填] 用于上下文导航

created: "2026-05-27"
  # (date) 片段创建日期
  # [必填]

updated: "2026-05-27"
  # (date) 最后更新日期
  # [选填]
```

### 3.2 Body 格式

片段正文采用 Markdown 格式，保持转录原文，仅做最小化格式化：

```markdown
弱势突破意味着交易区间即将来临。

突破可以成功（测量缺口）或失败（衰竭缺口）。

如果多头在空头趋势中获利：交易区间很可能即将来临。

在前低买入。如果逐步加仓的多头交易者通过在新低做多并以更低的价格逐步加仓可以获利，通道通常开始转变为交易区间。

弱势突破更可能是交易区间内的空头走势段，而非空头趋势的开始。

交易区间很可能出现，因此深度回调也很可能发生，即使后来变成了多头趋势也是如此。
```

**Body 格式规则：**

1. 保留原始中文文本，不做翻译或改写
2. 原文的短行用双换行分隔（增加可读性）
3. 如果在源文件中是连续的列表项，用 `- ` 前缀格式化
4. 对于明显的对照关系（多头 vs 空头），可用简单的 Markdown 表格组装（不常见，仅当原文是结构化对照时）
5. 不加额外的章节标题——所有元信息已在 frontmatter 中

---

## 四、Schema 字段映射速查表

| Frontmatter 字段 | 类型 | 必填 | 检索权重 | 说明 |
|-----------------|------|------|---------|------|
| `id` | string | ✓ | 标识 | 主键，格式 `ch{XX}-v{XX}{L}-{slug}` |
| `source_file` | string | ✓ | 标识 | 来源文件路径 |
| `source_video` | string | ✓ | 标识 | 来源视频段落 |
| `chapter` | integer | ✓ | 过滤 | 章节号 37-52 |
| `chapter_title` | string | ✓ | 过滤 | 四大类之一 |
| `segment_index` | integer | ✓ | 排序 | 视频内序号 |
| `line_start` | integer | | 溯源 | 源文件起始行 |
| `line_end` | integer | | 溯源 | 源文件结束行 |
| `topic` | string | ✓ | **高** | 中文主题（展示用） |
| `topic_en` | string | ✓ | 中 | 英文 slug（程序用） |
| `video_title` | string | ✓ | 中 | 所属视频标题 |
| `content_type` | string | ✓ | 过滤 | 内容类型分类 |
| `phase` | array | ✓ | **高** | 市场阶段（可多选） |
| `signal_types` | array | | **高** | 信号类型（可多选） |
| `direction` | array | | 中 | 交易方向 |
| `concepts` | array | | **高** | 概念页引用 |
| `keywords` | array | ✓ | **最高** | 中英文检索词 |
| `related_segments` | array | | 低 | 关联片段 |
| `difficulty` | string | ✓ | 过滤 | 难度分级 |
| `char_count` | integer | ✓ | 排序 | 片段大小 |
| `prev_id` | string | | 导航 | 前一片段 |
| `next_id` | string | | 导航 | 后一片段 |
| `created` | date | ✓ | - | 创建日期 |
| `updated` | date | | - | 更新日期 |

---

## 五、完整示例

以下是一个完整的 TranscriptSegment 文件示例（路径：`transcript-segments/ch42-v42b-weak-breakout.md`）：

```markdown
---
id: "ch42-v42b-weak-breakout"
source_file: "ch42_raw.txt"
source_video: "Video 42B"
chapter: 42
chapter_title: "图表形态"
segment_index: 1
line_start: 175
line_end: 205
topic: "弱势突破意味着交易区间即将来临"
topic_en: "weak-breakout-means-trading-range"
video_title: "弱势突破意味着交易区间即将来临"
content_type: "strategy"
phase:
  - "breakout"
  - "range"
  - "transition"
signal_types:
  - "failed-breakout"
  - "scalp"
  - "second-entry"
direction:
  - "both"
concepts:
  - "breakout-mechanics"
  - "trading-range-dynamics"
  - "failed-breakout-reversal"
keywords:
  - "弱势突破"
  - "交易区间"
  - "衰竭缺口"
  - "测量缺口"
  - "深度回调"
  - "weak breakout"
  - "trading range"
  - "exhaustion gap"
  - "measured gap"
  - "deep pullback"
related_segments:
  - "ch42-v42a-climax-identification"
  - "ch48-v48d-breakout-mode"
difficulty: "intermediate"
char_count: 385
prev_id: null
next_id: "ch42-v42b-measured-vs-exhaustion-gap"
created: "2026-05-27"
updated: "2026-05-27"
---

弱势突破意味着交易区间即将来临。

突破可以成功（测量缺口）或失败（衰竭缺口）。

如果多头在空头趋势中获利，交易区间很可能即将来临。在前低买入。如果逐步加仓的多头交易者通过在新低做多并以更低的价格逐步加仓可以获利，通道通常开始转变为交易区间。

弱势突破更可能是交易区间内的空头走势段，而非空头趋势的开始。交易区间很可能出现，因此深度回调也很可能发生，即使后来变成了多头趋势也是如此。

在交易区间的早期，大多数人应专注于做空信号。市场仍然始终看跌。任何做多都是刮头皮，直到形成更高低点的主要趋势反转。
```

---

## 六、枚举值完整列表

### 6.1 content_type 枚举

| 值 | 含义 | 示例 |
|----|------|------|
| `rule` | 交易规则/铁律 | "最重要的规则：价格即是真相" |
| `strategy` | 策略/方法论 | "在回调做多，在新高时部分止盈" |
| `definition` | 概念定义 | "高潮是价格向上或向下的加速运动" |
| `probability` | 概率/统计数据 | "有60%的概率会先下跌X个ticks" |
| `observation` | 市场观察/经验 | "交易区间有许多反转" |
| `instruction` | 操作指导/教程 | "在第三根连续的强势阴线收盘价附近做空" |
| `meta` | 非课程内容 | 译者致谢、版权声明等 |

### 6.2 phase 枚举

| 值 | 含义 |
|----|------|
| `trend` | 趋势行情（含多头趋势、空头趋势） |
| `range` | 交易区间（横盘震荡） |
| `breakout` | 突破阶段 |
| `transition` | 阶段转换（趋势→区间、区间→突破等） |
| `opening` | 开盘特定阶段 |
| `closing` | 尾盘特定阶段 |
| `any` | 适用于所有市场阶段 |

### 6.3 signal_types 枚举

| 值 | 含义 |
|----|------|
| `h1-entry` | H1 入场（第一次回调入场） |
| `h2-entry` | H2 入场（第二次回调入场，更高概率） |
| `l1-entry` | L1 入场（空头第一次反弹入场） |
| `l2-entry` | L2 入场（空头第二次反弹入场） |
| `breakout-entry` | 突破入场 |
| `pullback-entry` | 回调入场 |
| `reversal-entry` | 反转入场 |
| `limit-order` | 限价单策略 |
| `stop-order` | 止损单/市价单策略 |
| `scalp` | 刮头皮交易 |
| `swing` | 波段交易 |
| `climax-reversal` | 高潮反转 |
| `failed-breakout` | 失败突破 |
| `wedge-breakout` | 楔形突破 |
| `opening-reversal` | 开盘反转 |
| `trend-continuation` | 趋势延续 |
| `gap-entry` | 缺口入场 |
| `second-entry` | 二次入场（泛指） |
| `any-reason` | 任何理由入场（强势突破中） |
| `measured-move` | 测量移动目标 |

### 6.4 difficulty 枚举

| 值 | 含义 | 典型受众 |
|----|------|---------|
| `basic` | 基础概念，无需前置知识 | 入门学习者 |
| `intermediate` | 需要理解基本术语和概念 | 有基础的学习者 |
| `advanced` | 综合多个概念，需要实践经验 | 有经验的交易者 |

---

## 七、检索集成说明

### 7.1 检索权重

在语义检索 + 关键词检索的混合系统中，各字段的权重建议：

- **keywords** (权重 1.0): 中英文关键词，直接匹配
- **topic** (权重 0.8): 主题标题，概括性强
- **phase** (权重 0.7): 市场阶段过滤，精准缩小范围
- **signal_types** (权重 0.6): 信号类型过滤
- **concepts** (权重 0.5): 概念页交叉引用
- **content (body)** (权重 0.4): 全文语义相似度
- **chapter_title** (权重 0.3): 大类过滤

### 7.2 与现有知识库的关系

```
TranscriptSegment  ──concepts──→  wiki/concepts/*.md (概念页，240个)
                                  ↑ 双向引用：概念页可反向列出关联的片段

TranscriptSegment  ──chapter_title──→  结构化摘要 (01-04, 4个)
                                       ↑ 片段通过 chapter_title 归入 4 大类

TranscriptSegment  ←──id 引用──→  其他 TranscriptSegment
                                  ↑ prev_id/next_id 链式导航
                                  ↑ related_segments 交叉引用
```

---

## 八、实施建议

1. **拆分顺序**: 建议从 ch48（最大文件，内容最丰富）开始，验证 Schema 的覆盖度
2. **自动化**: 使用 LLM (如 Claude/GPT-4) 批量拆分，人工抽样校验
3. **概念关联**: 拆分完成后，反向更新 240 个概念页的 frontmatter，添加 `transcript_segments` 引用字段
4. **增量更新**: 每个片段独立为 `.md` 文件，便于 git diff 和增量索引
5. **质量检查**: 每个片段应能独立阅读理解，不依赖相邻片段即可传达核心知识点
