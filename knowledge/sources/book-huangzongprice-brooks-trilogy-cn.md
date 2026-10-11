# Al Brooks 三部曲 木羊中文译本 + 分析背景

## 元信息
- 作者：Al Brooks（原著），木羊（翻译）
- 日期：原著 2011-2012，译本出版约 2013-2014
- 原始位置：
  - `raw/books/huangzongprice/价格行为交易之趋势篇 中文 木羊（修订版）.md`
  - `raw/books/huangzongprice/价格行为交易之反转篇 中文 木羊（党生版）.md`
  - `raw/books/huangzongprice/价格行为交易之区间篇 中文 木羊.md`
  - `raw/books/huangzongprice/分析背景要走哪几步.md`
- 提取方式：pdftotext
- 文件规模：趋势篇 3180 行 / 反转篇 3356 行 / 区间篇 3623 行 / 分析背景 89 行

## 一句话摘要
⚠️ **OCR 全部失败** — 四份 PDF 均为扫描版，pdftotext 提取后中文内容全部乱码，仅残留少量英文术语碎片。与之前 ingest 的 `book-brooks-trends`（趋势篇初版）问题相同。

## 核心论点

### 内容概况
四份资料构成了 Brooks 价格行为学的完整中文译本体：
1. **趋势篇（修订版）** — 3180 行，目录可辨认 26 章结构，正文中文全部丢失，仅残留英文术语索引（always in、barbwire、breakout、climax、double top/bottom、EMA gap bar 等）
2. **反转篇（党生版）** — 3356 行，目录可辨认 25 章 + Globex/盘前盘后章节，正文中文全部丢失，残留部分英文术语和少量可读段落碎片
3. **区间篇** — 3623 行，目录可辨认 32 章（含突破/磁力/回调/订单管理等跨卷内容），正文中文全部丢失
4. **分析背景要走哪几步** — 89 行，完全损毁，仅残留 "EMA20"、"Market Cycle"、"Mermaid" 等碎片

### 与已有内容的互补
- Brooks 三部曲的**英文原版**已在之前 ingest 中消化完成：
  - 趋势篇 → [[book-brooks-reading-price-charts]]（英文原版）+ [[book-brooks-reading-price-charts-cn]]（机翻版）
  - 反转篇 → [[book-brooks-reversals]]（英文原版 + Al Brooks 反转篇英文版）
  - 区间篇 → [[book-brooks-trading-ranges]]（英文原版 + 中文木羊版已从 al-brooks-series 目录单独 ingest）
- 中文木羊译本的独特价值在于术语翻译对照，但当前 PDF 质量无法提取
- 之前 ingest 的 `book-brooks-trends`（中文趋势篇初版）同样是 OCR 失败，后被英文原版替代

## 提取出的新概念
无 — 文本不可读，无法提取新概念。

## 与现有知识的冲突
无 — 无法阅读正文，无法进行内容比对。

## 待办
- 若能获取这四份 PDF 的**原生文字版**（非扫描版），可重新提取中文术语体系
- 木羊译本的中文术语对照表（如 "always in → 总在场内"）具有独立参考价值
- 当前 Wiki 已从英文原版 + Brooks 课程笔记覆盖了这三卷的核心内容，中文译本属于锦上添花而非必要
