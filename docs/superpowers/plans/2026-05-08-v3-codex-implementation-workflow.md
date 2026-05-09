# 盲审论文修改 Skill v3 Codex 实现流程

> 日期：2026-05-08  
> 状态：实施前流程文档  
> 依据：`docs/superpowers/specs/盲审论文修改_Claude_Code_Skill_v3_Codex实现规格.md`

## 1. 本轮目标

本项目后续实现必须以 v3 规格为准，先交付一个可运行、可测试、可审查的 Claude Code Skill MVP，再补齐增强能力。

当前阶段只完成项目文档流程，不进入代码实现。后续实现时按本文档逐步推进，每个阶段完成后先验收再进入下一阶段。

## 2. v3 规格的核心准绳

1. Python 工具层只做确定性工作：文件提取、切分、JSON 校验、格式检查、报告渲染、PDF/DOCX 辅助输出。
2. Python 工具层不得内置 AI API 调用。
3. 主 Claude Code 会话是 Orchestrator，负责调用 Python 工具和派发 sub-agent。
4. sub-agent 只完成单一推理任务，不再派发新的 sub-agent。
5. 所有中间产物必须落盘到 `workdir/<run_id>/`。
6. sub-agent 输出必须是可校验 JSON。
7. 必须防止编造实验、数据、参考文献、图表编号、页码和“已完成修改”的虚假陈述。

## 3. 当前项目现状

当前仓库已有一版 v1/v2 风格实现：

| 模块 | 当前状态 | 与 v3 的关系 |
|---|---|---|
| 根目录 `SKILL.md` | 已存在 | 可作为旧版参考，但 v3 要求放入 `.claude/skills/thesis-review-revision/SKILL.md` |
| `src/parser/` | 已有 PDF/DOCX/盲审意见解析类 | 可复用部分逻辑，但 v3 优先要求 `scripts/extract_*.py` CLI 工具 |
| `src/analyzer/` | 已有格式检查和论文分析 | 可参考规则，但需适配 v3 JSON artifact 流程 |
| `src/suggestor/ai_client.py` | 已有 AI API 抽象 | 与 v3 硬性要求冲突，应停用或移出 MVP 路线 |
| `src/suggestor/suggestion_engine.py` | Python 内生成 AI 修改建议 | 与 v3 冲突，v3 应由 `revision-planner` sub-agent 完成 |
| `tests/` | 已有旧版 pytest | 需要扩展或重写为 v3 scripts/schemas/fixtures 测试 |
| `.claude/agents/` | 未发现 v3 6 个 agent 定义 | P0 必须创建 |
| `.claude/skills/thesis-review-revision/` | 未发现 v3 skill 目录 | P0 必须创建 |
| `schemas/` | 未发现 v3 schema | P0/P1 必须创建 |
| `scripts/` | 未发现 v3 scripts | P1/P2 必须创建 |
| `README.md` | 未发现 | P0/P3 必须创建 |

结论：后续应把现有代码视为“可借鉴的旧实现”，不能直接沿旧计划继续扩展 AI API 模式。

## 4. 目标交付结构

MVP 目标结构以 v3 规格为准：

```text
.claude/
├── skills/
│   └── thesis-review-revision/
│       ├── SKILL.md
│       ├── schemas/
│       ├── templates/
│       └── examples/
└── agents/
    ├── review-parser.md
    ├── paper-indexer.md
    ├── comment-mapper.md
    ├── revision-planner.md
    ├── quality-auditor.md
    └── response-writer.md

scripts/
├── extract_pdf.py
├── extract_docx.py
├── extract_txt.py
├── chunk_paper.py
├── validate_json.py
├── format_checker.py
├── render_report.py
├── annotate_pdf.py
└── patch_docx.py

src/
├── __init__.py
├── models.py
├── io_utils.py
├── paper_index.py
├── retrieval.py
├── report.py
└── docx_patch.py

tests/
├── fixtures/
└── test_*.py

workdir/
└── .gitkeep

pyproject.toml
requirements.txt
README.md
IMPLEMENTATION_NOTES.md
```

## 5. 标准运行流程

一次完整运行应形成以下数据流：

```text
1. 用户提供论文和盲审意见文件
2. Orchestrator 创建 workdir/<run_id>/
3. 复制输入文件到 inputs/
4. Python 提取文本到 extracted/
5. Python 切分论文到 chunks/ 和 artifacts/paper_chunks.json
6. paper-indexer 生成 artifacts/paper_index.json
7. review-parser 生成 artifacts/review_comments.json
8. comment-mapper 生成 artifacts/comment_mappings.json
9. revision-planner 逐条生成 revision_plans/<comment_id>.json
10. validate_json.py 校验所有 JSON
11. quality-auditor 生成 artifacts/quality_report.json
12. 如有 blocker，只重试受影响意见或标为作者待补充
13. response-writer 生成 outputs/*.md
14. Python 渲染 outputs/*.html / *.docx / *.pdf
15. Orchestrator 汇总产物路径和限制说明
```

## 6. 分阶段实施计划

### Phase 0：文档和边界确认

目标：锁定 v3 为唯一实现依据，避免继续扩展旧架构。

产物：

- 本流程文档
- 明确旧计划中的 AI API 模式暂不进入 MVP
- 明确后续阶段的验收标准

验收：

- 文档说明当前实现与 v3 的差异
- 后续任务可按阶段执行

### Phase 1：P0 Skill 骨架

目标：先让 Claude Code Skill 项目结构成立。

任务：

- 创建 `.claude/skills/thesis-review-revision/SKILL.md`
- 创建 6 个 `.claude/agents/*.md`
- 创建 schema 目录和模板目录
- 创建 examples 目录
- 创建 `README.md`
- 创建 `IMPLEMENTATION_NOTES.md`

验收：

- 6 个 agent 文件职责清晰，且不允许继续派发 sub-agent
- Skill frontmatter 不包含 `context: fork`
- Skill 明确 Orchestrator 是主会话
- README 明确安装、使用、输出和学术诚信限制

### Phase 2：P0/P1 JSON Schema

目标：所有 sub-agent 输出均可校验。

任务：

- 完整实现 `review_comments.schema.json`
- 实现 `paper_index.schema.json`
- 实现 `comment_mappings.schema.json`
- 实现 `revision_plan.schema.json`
- 实现 `quality_report.schema.json`
- 实现 `final_report.schema.json`
- 创建 examples JSON 并确保能通过校验

验收：

- schema 使用 draft 2020-12
- 关键字段 required
- 枚举锁定
- `confidence` 限制在 `[0, 1]`
- 默认 `additionalProperties: false`

### Phase 3：P1 确定性脚本 MVP

目标：建立不依赖 AI 的文件处理流水线。

任务：

- `scripts/extract_txt.py`
- `scripts/extract_docx.py`
- `scripts/extract_pdf.py`
- `scripts/chunk_paper.py`
- `scripts/validate_json.py`
- `scripts/render_report.py`

验收：

- TXT/DOCX/PDF 可提取为规范 JSON 或 TXT
- chunk 输出包含 `chunk_id`、页码范围、标题猜测、文本路径、字数
- JSON 校验脚本失败时返回 exit code 1 并打印错误路径
- Markdown 可以渲染为 HTML

### Phase 4：P2 辅助输出和格式检查

目标：补齐基础质量检查和辅助文档输出。

任务：

- `scripts/format_checker.py`
- `scripts/patch_docx.py`
- `scripts/annotate_pdf.py`
- 对应 `src/report.py`、`src/docx_patch.py` 等可复用逻辑

验收：

- format checker 能输出 `format_issues.json`
- DOCX 修改建议版以表格形式输出，不直接伪造最终修改
- PDF 标注基础版只按页添加批注，不承诺精准坐标

### Phase 5：P3 测试和 fixtures

目标：让 MVP 可持续验证。

任务：

- 创建 `tests/fixtures/`
- 添加 sample paper/review 和 sample artifacts
- 实现脚本级 pytest
- 覆盖 schema 校验、文本提取、chunk、格式检查、报告渲染

验收：

- `pytest` 全部通过
- v3 规格中列出的手动命令可正常执行

### Phase 6：集成演练

目标：用示例文件跑通非 AI 的确定性部分，并形成手动 Orchestrator 操作说明。

任务：

- 用 mock JSON artifact 跑通 reports 输出
- 在 `IMPLEMENTATION_NOTES.md` 记录一次端到端流程
- 标明哪些步骤需要 Claude Code sub-agent 人工编排

验收：

- `workdir/test/` 结构符合规范
- 至少生成 `outputs/修改报告.md` 和 `outputs/修改报告.html`
- 明确未接入真实 sub-agent 时的手动替代步骤

## 7. 实现顺序

建议严格按以下顺序推进：

1. 先补 v3 目录结构和文档骨架。
2. 再补 JSON Schema，因为后续 agent 和测试都依赖 schema。
3. 再写 Python scripts，先做最小可用的确定性管道。
4. 再补 tests/fixtures，保证每个确定性脚本可测。
5. 最后处理 PDF 标注、DOCX 建议稿等增强功能。

不要先改 `src/suggestor` 或扩展 AI API 调用。该方向与 v3 目标冲突。

## 8. 风险和处理策略

| 风险 | 处理策略 |
|---|---|
| 旧计划与 v3 规格冲突 | 以 v3 规格为准，旧计划只作参考 |
| 现有代码含 AI API 调用 | MVP 阶段不删除，但不作为主流程依赖 |
| PDF 是扫描版 | 提取脚本给出 warning，不在 MVP 做 OCR |
| DOCX 页码不可可靠获取 | 页码设为 null，保留段落和标题信息 |
| sub-agent 输出不合法 JSON | 必须用 schema 校验，不通过则重试该步骤 |
| 修改建议可能过度承诺 | quality-auditor 阶段拦截，并要求区分“拟修改”和“已修改” |

## 9. 后续执行检查清单

- [ ] Phase 1：创建 v3 Skill 骨架
- [ ] Phase 2：创建 JSON Schema 和 examples
- [ ] Phase 3：实现提取、chunk、校验、渲染脚本
- [ ] Phase 4：实现格式检查、DOCX 建议稿、PDF 标注基础版
- [ ] Phase 5：补 tests/fixtures 并跑通 pytest
- [ ] Phase 6：端到端集成演练并记录结果

## 10. 当前决策记录

- 决策 1：v3 规格是后续唯一实现依据。
- 决策 2：Python 工具不再新增 AI API 调用。
- 决策 3：现有旧版 `src/suggestor` 暂不进入 MVP 主流程。
- 决策 4：所有可审查中间结果统一落盘到 `workdir/<run_id>/`。
- 决策 5：先做可运行 MVP，再做高级检索、OCR、精准 PDF 坐标、DOCX 保留样式修改。
