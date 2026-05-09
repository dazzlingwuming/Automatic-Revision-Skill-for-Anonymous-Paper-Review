# CLAUDE.md

## 项目概述

**盲审论文修改 Agent Pipeline** — 一个通用 Agent 流水线 + Claude Code Skill 适配器 + Python 确定性工具项目，帮助研究生高效完成盲审论文的修改任务。

基于 Python 3.13。

当前实现以 v3.4 provider-neutral Agent Pipeline 规格为准：`agent_specs/` 是通用 agent 定义事实源，`.claude/` 只是 Claude Code 适配层。任意宿主 agent（Claude Code、Codex 或其他应用）都可以读取 `agent_specs/` 并调用 `scripts/run_pipeline.py`。Python 工具层只负责 DOCX 结构化 ingest、图表资产提取、Markdown/JSON 转换、schema 校验、格式检查、确定性质量预审、报告渲染、PDF/DOCX 辅助输出等确定性工作。PDF 不再作为高质量主结构源。

## 核心组件

| 组件 | 路径 | 说明 |
|------|------|------|
| 通用 Agent 定义 | `agent_specs/` | provider-neutral workflow 和 agent specs，供 Claude、Codex 或其他宿主读取 |
| Claude Skill 适配器 | `.claude/skills/thesis-review-revision/SKILL.md` | Claude Code 的触发入口和工作流说明 |
| Claude Agent 适配器 | `.claude/agents/` | 由 `agent_specs/agents` 同步得到的 Claude Code agent 文件 |
| JSON Schema | `.claude/skills/thesis-review-revision/schemas/` | sub-agent 输出校验 |
| 脚本工具 | `scripts/` | v3/v3.2 确定性 CLI 工具 |
| 旧版 Skill 定义 | `SKILL.md` | 早期版本参考 |
| 设计文档 | `docs/superpowers/specs/` | 架构设计和需求规格 |
| 实现计划 | `docs/superpowers/plans/` | 按任务拆分的实现计划 |
| DOCX-first ingest | `src/docx_ingestion/` | Word 原始顺序 blocks、章节树、Markdown、图表资产 |
| Python 工具 | `src/` | 可复用 helper、patching 和旧版模块 |
| 测试 | `tests/` | pytest 单元测试 |

## 项目结构

```
盲审论文修改skill/
├── SKILL.md                        # Skill 核心定义
├── CLAUDE.md                       # 项目说明（本文件）
├── main.py                         # CLI 入口
├── requirements.txt                # Python 依赖
├── pyproject.toml                  # pytest 配置
├── README.md                       # v3 使用说明
├── IMPLEMENTATION_NOTES.md         # v3 实现备注
├── .claude/
│   ├── skills/thesis-review-revision/
│   │   ├── SKILL.md                # v3 Skill 定义
│   │   ├── schemas/                # JSON Schema
│   │   ├── templates/              # 报告模板
│   │   └── examples/               # 示例 JSON
│   └── agents/                     # 6 个 v3 sub-agent
├── scripts/                        # v3 确定性工具脚本
├── docs/superpowers/
│   ├── specs/                      # 设计文档
│   └── plans/                      # 实现计划
├── src/
│   ├── __init__.py
│   ├── cli.py                      # 命令行参数解析
│   ├── models.py                   # 数据模型定义
│   ├── parser/                     # 解析层
│   │   ├── pdf_parser.py           #   PDF 解析
│   │   ├── docx_parser.py          #   Word 解析
│   │   └── review_parser.py        #   盲审意见解析
│   ├── analyzer/                   # 分析层
│   │   ├── format_checker.py       #   格式检查
│   │   └── paper_analyzer.py       #   论文-意见映射
│   ├── docx_ingestion/             # v3.2 DOCX-first 结构化 ingest
│   ├── patching/                   # Word 建议版输出
│   ├── suggestor/                  # 旧版建议层（不属于 v3 MVP 主流程）
│   │   ├── ai_client.py            #   AI API 抽象接口
│   │   └── suggestion_engine.py    #   修改建议生成
│   └── reporter/                   # 输出层
│       ├── report_generator.py     #   报告生成 (MD/HTML)
│       ├── pdf_annotator.py        #   PDF 标注
│       └── templates/report.html   #   HTML 模板
├── tests/                          # 测试
│   ├── conftest.py                 #   测试夹具
│   ├── test_models.py              #   数据模型测试
│   ├── test_pdf_parser.py          #   PDF 解析测试
│   ├── test_review_parser.py       #   盲审意见解析测试
│   ├── test_format_checker.py      #   格式检查测试
│   └── test_suggestion_engine.py   #   建议引擎测试
└── 例子/
    ├── 盲审版本.pdf
    └── 盲审评价.pdf
```

## 命令

| 命令 | 说明 |
|------|------|
| `python main.py -h` | 查看 CLI 帮助 |
| `python main.py --paper 论文.pdf --review 意见.pdf` | 完整处理流程 |
| `python main.py --paper 论文.pdf --review 意见.pdf --format-only` | 仅格式检查 |
| `python scripts/ingest_docx.py --paper 论文.docx --out workdir\run` | DOCX-first 结构化 ingest |
| `python scripts/run_docx_first_prepare.py --paper-docx 论文.docx --review 意见.pdf --out workdir\run` | DOCX-first deterministic prepare |
| `python scripts/run_pipeline.py --paper-docx 论文.docx --review 意见.pdf --out workdir\run --mode full` | 通用流水线入口：prepare + report + Word 建议版 |
| `python scripts/sync_agent_adapters.py` | 将 `agent_specs/agents` 同步到 `.claude/agents` |
| `python scripts/audit_revision_solutions.py --revision-plans-dir workdir\run\revision_plans --output workdir\run\audits\revision_solution_audit.json` | 深度修改方案预审 |
| `python scripts/patch_docx.py --input-docx 论文.docx --revision-plans-dir workdir\run\revision_plans --output workdir\run\outputs\05_修改建议版.docx` | 生成高亮建议版 Word |
| `python -m pytest tests -q --basetemp workdir\pytest-tmp` | 运行测试，临时文件留在项目内 |
| `pip install -r requirements.txt` | 安装依赖 |

## 架构

v3.4 处理流水线：**DOCX 原始顺序解析 → 章节树 → 图表资产 → Markdown/section files → 章节摘要 → 意见解析 → 多位置映射 → context bundle → deep-revision-planner 输出 Markdown 修改卡片 → parse 成内部 JSON → revision-solution-auditor → 不合格打回重写 → 质量审计 → 报告和建议版 Word**

输入（DOCX 论文 + 盲审意见）→ Python 生成结构化论文 artifacts → sub-agent 生成可读 Markdown 修改卡片 → Python 转内部 JSON → schema 校验 → Python 渲染报告和建议版 DOCX。

## Skill 使用

当用户在 Claude Code 中提出盲审论文修改相关需求时，Claude 应遵循 `.claude/skills/thesis-review-revision/SKILL.md` 中定义的适配流程；当用户在 Codex 或其他宿主中使用时，直接读取 `agent_specs/workflow.md` 并调用 `scripts/run_pipeline.py`：
1. 收集输入（论文 + 盲审意见）
2. 解析和分类评审意见
3. 分析论文内容，定位问题
4. 生成具体的修改建议
5. 执行格式检查
6. 输出完整的修改报告

## 开发约定

- 中文项目，代码注释和文档优先使用中文
- 使用 PyCharm (Python 3.13) 开发
- 遵循 v3/v3.2 artifact 管道，阶段间通过 `workdir/<run_id>/` 下的 JSON 文件通信
- 论文主事实源优先使用 DOCX；PDF-only 只能作为 degraded mode
- Python 工具不得新增 AI API 调用
- 旧版 `src/suggestor` 仅保留为历史参考，不作为 v3 MVP 主流程依赖
