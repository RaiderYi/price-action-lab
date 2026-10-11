# 分析背景要走哪几步

## 元信息
- 作者：huangzongprice（个人方法论文档）
- 日期：未标注（基于引用的 Brooks 课程视频，推测 2025 年前后编写）
- 原始位置：`raw/books/huangzongprice/分析背景要走哪几步.md`
- 提取方式：pdftotext（扫描 PDF，严重乱码）
- 文件规模：89 行（极短的方法论文档）

## 一句话摘要
huangzongprice 的 Brooks 背景分析个人方法论——将 Brooks Trading Course 多节视频内容整合为 4 步分析流程 + Mermaid 流程图。

## 核心论点

### 文档性质
这不是 Brooks 原著翻译，而是 **huangzongprice 基于 Brooks 课程的个人知识整合**——将分散在多节视频中的「如何分析背景」方法论压缩为一页流程图。与已有的 [[article-20250519-brooks-context-4-pine]]（Pine Script 工程化落地）形成「方法论 → 代码实现」的上下游关系。

### 从残留碎片恢复的 4 步框架
```
Step 1 ──→ 参考: 02D（Momentum 动量分析）
Step 2 ──→ 参考: 19B
Step 3 ──→ EMA20 均线位置判断
Step 4 ──→ MM（Measured Move 测量走势）

然后进入 K 线分析：
  1. K 线形态判断
  2. 信号棒/入场棒识别
  3. K 线组合确认
  ──→ 参考: 08C + 08D（Candles, Setups and Signal Bars）
```

### 引用的 Brooks 课程视频
| 视频编号 | 主题 | 在分析流程中的角色 |
|---------|------|------------------|
| 02D | Momentum | Step 1：判断动能方向和强度 |
| 19B | （未知具体内容） | Step 2 |
| 12A | Market Cycle | 背景判断的核心——当前处于市场周期哪个阶段 |
| 16C | （未知具体内容） | 辅助判断 |
| 14D | （未知具体内容） | 辅助判断 |
| 08C | Candles, Setups and Signal Bars | K 线识别与信号棒判断 |
| 08D | Candles, Setups and Signal Bars（续） | 入场棒确认 |

### Mermaid 流程图
文件中包含一个 Mermaid 流程图（已乱码无法恢复），推测为 4 步分析流程的可视化表示。

## 提取出的新概念

### 已创建概念页
- [[brooks-four-step-context]] — huangzongprice 背景分析四步框架：动量→结构→均线→测量→K线

### 与已有概念的关系
| 本文框架 | 已有概念 | 关系 |
|---------|---------|------|
| Step 1 动量 | [[brooks-four-step-context]] (ctx1: S/R) | 不同框架——前者看动量，后者看 S/R |
| Step 3 EMA20 | [[twenty-gap-bars]]（20 缺口棒） | EMA 是 Brooks 核心均线，本框架将其作为独立步骤 |
| Step 4 MM | [[measured-move]] | 已有概念覆盖 |
| K 线分析 | [[signal-bars]], [[reversal-bars]], [[setup-anatomy]] | 已有概念覆盖 |

## 与现有知识的冲突
- **与 [[brooks-four-step-context]] 的框架对比**：
  - Brooks 四步（ctx）：价位(S/R)→阶段(FSM)→动能(重叠/斜率)→否决(TR/逃生)
  - huangzongprice 四步（本文）：动量→结构→均线→测量→K线
  - 两个框架的步骤顺序和关注点不同：ctx 框架以 S/R 为起点、以否决为终点（偏量化实现）；本文框架以动量为起点、以 K 线为终点（偏人工判断方法论）。本文可能是 ctx 框架的早期思想来源。

## 建议
1. 获取原生 PDF 重新 OCR（当前 pdftotext 完全失败）
2. 若能恢复完整 Mermaid 图，可作为 [[brooks-four-step-context]] 的「方法论原型」对比分析
3. 本文引用的 Brooks 视频（02D/19B/16C/14D）在 Wiki 中尚无对应笔记，属于知识缺口
