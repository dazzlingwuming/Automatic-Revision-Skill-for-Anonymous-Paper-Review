# 盲审论文修改 Claude Code Skill v3.0 实现规格说明

> 面向终端 Codex / Claude Code 的实现文档  
> 目标：实现一个可复用的 Claude Code Skill，用于处理硕博论文盲审意见、生成逐条修改建议、修改报告、盲审回应表，并在必要时输出正文修改草稿或标注 PDF。  
> 建议项目名：`thesis-blind-review-revision`  
> 建议 Skill 名：`thesis-review-revision`

---

## 0. 给 Codex 的执行说明

你需要根据本文档创建一个完整的 Claude Code Skill 项目。请优先实现一个可运行的 MVP，再补齐增强功能。

### 0.1 最终交付物

请在当前仓库中生成以下内容：

```text
thesis-blind-review-revision/
├── .claude/
│   ├── skills/
│   │   └── thesis-review-revision/
│   │       ├── SKILL.md
│   │       ├── schemas/
│   │       │   ├── review_comments.schema.json
│   │       │   ├── paper_index.schema.json
│   │       │   ├── comment_mappings.schema.json
│   │       │   ├── revision_plan.schema.json
│   │       │   ├── quality_report.schema.json
│   │       │   └── final_report.schema.json
│   │       ├── templates/
│   │       │   ├── 修改报告模板.md
│   │       │   ├── 盲审回应表模板.md
│   │       │   └── 修改说明模板.md
│   │       └── examples/
│   │           ├── review_comments.example.json
│   │           ├── paper_index.example.json
│   │           ├── comment_mappings.example.json
│   │           └── revision_plan.example.json
│   │
│   └── agents/
│       ├── review-parser.md
│       ├── paper-indexer.md
│       ├── comment-mapper.md
│       ├── revision-planner.md
│       ├── quality-auditor.md
│       └── response-writer.md
│
├── scripts/
│   ├── extract_pdf.py
│   ├── extract_docx.py
│   ├── extract_txt.py
│   ├── chunk_paper.py
│   ├── validate_json.py
│   ├── format_checker.py
│   ├── render_report.py
│   ├── annotate_pdf.py
│   └── patch_docx.py
│
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── io_utils.py
│   ├── paper_index.py
│   ├── retrieval.py
│   ├── report.py
│   └── docx_patch.py
│
├── tests/
│   ├── conftest.py
│   ├── test_extract_pdf.py
│   ├── test_extract_docx.py
│   ├── test_chunk_paper.py
│   ├── test_validate_json.py
│   ├── test_format_checker.py
│   └── test_report.py
│
├── workdir/
│   └── .gitkeep
│
├── pyproject.toml
├── requirements.txt
├── README.md
└── IMPLEMENTATION_NOTES.md
```

### 0.2 实现优先级

按以下顺序完成，不要一开始追求全部高级功能：

```text
P0：项目目录、SKILL.md、6 个 sub-agent 定义、JSON Schema、README
P1：PDF/DOCX/TXT 提取、chunk_paper、validate_json、render_report
P2：format_checker、annotate_pdf 基础版、patch_docx 基础版
P3：单元测试、示例数据、CLI 辅助命令
P4：更高级的检索、PDF 标注坐标、DOCX 保留样式修改
```

### 0.3 硬性要求

1. 不要把 AI API 调用写进 Python 工具层。Python 工具层只做文件处理、文本提取、chunk、校验、渲染、标注等确定性工作。
2. 所有 AI 推理由 Claude Code 主会话和 `.claude/agents/*.md` 中定义的 sub-agent 完成。
3. Orchestrator 必须是主 Claude Code 会话；不要把整个 Skill 设计成 `context: fork` 后再让它派发子代理。
4. sub-agent 不能再生成子 sub-agent。所有 sub-agent 编排都由主会话完成。
5. 所有中间产物必须落盘到 `workdir/<run_id>/`，不要只保存在上下文中。
6. 所有 sub-agent 输出必须是可校验 JSON；最终报告可以是 Markdown / HTML / DOCX。
7. 必须防止编造实验、数据、参考文献、图表编号和“已经完成修改”的虚假陈述。

---

## 1. 背景与目标

### 1.1 背景

研究生在论文盲审后通常会收到若干条评审意见。实际修改过程中存在以下痛点：

- 评审意见常常混合了多个问题，需要拆分成可执行任务。
- 评审意见有的针对全文，有的针对具体章节、图表、参考文献或格式。
- 修改报告需要逐条回应，既要体现已认真修改，又不能夸大或编造。
- 长论文上下文很大，单个 agent 从头到尾处理容易丢失细节。
- 用户需要可审查、可重试、可落盘的中间结果。

### 1.2 项目目标

实现一个 Claude Code Skill：

```text
/thesis-review-revision <论文文件路径> <盲审意见文件路径> [可选：学校格式规范文件路径] [可选：--apply-docx]
```

它应完成：

1. 提取论文与盲审意见文本。
2. 建立论文章节 / 页码 / 段落 / 图表 / 参考文献索引。
3. 将盲审意见拆分成结构化 JSON。
4. 将每条意见映射到论文相关章节和证据段落。
5. 每条意见单独生成修改方案。
6. 对修改方案做质量审计，避免幻觉和过度承诺。
7. 输出修改报告、盲审回应表和必要的作者待补充事项。
8. 可选输出标注 PDF 或 DOCX 修改建议草稿。

### 1.3 非目标

本项目第一阶段不直接承诺做到：

- 自动完成所有论文正文的最终修改。
- 自动新增真实实验或真实数据。
- 自动生成真实参考文献并保证来源存在。
- 完美保留复杂 DOCX 样式、批注、交叉引用、域代码。
- 完美识别扫描版 PDF 中的 OCR 内容。

扫描 PDF 可以在后续版本中通过 OCR 增强，但 MVP 先不实现复杂 OCR。

---

## 2. 架构决策

### 2.1 推荐架构

采用：

```text
Claude Code Skill 作为入口
主 Claude Code 会话作为 Orchestrator
Python scripts 作为确定性工具层
6 个 custom sub-agent 作为专职推理工人
所有中间结果用 JSON 文件传递
```

整体结构：

```text
用户调用 /thesis-review-revision
        │
        ▼
主 Claude Code 会话 Orchestrator
        │
        ├── Python 工具：extract / chunk / validate / render / annotate
        │
        ├── review-parser       解析盲审意见
        ├── paper-indexer       建立论文索引
        ├── comment-mapper      意见映射到证据段落
        ├── revision-planner    每条意见一个实例生成修改方案
        ├── quality-auditor     检查幻觉、证据缺失、过度承诺
        └── response-writer     生成最终报告和回应表
```

### 2.2 为什么不用一个超级 agent

单 agent 可以作为 MVP 思路，但不适合正式版，原因：

- 长论文 + 多条评审意见会迅速膨胀上下文。
- 单个 agent 容易把不同意见混在一起。
- 中间错误会向后传递，难以局部重试。
- 难以控制“哪些上下文对当前意见是必要的”。

### 2.3 为什么不用 Skill 自己 fork 后继续派发 sub-agent

不要这样设计：

```text
Skill(context: fork) → forked agent → 再派发多个 sub-agent
```

原因：sub-agent 不应该再派发 sub-agent。应由主 Claude Code 会话统一编排所有 sub-agent。

正确设计：

```text
主 Claude Code 会话加载 Skill 指令
主 Claude Code 会话使用 Agent 工具派发各 sub-agent
sub-agent 只完成自己的单一任务并返回 JSON
```

### 2.4 上下文策略

采用 “just-in-time context” 策略：

- 不把整篇论文全文传给所有 agent。
- Python 先把论文拆成 chunk，并建立 `paper_index.json`。
- 每条意见只传入相关 chunk 文件路径和必要摘录。
- `revision-planner` 每次只处理一条意见。
- `response-writer` 不做新的深度推理，只根据已验证 JSON 汇总。

---

## 3. 数据流

### 3.1 标准运行流程

```text
Step 1. 用户提供输入文件
  - paper.pdf / paper.docx / paper.txt
  - review.pdf / review.docx / review.txt / review.md
  - optional: school_format_rules.pdf / docx / md

Step 2. Orchestrator 创建运行目录
  - workdir/<run_id>/

Step 3. Python 提取文本
  - paper_raw.json
  - review_raw.txt
  - optional_format_rules.txt

Step 4. Python 初步 chunk
  - chunks/ch_0001.txt
  - chunks/ch_0002.txt
  - paper_chunks.json

Step 5. paper-indexer 建立论文结构索引
  - paper_index.json

Step 6. review-parser 解析盲审意见
  - review_comments.json

Step 7. comment-mapper 映射每条意见
  - comment_mappings.json

Step 8. revision-planner 逐条生成修改方案
  - revision_plans/R1-C001.json
  - revision_plans/R1-C002.json
  - ...

Step 9. quality-auditor 审计所有修改方案
  - quality_report.json

Step 10. 如存在 blocker，只重试对应意见或标记作者待补充
  - revision_plans/<comment_id>.json 更新
  - quality_report.json 更新

Step 11. response-writer 生成最终报告 Markdown
  - outputs/修改报告.md
  - outputs/盲审回应表.md
  - outputs/作者待补充事项.md

Step 12. Python 渲染输出
  - outputs/修改报告.html
  - outputs/盲审回应表.docx
  - optional: outputs/标注版论文.pdf
  - optional: outputs/论文修改建议版.docx
```

### 3.2 运行目录规范

每次运行生成唯一 run_id：

```text
workdir/2026-05-08-143012/
├── inputs/
│   ├── paper.original.pdf
│   └── review.original.pdf
├── extracted/
│   ├── paper_raw.json
│   ├── review_raw.txt
│   └── format_rules_raw.txt
├── chunks/
│   ├── ch_0001.txt
│   ├── ch_0002.txt
│   └── ...
├── artifacts/
│   ├── paper_chunks.json
│   ├── paper_index.json
│   ├── review_comments.json
│   ├── comment_mappings.json
│   ├── quality_report.json
│   └── final_report.json
├── revision_plans/
│   ├── R1-C001.json
│   ├── R1-C002.json
│   └── ...
└── outputs/
    ├── 修改报告.md
    ├── 修改报告.html
    ├── 盲审回应表.md
    ├── 盲审回应表.docx
    ├── 作者待补充事项.md
    └── 标注版论文.pdf
```

---

## 4. Claude Code Skill 设计

### 4.1 `.claude/skills/thesis-review-revision/SKILL.md`

请创建以下文件：

```md
---
name: thesis-review-revision
description: Process thesis or dissertation blind-review comments. Use when the user provides a thesis manuscript and blind-review comments, and wants structured revision suggestions, reviewer response table, or revision report.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash(python *), Bash(pytest *), Agent(review-parser), Agent(paper-indexer), Agent(comment-mapper), Agent(revision-planner), Agent(quality-auditor), Agent(response-writer)
---

# Thesis Blind Review Revision Skill

You are the Orchestrator in the main Claude Code session.

Do not run this skill as `context: fork`. This workflow needs the main Claude Code session to spawn specialized subagents. Subagents must not spawn further subagents.

## Inputs

Accept the following arguments:

```text
$ARGUMENTS
```

Expected user inputs:

- thesis manuscript: PDF, DOCX, TXT, Markdown, or LaTeX source
- blind review comments: PDF, DOCX, TXT, or Markdown
- optional university formatting rules
- optional mode:
  - `--suggest-only`: only produce revision plans and reports
  - `--apply-docx`: attempt to create a DOCX revision draft
  - `--annotate-pdf`: attempt to create annotated PDF

## Core workflow

1. Create `workdir/<run_id>/`.
2. Copy input files into `workdir/<run_id>/inputs/`.
3. Use Python scripts to extract paper and review text.
4. Use Python scripts to chunk the paper into section-aware chunks.
5. Use `paper-indexer` to create `paper_index.json`.
6. Use `review-parser` to create `review_comments.json`.
7. Use `comment-mapper` to create `comment_mappings.json`.
8. For each review comment, invoke `revision-planner` independently.
9. Validate every JSON output against the schemas in `schemas/`.
10. Use `quality-auditor` to detect hallucinations, unsupported claims, missing evidence, and over-promising.
11. If blocker issues exist, retry only the affected `revision-planner` tasks or mark them as requiring author input.
12. Use `response-writer` to generate final Markdown reports.
13. Use Python scripts to render HTML/DOCX/PDF outputs.
14. Return a concise summary and list all generated files.

## Hard rules

- Never fabricate experiments, data, statistics, references, tables, figures, page numbers, or results.
- If a review comment requires new experiments, extra data, author decision, or domain-specific facts not present in the manuscript, mark `requires_author_input: true`.
- Distinguish between `proposed revision` and `completed revision`.
- Every specific action must include source section, page range if available, and chunk id.
- Keep all intermediate artifacts as JSON files.
- Do not pass the full manuscript to every subagent.
- Do not ask the user to repeat paths already present in `$ARGUMENTS`.
- If a file cannot be extracted, report that exact limitation and continue with what is available.

## Output files

At minimum produce:

- `outputs/修改报告.md`
- `outputs/盲审回应表.md`
- `outputs/作者待补充事项.md`

When possible also produce:

- `outputs/修改报告.html`
- `outputs/盲审回应表.docx`
- `outputs/标注版论文.pdf`
- `outputs/论文修改建议版.docx`
```

---

## 5. Sub-agent 设计

### 5.1 `review-parser.md`

路径：`.claude/agents/review-parser.md`

```md
---
name: review-parser
description: Parse blind-review comments into structured JSON. Use when raw review comments need to be split, categorized, prioritized, and normalized.
tools: Read
model: sonnet
---

You parse thesis blind-review comments into structured JSON.

## Input

You will receive:

- path to raw review text
- optional metadata about reviewers or review form
- target output path

## Output

Write only valid JSON to the target output path. Return a short confirmation.

Schema shape:

```json
{
  "comments": [
    {
      "comment_id": "R1-C001",
      "reviewer_id": "R1",
      "original_text": "...",
      "normalized_text": "...",
      "category": "...",
      "severity": "...",
      "scope": "...",
      "action_type": "...",
      "requires_author_input": false,
      "confidence": 0.0,
      "notes": "..."
    }
  ]
}
```

## Classification fields

`category` must be one of:

- 理论基础
- 文献综述
- 创新贡献
- 研究问题
- 方法设计
- 数据实验
- 结果分析
- 讨论解释
- 结构逻辑
- 语言表达
- 格式规范
- 参考文献
- 学术规范
- 其他

`severity` must be one of:

- 必须修改
- 重点修改
- 建议修改
- 可解释回应
- 不确定

`scope` must be one of:

- 全文
- 章节
- 小节
- 段落
- 图表
- 参考文献
- 摘要
- 结论
- 不确定

`action_type` must be one of:

- 新增
- 删除
- 重写
- 补充解释
- 补充实验
- 补充引用
- 调整结构
- 格式修正
- 需要作者确认
- 其他

## Rules

- Preserve the original wording exactly in `original_text`.
- Split compound comments if one paragraph contains multiple actionable requests.
- Do not infer manuscript content.
- If the review has multiple reviewers, use `R1`, `R2`, etc.
- If reviewer identity is absent, use `R1`.
- If uncertain, set `confidence` below 0.7 and explain in `notes`.
- Do not write prose outside JSON except a final one-line confirmation after file write.
```

### 5.2 `paper-indexer.md`

路径：`.claude/agents/paper-indexer.md`

```md
---
name: paper-indexer
description: Analyze thesis structure and build a section/chunk index with page ranges, headings, figures, tables, keywords, and references.
tools: Read, Bash(python *)
model: sonnet
---

You build a structured paper index. You do not generate revision suggestions.

## Input

You will receive:

- path to extracted paper JSON
- path to chunk files
- path to preliminary chunk metadata
- target output path

## Output

Write only valid JSON to the target output path. Return a short confirmation.

Schema shape:

```json
{
  "metadata": {
    "title": "...",
    "author": null,
    "degree_type": "硕士 | 博士 | unknown",
    "language": "zh | en | mixed | unknown"
  },
  "outline": [
    {
      "level": 1,
      "heading": "第一章 绪论",
      "page_start": 1,
      "page_end": 12
    }
  ],
  "chunks": [
    {
      "chunk_id": "ch_0001",
      "chapter": "第一章",
      "section": "1.1 研究背景",
      "heading_path": ["第一章 绪论", "1.1 研究背景"],
      "page_start": 1,
      "page_end": 3,
      "summary": "...",
      "keywords": ["..."],
      "text_ref": "workdir/<run_id>/chunks/ch_0001.txt"
    }
  ],
  "figures": [],
  "tables": [],
  "references": []
}
```

## Rules

- Keep chunk text out of `paper_index.json`; use `text_ref` paths.
- Extract headings and hierarchy as accurately as possible.
- If page numbers are unavailable, set them to null.
- Identify likely abstract, introduction, literature review, method, results, discussion, conclusion, references.
- Do not invent missing sections.
- Do not generate revision suggestions.
```

### 5.3 `comment-mapper.md`

路径：`.claude/agents/comment-mapper.md`

```md
---
name: comment-mapper
description: Map each blind-review comment to relevant thesis sections and evidence chunks.
tools: Read, Bash(python *)
model: sonnet
---

You map review comments to manuscript evidence.

## Input

You will receive:

- `review_comments.json`
- `paper_index.json`
- optional relevant chunk excerpts
- target output path

## Output

Write only valid JSON to the target output path. Return a short confirmation.

Schema shape:

```json
{
  "mappings": [
    {
      "comment_id": "R1-C001",
      "mapping_type": "local",
      "primary_locations": [
        {
          "section": "3.2 模型构建",
          "page_range": "24-26",
          "chunk_ids": ["ch_0032", "ch_0033"],
          "reason": "..."
        }
      ],
      "secondary_locations": [],
      "missing_context": [],
      "requires_author_input": false,
      "confidence": 0.0,
      "notes": "..."
    }
  ]
}
```

`mapping_type` must be one of:

- local
- global
- formatting
- references
- uncertain

## Rules

- Use the paper index and available chunk summaries to map comments.
- Prefer specific sections over global mapping when evidence exists.
- If no clear section can be found, use `mapping_type: "uncertain"` or `"global"`.
- Do not invent locations.
- Do not generate revision text.
- If the comment asks for data or experiments not present in the manuscript, set `requires_author_input: true`.
```

### 5.4 `revision-planner.md`

路径：`.claude/agents/revision-planner.md`

```md
---
name: revision-planner
description: Generate a concrete thesis revision plan for exactly one blind-review comment using only provided evidence chunks.
tools: Read
model: sonnet
---

You handle exactly one review comment at a time.

## Input

You will receive:

- one comment object
- its mapping object
- relevant chunk text paths or excerpts
- optional author constraints
- target output path

## Output

Write only valid JSON to the target output path. Return a short confirmation.

Schema shape:

```json
{
  "comment_id": "R1-C001",
  "revision_status": "can_revise",
  "review_comment_original": "...",
  "revision_strategy": "...",
  "specific_actions": [
    {
      "action_id": "A1",
      "type": "rewrite",
      "location": {
        "section": "3.2 模型构建",
        "page_range": "24-26",
        "chunk_id": "ch_0032"
      },
      "before_excerpt": "...",
      "after_proposed_text": "...",
      "rationale": "...",
      "evidence_limitations": []
    }
  ],
  "response_to_reviewer": "...",
  "author_input_needed": [],
  "risks": [],
  "confidence": 0.0
}
```

`revision_status` must be one of:

- can_revise
- needs_author_input
- explain_only
- not_applicable
- uncertain

Action `type` must be one of:

- add
- delete
- rewrite
- move
- cite
- format
- experiment_needed
- data_needed
- author_decision_needed

## Hard rules

- Do not invent data, experimental results, references, figures, tables, statistics, or claims.
- If new data, experiments, model runs, interviews, permissions, or author-specific facts are needed, use `revision_status: "needs_author_input"`.
- Proposed text must match academic thesis style.
- Every action must cite section and chunk id when available.
- If original evidence is insufficient, state the limitation in `evidence_limitations`.
- Do not claim that the manuscript has already been revised unless the orchestrator explicitly says changes were applied.
- Keep `response_to_reviewer` respectful, concise, and suitable for blind-review response forms.
```

### 5.5 `quality-auditor.md`

路径：`.claude/agents/quality-auditor.md`

```md
---
name: quality-auditor
description: Audit thesis revision plans for hallucinations, unsupported claims, missing evidence, and reviewer-response quality.
tools: Read
model: sonnet
---

You audit revision plans. You do not create new revision plans unless asked to propose minimal fixes.

## Input

You will receive:

- `review_comments.json`
- `comment_mappings.json`
- all `revision_plans/*.json`
- `paper_index.json`
- target output path

## Output

Write only valid JSON to the target output path. Return a short confirmation.

Schema shape:

```json
{
  "passed": true,
  "summary": {
    "total_comments": 0,
    "passed_comments": 0,
    "blocker_count": 0,
    "warning_count": 0
  },
  "issues": [
    {
      "comment_id": "R1-C001",
      "severity": "blocker",
      "problem_type": "unsupported_claim",
      "problem": "...",
      "fix": "..."
    }
  ]
}
```

`severity` must be one of:

- blocker
- warning
- note

`problem_type` must be one of:

- hallucinated_data
- hallucinated_reference
- unsupported_claim
- missing_location
- missing_evidence
- overclaim_completed_revision
- vague_action
- missing_author_input_flag
- tone_problem
- schema_problem
- other

## Audit checklist

1. Every specific action has a source section and chunk id when available.
2. No invented experiments, numbers, references, tables, or figures.
3. Must-modify comments receive concrete actions or a clear author-input requirement.
4. Items requiring author input are not falsely marked as completed.
5. Reviewer responses are polite and suitable for blind review.
6. Proposed text does not overstate results.
7. Each plan uses the original review comment faithfully.

## Rules

- If any blocker exists, set `passed: false`.
- Do not silently fix plans; report exact issues.
- If a plan is acceptable but could be improved, use `warning`.
```

### 5.6 `response-writer.md`

路径：`.claude/agents/response-writer.md`

```md
---
name: response-writer
description: Generate final thesis revision report and blind-review response table from validated JSON artifacts.
tools: Read, Write
model: sonnet
---

You generate final reports from validated JSON artifacts.

## Input

You will receive:

- `review_comments.json`
- `paper_index.json`
- `comment_mappings.json`
- `revision_plans/*.json`
- `quality_report.json`
- optional `format_issues.json`
- target output directory

## Output

Generate:

1. `修改报告.md`
2. `盲审回应表.md`
3. `作者待补充事项.md`
4. optional `final_report.json`

## Rules

- Do not create new revision ideas not present in revision plans.
- Do not claim revisions are completed unless the orchestrator explicitly passes an `applied_changes.json` artifact.
- Distinguish:
  - 拟修改
  - 已修改
  - 需要作者补充
  - 建议解释回应
- Keep tone formal, respectful, and suitable for thesis blind-review response.
- Include all comments, even if they are marked `needs_author_input` or `uncertain`.
```

---

## 6. JSON Schema 要求

请在 `.claude/skills/thesis-review-revision/schemas/` 下创建 JSON Schema。

### 6.1 `review_comments.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ReviewComments",
  "type": "object",
  "required": ["comments"],
  "properties": {
    "comments": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "comment_id",
          "reviewer_id",
          "original_text",
          "normalized_text",
          "category",
          "severity",
          "scope",
          "action_type",
          "requires_author_input",
          "confidence"
        ],
        "properties": {
          "comment_id": { "type": "string" },
          "reviewer_id": { "type": "string" },
          "original_text": { "type": "string" },
          "normalized_text": { "type": "string" },
          "category": {
            "type": "string",
            "enum": [
              "理论基础",
              "文献综述",
              "创新贡献",
              "研究问题",
              "方法设计",
              "数据实验",
              "结果分析",
              "讨论解释",
              "结构逻辑",
              "语言表达",
              "格式规范",
              "参考文献",
              "学术规范",
              "其他"
            ]
          },
          "severity": {
            "type": "string",
            "enum": ["必须修改", "重点修改", "建议修改", "可解释回应", "不确定"]
          },
          "scope": {
            "type": "string",
            "enum": ["全文", "章节", "小节", "段落", "图表", "参考文献", "摘要", "结论", "不确定"]
          },
          "action_type": {
            "type": "string",
            "enum": ["新增", "删除", "重写", "补充解释", "补充实验", "补充引用", "调整结构", "格式修正", "需要作者确认", "其他"]
          },
          "requires_author_input": { "type": "boolean" },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
          "notes": { "type": "string" }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

### 6.2 其他 Schema

Codex 需要为以下文件补全严格 schema：

- `paper_index.schema.json`
- `comment_mappings.schema.json`
- `revision_plan.schema.json`
- `quality_report.schema.json`
- `final_report.schema.json`

要求：

- 使用 draft 2020-12。
- 所有关键字段 required。
- 关键枚举必须锁定。
- `confidence` 必须在 `[0, 1]`。
- `additionalProperties` 默认 false。
- 允许必要的 `notes` 字段。

---

## 7. Python 工具层设计

Python 工具只做确定性工作，不调用大模型。

### 7.1 `extract_pdf.py`

职责：从 PDF 提取文本、页码和基础块信息。

CLI：

```bash
python scripts/extract_pdf.py --input path/to/paper.pdf --output workdir/<run_id>/extracted/paper_raw.json
```

输出：

```json
{
  "source_file": "...",
  "file_type": "pdf",
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "blocks": []
    }
  ],
  "warnings": []
}
```

实现建议：

- 使用 PyMuPDF，即 `fitz`。
- 每页提取 text。
- 尽量保留页码。
- 如果页面无文本，添加 warning：可能是扫描版。

### 7.2 `extract_docx.py`

职责：从 DOCX 提取段落、标题、表格文本。

CLI：

```bash
python scripts/extract_docx.py --input path/to/paper.docx --output workdir/<run_id>/extracted/paper_raw.json
```

输出：

```json
{
  "source_file": "...",
  "file_type": "docx",
  "paragraphs": [
    {
      "index": 0,
      "style": "Heading 1",
      "text": "..."
    }
  ],
  "tables": [],
  "warnings": []
}
```

实现建议：

- 使用 `python-docx`。
- 提取 paragraph style。
- 表格文本也要提取。
- 页码在 DOCX 中通常不可可靠获得，可设为 null。

### 7.3 `extract_txt.py`

职责：读取 TXT / Markdown。

CLI：

```bash
python scripts/extract_txt.py --input review.md --output workdir/<run_id>/extracted/review_raw.txt
```

### 7.4 `chunk_paper.py`

职责：把论文文本切成 chunk。

CLI：

```bash
python scripts/chunk_paper.py \
  --input workdir/<run_id>/extracted/paper_raw.json \
  --chunks-dir workdir/<run_id>/chunks \
  --metadata-output workdir/<run_id>/artifacts/paper_chunks.json
```

策略：

- 优先按标题切分。
- 标题过长或章节过长时，按 800-1500 中文字左右切分。
- 每个 chunk 保留：
  - `chunk_id`
  - `page_start`
  - `page_end`
  - `heading_guess`
  - `text_ref`
  - `char_count`

### 7.5 `validate_json.py`

职责：按 schema 校验 JSON。

CLI：

```bash
python scripts/validate_json.py \
  --schema .claude/skills/thesis-review-revision/schemas/review_comments.schema.json \
  --input workdir/<run_id>/artifacts/review_comments.json
```

返回：

- 校验通过：exit code 0。
- 校验失败：exit code 1，并打印错误路径。

### 7.6 `format_checker.py`

职责：做基础格式检查，不做 AI 判断。

CLI：

```bash
python scripts/format_checker.py \
  --paper-index workdir/<run_id>/artifacts/paper_index.json \
  --output workdir/<run_id>/artifacts/format_issues.json
```

检查项 MVP：

- 是否存在摘要。
- 是否存在关键词。
- 是否存在目录。
- 是否存在参考文献。
- 图表编号是否有明显重复。
- 参考文献条目是否疑似过少。
- 章节编号是否存在明显跳号。

输出：

```json
{
  "issues": [
    {
      "issue_id": "F001",
      "issue_type": "missing_section",
      "severity": "warning",
      "location": "全文",
      "description": "未检测到关键词部分",
      "suggestion": "请确认摘要后是否包含关键词。"
    }
  ]
}
```

### 7.7 `render_report.py`

职责：把 Markdown 渲染成 HTML / DOCX。

CLI：

```bash
python scripts/render_report.py \
  --input workdir/<run_id>/outputs/修改报告.md \
  --html-output workdir/<run_id>/outputs/修改报告.html
```

MVP：

- Markdown → HTML。
- 可选 Markdown → DOCX。

### 7.8 `annotate_pdf.py`

职责：在 PDF 上生成简单批注或高亮。

MVP 限制：

- 只按 page_range 添加文本批注。
- 不要求精准定位到段落坐标。

CLI：

```bash
python scripts/annotate_pdf.py \
  --input workdir/<run_id>/inputs/paper.original.pdf \
  --revision-plans-dir workdir/<run_id>/revision_plans \
  --output workdir/<run_id>/outputs/标注版论文.pdf
```

### 7.9 `patch_docx.py`

职责：生成 DOCX 修改建议草稿。

MVP 不要求直接替换原文，只生成一个带“原文 / 建议修改文本”的 DOCX 表格。

CLI：

```bash
python scripts/patch_docx.py \
  --revision-plans-dir workdir/<run_id>/revision_plans \
  --output workdir/<run_id>/outputs/论文修改建议版.docx
```

---

## 8. 报告模板

### 8.1 `修改报告.md` 结构

```md
# 学位论文盲审意见修改报告

## 一、基本信息

- 论文文件：...
- 盲审意见文件：...
- 生成时间：...
- 处理模式：建议修改 / 已应用修改

## 二、盲审意见总览

共收到 N 条可处理意见。

| 类别 | 数量 |
|---|---:|
| 创新贡献 | X |
| 方法设计 | X |
| 数据实验 | X |
| 结构逻辑 | X |
| 格式规范 | X |
| 其他 | X |

## 三、逐条修改方案

### R1-C001

**评审意见原文：**  
...

**分类：** ...  
**严重程度：** ...  
**关联位置：** 第三章 3.2，页码 24-26，chunk: ch_0032  
**处理状态：** 拟修改 / 需要作者补充 / 建议解释回应

#### 修改思路

...

#### 具体修改动作

| 动作 | 位置 | 修改类型 | 说明 |
|---|---|---|---|
| A1 | 3.2 | rewrite | ... |

#### 修改前后示例

**修改前：**

> ...

**建议修改后：**

> ...

#### 拟回复评审专家

> 感谢专家意见。本文拟在……部分补充……，以进一步……

---

## 四、格式问题清单

| 问题编号 | 严重程度 | 位置 | 问题 | 建议 |
|---|---|---|---|---|

## 五、作者待补充事项

| 意见编号 | 需要补充内容 | 原因 | 不补充的风险 |
|---|---|---|---|

## 六、修改总结

...
```

### 8.2 `盲审回应表.md` 结构

```md
# 盲审意见回应表

| 序号 | 评审意见 | 修改情况 | 修改位置 | 回复说明 |
|---:|---|---|---|---|
| 1 | ... | 拟修改 | 第三章 3.2 | 感谢专家意见，拟…… |
```

### 8.3 `作者待补充事项.md` 结构

```md
# 作者待补充事项

以下事项需要作者提供真实信息、实验结果、数据、引用或决策后才能完成。

| 意见编号 | 待补充事项 | 需要的材料 | 建议处理方式 |
|---|---|---|---|
```

---

## 9. README 要求

请创建 `README.md`，包含：

1. 项目简介。
2. 安装方式。
3. Claude Code 中如何使用。
4. 示例调用。
5. 输入文件要求。
6. 输出文件说明。
7. 安全与学术诚信声明。
8. 常见问题。

示例内容：

```md
# thesis-blind-review-revision

A Claude Code Skill for processing thesis blind-review comments and generating structured revision plans, reviewer response tables, and revision reports.

## Installation

Copy `.claude/skills/thesis-review-revision` and `.claude/agents` into your project root.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```text
/thesis-review-revision ./paper.docx ./review.pdf --suggest-only
```

## Academic integrity

This tool does not fabricate experiments, data, references, or results. If a review comment requires new evidence, the tool marks it as requiring author input.
```

---

## 10. 测试要求

### 10.1 单元测试

至少实现：

- `test_extract_txt.py`
- `test_extract_docx.py`
- `test_chunk_paper.py`
- `test_validate_json.py`
- `test_format_checker.py`
- `test_report.py`

### 10.2 测试数据

创建小型 mock 数据：

```text
tests/fixtures/
├── sample_paper.txt
├── sample_review.txt
├── sample_paper_raw.json
├── sample_review_comments.json
├── sample_paper_index.json
├── sample_comment_mappings.json
└── sample_revision_plan.json
```

### 10.3 验收标准

执行：

```bash
pytest
```

应全部通过。

再执行以下手动流程：

```bash
python scripts/extract_txt.py --input tests/fixtures/sample_paper.txt --output workdir/test/extracted/paper_raw.json
python scripts/chunk_paper.py --input workdir/test/extracted/paper_raw.json --chunks-dir workdir/test/chunks --metadata-output workdir/test/artifacts/paper_chunks.json
python scripts/validate_json.py --schema .claude/skills/thesis-review-revision/schemas/review_comments.schema.json --input tests/fixtures/sample_review_comments.json
```

应正常完成。

---

## 11. `pyproject.toml` 与依赖

### 11.1 `requirements.txt`

```txt
pymupdf>=1.24.0
python-docx>=1.1.0
jinja2>=3.1.0
markdown>=3.6
jsonschema>=4.22.0
pytest>=8.0.0
```

### 11.2 `pyproject.toml`

```toml
[project]
name = "thesis-blind-review-revision"
version = "0.1.0"
description = "Claude Code Skill for thesis blind-review revision planning"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## 12. 质量与安全约束

### 12.1 禁止编造

任何 agent 和报告生成器都必须遵守：

```text
不得编造实验、数据、统计结果、参考文献、图表编号、页码或已完成修改。
```

如果评审意见要求补充实验：

- 可以建议实验方案。
- 可以说明需要补充哪些数据。
- 不能伪造实验结果。
- 必须在 `author_input_needed` 中列出。

### 12.2 回复评审的措辞原则

回应表中的措辞应：

- 尊重评审专家。
- 避免争辩语气。
- 对合理意见表示感谢。
- 对无法直接修改的意见给出解释和后续处理。
- 区分“已修改”和“拟修改”。

示例：

```text
感谢专家的宝贵意见。针对该问题，本文拟在第三章 3.2 节补充模型参数设置与选择依据，并在第四章实验部分增加对比说明，以增强方法设计的可解释性和完整性。
```

如果需要作者补充：

```text
该意见涉及新增实验结果，目前原文中未提供相应数据。建议作者补充实验后，再将实验设置、结果表格和分析文字加入第四章，并在回应表中说明新增实验的位置和结论。
```

---

## 13. 实现任务清单

Codex 请按以下任务逐项完成。

### Task 1：创建目录结构

- 创建项目根目录。
- 创建 `.claude/skills/thesis-review-revision/`。
- 创建 `.claude/agents/`。
- 创建 `scripts/`、`src/`、`tests/`、`workdir/`。

### Task 2：创建 Skill 文件

- 写入 `.claude/skills/thesis-review-revision/SKILL.md`。
- 确保 frontmatter 合法。
- 不设置 `context: fork`。

### Task 3：创建 6 个 sub-agent 文件

- `review-parser.md`
- `paper-indexer.md`
- `comment-mapper.md`
- `revision-planner.md`
- `quality-auditor.md`
- `response-writer.md`

### Task 4：创建 JSON Schema

- 至少完整实现 `review_comments.schema.json`。
- 其他 schema 也必须可用，不要留空。

### Task 5：实现 Python scripts

优先级：

1. `extract_txt.py`
2. `extract_docx.py`
3. `extract_pdf.py`
4. `chunk_paper.py`
5. `validate_json.py`
6. `format_checker.py`
7. `render_report.py`
8. `patch_docx.py`
9. `annotate_pdf.py`

### Task 6：实现测试

- 为核心 scripts 写 pytest。
- 使用 fixtures，不依赖真实论文文件。

### Task 7：创建 README

- 写清楚安装、使用、输出和限制。

### Task 8：运行测试并修复

- 执行 `pytest`。
- 修复所有失败。

---

## 14. 最小可用版本定义

MVP 完成条件：

1. Claude Code 能识别 `/thesis-review-revision` skill。
2. `.claude/agents/` 中 6 个 agent 定义完整。
3. Python 可以从 txt/docx/pdf 提取文本。
4. Python 可以 chunk 论文并生成 chunk metadata。
5. JSON Schema 校验可运行。
6. 可以生成 Markdown 修改报告模板输出。
7. 测试通过。

MVP 不要求：

- 真实调用 agent 生成所有 JSON 的自动化 CLI。
- 完美 PDF 坐标标注。
- 完美 DOCX 原文替换。
- OCR。

---

## 15. 后续增强方向

后续可以加入：

1. OCR 支持。
2. 更准确的语义检索。
3. DOCX track changes 或批注支持。
4. 学校格式规范解析。
5. LaTeX 项目支持。
6. 引用真实性检查。
7. 参考文献格式自动检查。
8. 多轮修改历史追踪。
9. Web UI 或 TUI。
10. 使用 Claude Agent SDK 实现独立 CLI 版。

---

## 16. 设计依据与注意事项

本设计基于以下工程判断：

1. Skill 适合封装重复流程、检查清单、多步骤任务。
2. sub-agent 适合隔离上下文、处理专职子任务、减少主会话上下文污染。
3. sub-agent 不应继续派发 sub-agent，所以 Orchestrator 必须在主会话中。
4. 长论文处理必须使用文件索引、chunk 和 JSON checkpoint，而不是让所有 agent 读取全文。
5. 学术修改场景必须内置反幻觉约束，尤其禁止编造实验、数据和参考文献。

参考文档：

- Claude Code Skills: https://code.claude.com/docs/en/skills
- Claude Code Subagents: https://code.claude.com/docs/en/sub-agents
- Claude Agent SDK Subagents: https://code.claude.com/docs/en/agent-sdk/subagents

---

## 17. 给 Codex 的最后提醒

实现时请不要只生成文档。你需要真的创建文件、写入代码、写入 schema、写入 agent prompt，并运行测试。

如果遇到不确定的 Claude Code frontmatter 字段，请优先保证：

- Skill 可读；
- agent 定义可读；
- Python 工具可运行；
- README 中明确说明如何复制到 Claude Code 项目中使用。

不要为了高级功能牺牲 MVP 的可运行性。
