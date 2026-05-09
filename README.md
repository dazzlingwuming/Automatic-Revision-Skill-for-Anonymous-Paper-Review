# Automatic Revision Skill for Anonymous Paper Review

这是一个面向学位论文/论文盲审意见修改的 **通用 Agent Pipeline**。它可以读取论文 DOCX 和盲审意见文件，生成逐条修改方案、盲审回复表、修改报告，以及一个带高亮建议的 Word 文档。

项目不是单纯的 Claude Code Skill。更准确地说：

- `agent_specs/` 是通用 agent 定义，Claude、Codex 或其他宿主都可以读取。
- `.claude/` 是 Claude Code 适配层，用来让 Claude Code 以 Skill/Agent 方式调用本项目。
- `scripts/` 和 `src/` 是确定性 Python 工具层，负责 DOCX 解析、意见解析、映射、校验、报告渲染和 Word 输出。

## 适用场景

- 论文已经收到盲审意见，需要逐条生成修改方案。
- 希望从 Word 文档入手，而不是依赖 PDF 解析。
- 需要生成盲审回复表、修改报告、作者待补充事项。
- 希望把“修改方案生成”和“修改质量审查”拆成 planner/auditor 两个 agent。

## 安装

建议使用 Python 3.12+ 或 3.13。

```bash
pip install -r requirements.txt
```

如果在 Claude Code 中使用，可同步通用 agent 定义到 `.claude/agents`：

```bash
python scripts/sync_agent_adapters.py
```

## 快速开始

最常用入口是：

```bash
python scripts/run_pipeline.py ^
  --paper-docx ./paper.docx ^
  --review ./review.pdf ^
  --out workdir/example-run ^
  --title "论文标题" ^
  --mode full
```

PowerShell 也可以写成单行：

```powershell
python scripts\run_pipeline.py --paper-docx .\paper.docx --review .\review.pdf --out workdir\example-run --title "论文标题" --mode full
```

## 输入文件

必需：

- `--paper-docx`：论文 Word 文件。DOCX 是主解析来源。
- `--review`：盲审意见文件，支持 PDF、DOCX、TXT、Markdown。
- `--out`：输出目录。

可选：

- `--title`：论文标题，用于报告展示。
- `--mode`：运行模式。

## 运行模式

```text
prepare  只做确定性准备：DOCX 解析、盲审意见解析、意见定位、scaffold 修改方案
report   基于已有 revision_plans 生成可读卡片、审查结果、报告和 Word 建议版
full     prepare + report，一次跑完整个确定性流程
```

当前 `full` 是稳定的确定性流程。深度 agent 闭环的设计已经放在 `agent_specs/` 和 `.claude/agents/` 中，宿主 agent 可以在 `prepare` 后逐条调用 `deep-revision-planner` 和 `revision-solution-auditor`。

## 输出看哪里

用户主要看这几个目录：

```text
workdir/example-run/
├── outputs/
│   ├── 修改报告.md
│   ├── 盲审回应表.md
│   ├── 作者待补充事项.md
│   └── 05_修改建议版.docx
├── revision_plan_notes/
│   ├── R1-C001.md
│   ├── R1-C002.md
│   └── ...
└── audits/
    └── revision_solution_audit.json
```

说明：

- `outputs/修改报告.md`：总报告，适合整体查看。
- `outputs/盲审回应表.md`：按盲审回复格式整理。
- `outputs/作者待补充事项.md`：列出需要真实数据、实验结果、图源文件、参考文献核实的内容。
- `outputs/05_修改建议版.docx`：在 Word 中生成的高亮建议版。
- `revision_plan_notes/*.md`：每一条意见的可读修改卡片。

不建议直接阅读这些内部目录：

```text
paper/
assets/
artifacts/
revision_plans/
review/
```

这些主要给程序使用，其中 `revision_plans/*.json` 是内部结构化数据，不是面向用户阅读的最终文本。

## 架构说明

整体流程：

```text
论文 DOCX
  ↓
DOCX-first 结构化解析
  ↓
章节树 / 图表资产 / 正文 Markdown
  ↓
盲审意见解析
  ↓
意见到章节、图表、参考文献的映射
  ↓
修改方案 JSON / Markdown 卡片
  ↓
质量审查
  ↓
修改报告 / 回复表 / Word 建议版
```

通用 agent 设计：

```text
agent_specs/
├── workflow.md
└── agents/
    ├── deep-revision-planner.md
    ├── revision-solution-auditor.md
    └── ...
```

Claude Code 适配层：

```text
.claude/
├── skills/thesis-review-revision/SKILL.md
└── agents/
```

`agent_specs/` 是更通用的事实源；`.claude/agents` 可以通过 `scripts/sync_agent_adapters.py` 从它同步。

## 常用命令

完整流程：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/example-run --title "论文标题" --mode full
```

只做准备：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/example-run --title "论文标题" --mode prepare
```

只生成报告：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/example-run --mode report
```

把内部 JSON 修改方案渲染成人可读 Markdown：

```bash
python scripts/render_revision_plan_notes.py --revision-plans-dir workdir/example-run/revision_plans --output-dir workdir/example-run/revision_plan_notes
```

校验 agent 输出 JSON：

```bash
python scripts/validate_agent_json.py --schema .claude/skills/thesis-review-revision/schemas/revision_plan.schema.json --input workdir/example-run/revision_plans/R1-C001.json
```

运行测试：

```bash
python -m pytest -q
```

## 学术诚信边界

本项目不会，也不应该：

- 编造实验结果；
- 编造数据；
- 编造参考文献信息；
- 编造图表源文件；
- 编造页码；
- 把“拟修改”说成“已修改”。

如果某条盲审意见需要真实实验、真实数据、导师决策、图源文件或参考文献核实，系统应将其列入 `作者待补充事项.md`。

## 当前限制

- PDF-only 模式质量较低，推荐始终提供 DOCX。
- DOCX 本身没有可靠页码信息；如果需要精确页码，需要额外提供排版一致的 PDF 做对照。
- `05_修改建议版.docx` 是高亮建议版，不是 Word 修订模式的 tracked changes。
- `full` 当前主要是确定性流程；深度 planner/auditor agent 闭环需要宿主 agent 调度。

## 不会上传的本地内容

`.gitignore` 默认排除了：

- `workdir/`
- `output/`
- `例子/`
- `.idea/`
- `.pytest_cache/`
- `.claude/settings.local.json`

因此真实论文、盲审文件、运行产物和本地配置不会进入公开仓库。
