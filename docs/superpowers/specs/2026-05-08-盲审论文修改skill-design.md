# 盲审论文修改 Skill 设计文档

> **版本:** v2.0
> **日期:** 2026-05-08
> **状态:** 设计稿

## 1. 概述

### 1.1 项目目标

设计一个 Claude Code Skill，帮助研究生高效完成盲审论文的修改任务。该 Skill 定义了 Claude 在处理盲审论文修改时的完整工作流程、sub-agent 分工与协作方式、行为规范和输出标准，并配套提供 Python 自动化工具作为支撑。

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **每个步骤独立 sub-agent** | 不同阶段由独立的 sub-agent 处理，上下文高度聚焦，互不污染 |
| **逐条处理评审意见** | 每条评审意见由独立的 sub-agent 实例处理，单条处理完后再汇总 |
| **结构化数据传递** | 阶段之间通过 JSON 结构化数据通信，而非原始长文本 |
| **可审查可重试** | 每步输出都可审查，某条意见失败只需重试对应 sub-agent |
| **Python 做脏活** | 文件 I/O、文本提取、报告渲染等纯工具工作由 Python 完成，AI 推理全部由 sub-agent 承担 |

### 1.3 核心能力

| 能力 | 说明 | 负责方 |
|------|------|--------|
| **盲审意见解析** | 自动解析盲审意见书，逐条提取评审意见并分类 | Sub-agent 1 |
| **论文内容分析** | 将每一条评审意见映射到论文的具体章节和位置 | Sub-agent 2 |
| **修改建议生成** | 针对每条意见结合论文内容生成具体的修改方案 | Sub-agent 3（每条意见一个实例） |
| **格式规范性检查** | 检查论文格式是否符合学术规范 | Python 工具 |
| **修改报告生成** | 输出结构化的 Markdown/HTML 修改报告 | Sub-agent 4 |
| **标注 PDF 生成** | 在原 PDF 上标注修改位置 | Python 工具 |

### 1.4 用户画像

- 硕博研究生，需要进行盲审后的论文修改
- 手头有盲审版本论文（PDF/Word）和盲审意见书（PDF/文字）
- 需要系统性地处理每一条评审意见，输出规范的修改报告

## 2. 架构设计

### 2.1 整体架构

```
┌────────────────────────────────────────────────────────────────────┐
│                          SKILL.md (行为定义)                        │
│  定义 Orchestrator 的工作流程、sub-agent 分工、prompt 模板、       │
│  审查标准、输出规范                                                │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ 遵循
┌──────────────────────────▼─────────────────────────────────────────┐
│                     Orchestrator (主 Claude 会话)                   │
│  协调整个流程：收集输入 → 派发 sub-agent → 审查结果 → 输出         │
│  每个步骤只传递必要的数据，不做 AI 推理工作                         │
└────────────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬──────────────────┐
        ▼                  ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Sub-agent 1  │  │ Sub-agent 2  │  │ Sub-agent 3  │  │ Sub-agent 4  │
│  ParseReview │→ │ AnalyzePaper │→ │GenSuggestions│→ │GenReport     │
│ 解析盲审意见  │  │ 映射到章节    │  │ 逐条生成建议  │  │ 合成报告     │
│ 输出: JSON   │  │ 输出: JSON   │  │ 输出: JSON   │  │ 输出: MD+HTML│
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
                                                    │
                                                    ▼
                                           ┌──────────────┐
                                           │ Python 工具   │
                                           │ PDF提取/格式  │
                                           │ 检查/报告渲染  │
                                           └──────────────┘
```

### 2.2 关键区别（vs v1.0 架构）

| 维度 | v1.0 架构（问题） | v2.0 架构（改进） |
|------|------------------|------------------|
| **上下文管理** | 所有步骤在同一上下文串行执行，越往后效果越差 | 每个 sub-agent 只看到自己需要的数据，上下文高度聚焦 |
| **意见处理** | 一次性处理所有意见 | 逐条独立处理，互不干扰 |
| **错误隔离** | 中间出错要全部重来 | 单条意见出错只需重试对应 sub-agent |
| **扩展性** | 修改流程需要改整体代码 | 可独立调整某个 sub-agent 的 prompt |
| **AI 职责** | Python 工具中封装 AI 调用 | AI 推理全部由 sub-agent 承担，Python 只做工具性工作 |

### 2.3 数据流

```
步骤1: 用户提供 论文PDF + 盲审意见PDF
          │
          ▼
步骤2: Python 工具提取文本
          │  输出: paper_text (str), review_text (str)
          ▼
步骤3: Orchestrator 派发 Sub-agent 1 (ParseReview)
          │  输入: review_text
          │  输出: JSON [{id, category, severity, original_text}, ...]
          ▼
步骤4: Orchestrator 派发 Sub-agent 2 (AnalyzePaper)
          │  输入: paper_text + JSON comments
          │  输出: JSON comments (补充了 related_section, page_ref)
          ▼
步骤5: Orchestrator 派发 Python 格式检查
          │  输入: paper_text
          │  输出: JSON [{issue_type, description, location, suggestion}, ...]
          ▼
步骤6: Orchestrator 逐个派发 Sub-agent 3 (GenSuggestion × N)
          │  每个实例输入: 单条 comment + 对应论文段落
          │  每个实例输出: JSON {comment_id, suggestion, example_text}
          │  (可并行派发)
          ▼
步骤7: Orchestrator 派发 Sub-agent 4 (GenReport)
          │  输入: 汇总的 JSON 数据 (不含原始论文全文)
          │  输出: 修改报告 (Markdown)
          ▼
步骤8: Python 工具渲染 HTML + 生成标注 PDF
```

### 2.4 每个 Sub-agent 的上下文范围

```
Sub-agent 1 (ParseReview): 仅盲审意见文本 + 分类规范
  → 上下文大小: ~3K tokens

Sub-agent 2 (AnalyzePaper): 论文目录结构 + 每条意见的文本
  → 上下文大小: ~5K tokens

Sub-agent 3 (GenSuggestion × 1): 仅 1 条意见 + 对应论文段落
  → 上下文大小: ~2-4K tokens

Sub-agent 4 (GenReport): 结构化 JSON 数据（无原始论文）
  → 上下文大小: ~3K tokens

对比 v1.0: 全部内容塞在一个上下文（可能 50K+ tokens）
```

## 3. Sub-agent 详细设计

### 3.1 Sub-agent 1: 盲审意见解析器 (ParseReview)

**职责:** 从盲审意见文本中逐条提取评审意见，进行分类和严重程度标注

**输入:**
```
盲审意见文本（来自 PDF 提取）
```

**输出格式:**
```json
[
  {
    "id": "意见1",
    "category": "创新性",
    "severity": "必须修改",
    "original_text": "论文创新点不足，需要进一步突出研究贡献。"
  },
  {
    "id": "意见2",
    "category": "实验设计",
    "severity": "建议修改",
    "original_text": "实验样本量过小，建议补充更多数据。"
  }
]
```

**Prompt 要点:**
- 按编号（1. 2. 3. / ① ② ③ / 一、二、三）分割意见条目
- 分类标准见第 4 节
- 严重程度：看是否有"必须""务必""强烈建议"等关键词
- 如果文本中没有明确编号，也要按语意段落分割

### 3.2 Sub-agent 2: 论文分析器 (AnalyzePaper)

**职责:** 将每条评审意见映射到论文的具体章节和位置

**输入:**
```
论文全文文本 + Sub-agent 1 的 JSON 输出
```

**输出格式:**
```json
[
  {
    "id": "意见1",
    "category": "创新性",
    "severity": "必须修改",
    "original_text": "...",
    "related_section": "第三章 研究方法",   // 新增
    "page_ref": 15                          // 新增
  }
]
```

**Prompt 要点:**
- 先提取论文的章节结构（目录）
- 对每条意见，判断它最可能指向哪个章节
- 如果无法精确映射，标注"全文性意见"

### 3.3 Sub-agent 3: 修改建议生成器 (GenSuggestion)

**职责:** 针对单条评审意见，结合对应的论文段落，生成具体的修改方案

**每条意见启动一个独立的 Sub-agent 实例，这是架构的核心改进点。**

**输入:**
```json
{
  "comment": {
    "id": "意见1",
    "category": "创新性",
    "severity": "必须修改",
    "original_text": "论文创新点不足，需要进一步突出研究贡献。"
  },
  "paper_section": "第三章 研究方法的第3.2节相关内容...（有限段落，非全篇）"
}
```

**输出格式:**
```json
{
  "comment_id": "意见1",
  "suggestion": "修改方案：在第三章末尾增加一段...（详细方案）",
  "example_text": "修改前：...\n修改后：...",
  "suggestion_summary": "在3.2节末尾增加创新性论述"
}
```

**Prompt 要点:**
- 不要泛泛而谈，必须给出具体可操作的修改方案
- 必须包含修改前后的文本示例对比
- 尊重原文的学术风格
- 上下文只包含 1 条意见 + 相关段落，token 数极低

### 3.4 Sub-agent 4: 报告生成器 (GenReport)

**职责:** 将所有的分析结果和修改建议合成一份完整的修改报告

**输入:** 前面所有步骤的结构化 JSON 数据汇总

**输出:** Markdown 格式的完整修改报告

**Prompt 要点:**
- 遵循第 5 节的报告格式
- 不需要参考原始论文全文，只基于结构化数据

## 4. 评审意见分类体系

| 类别 | 判断关键词 | 修改策略 |
|------|-----------|---------|
| **创新性** | 创新、贡献、新颖、新意、研究价值 | 补充创新点论述，加强文献对比，突出差异化贡献 |
| **实验设计** | 实验、数据、方法、模型、样本、验证 | 补充实验细节，增加对比实验，完善数据分析 |
| **写作规范** | 写作、逻辑、结构、表达、语言 | 调整结构，优化逻辑，精简表达，统一术语 |
| **格式规范** | 格式、排版、图表、参考文献、字体 | 统一格式，规范引用，调整排版 |
| **其他** | 无法归入以上类别的意见 | 根据具体内容灵活处理 |

## 5. 报告格式

修改报告应包含以下四个部分：

### 一、盲审意见总览
```
共收到 N 条评审意见：
- 创新性: X 条
- 实验设计: X 条
...
```

### 二、逐条修改建议
每条意见的修改建议表格，含：
- 评审意见原文
- 分类和严重程度标签
- 修改方案
- 修改前后对比示例
- 关联章节

### 三、格式问题清单
格式不规范项及修改建议（表格形式）

### 四、修改总结
整体修改情况统计，未处理意见及理由

## 6. Python 工具设计

经过架构调整后，Python 工具的角色从"AI 调用层"变为"纯工具层"：

| 模块 | 职责 | 说明 |
|------|------|------|
| `pdf_parser.py` | PDF 文本提取 | 使用 PyMuPDF，只做文本提取，不做语义分析 |
| `docx_parser.py` | Word 文本提取 | 使用 python-docx |
| `format_checker.py` | 格式规则检查 | 纯规则引擎（关键词数量、摘要存在性、参考文献检测等） |
| `report_generator.py` | 报告模板渲染 | Markdown + Jinja2 HTML 渲染 |
| `cli.py` | 独立运行入口 | 供不通过 Claude Code 的用户使用（直接调用 API 的模式） |

### 6.1 CLI 模式（独立使用）

当用户没有通过 Claude Code 交互，而是直接 `python main.py` 运行时，Python 工具会自行调用 AI API，采用同样的 sub-agent 逻辑（通过 Agent 工具）：

```
CLI 入口
  → Python 提取文本
  → 调用 API 依次完成 4 个 sub-agent 步骤
  → 生成报告
```

## 7. 技术选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| PDF解析 | PyMuPDF (fitz) | 高性能 PDF 文本提取 |
| Word解析 | python-docx | Word 文档读写 |
| HTML报告 | Jinja2 | 模板引擎生成可视化报告 |
| CLI框架 | argparse | 命令行参数解析 |
| 测试 | pytest | 单元测试框架 |
| Sub-agent 机制 | Claude Code Agent 工具 | 通过 Agent 工具派发独立 sub-agent |

## 8. 项目结构

```
盲审论文修改skill/
├── SKILL.md                         # Skill 核心定义（Orchestrator 行为 + sub-agent prompts）
├── CLAUDE.md                        # 项目说明
├── main.py                          # CLI 入口（独立运行模式）
├── requirements.txt                 # Python 依赖
├── docs/
│   └── superpowers/
│       ├── specs/                   # 设计文档（本文件）
│       └── plans/                   # 实现计划
├── src/
│   ├── __init__.py
│   ├── cli.py                       # CLI 参数解析
│   ├── models.py                    # 结构化数据模型（JSON schema）
│   ├── parser/
│   │   ├── pdf_parser.py            # PDF 文本提取
│   │   └── docx_parser.py           # Word 文本提取
│   ├── checker/
│   │   └── format_checker.py        # 格式规则检查（纯规则引擎）
│   └── reporter/
│       ├── report_generator.py      # 报告渲染
│       ├── pdf_annotator.py         # PDF 标注
│       └── templates/
│           └── report.html          # HTML 模板
├── tests/
│   ├── conftest.py
│   ├── test_pdf_parser.py
│   ├── test_format_checker.py
│   └── test_models.py
└── 例子/
    ├── 盲审版本.pdf
    └── 盲审评价.pdf
```
