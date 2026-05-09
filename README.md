# Automatic Revision Skill for Anonymous Paper Review

这是一个用于处理论文/学位论文盲审意见的 **Skill + Agent Pipeline**。

新用户可以把它理解成：

```text
Skill 是入口：告诉 Claude Code、Codex 或其他 Agent 什么时候使用、怎么使用。
Agent Pipeline 是执行体：负责解析 DOCX、处理盲审意见、生成深度修改方案、输出报告和 DOCX 修改稿。
```

所以它既不是单纯的 Python 脚本，也不是只适用于 Claude Code 的 `.claude` 配置。推荐用法是：

- 在 **Claude Code** 中，通过 `.claude/skills/thesis-review-revision/SKILL.md` 作为 Skill 使用。
- 在 **Codex 或其他 Agent** 中，让 Agent 读取根目录 `SKILL.md` 或 `agent_specs/workflow.md`，再调用本项目脚本。
- 如果不使用 Agent，也可以直接运行 `scripts/run_pipeline.py`。

## 一句话使用

把论文 DOCX 和盲审意见文件放进项目目录，然后在 Claude Code / Codex 里说：

```text
请使用这个盲审论文修改 skill，处理 paper.docx 和 review.pdf，输出到 workdir/run1。
```

Agent 应该根据 Skill 说明执行底层命令，而不是让用户手动理解所有脚本。

## 1. Claude Code 用户怎么用

### 方式 A：直接在本仓库里使用

1. 克隆仓库：

```bash
git clone git@github.com:dazzlingwuming/Automatic-Revision-Skill-for-Anonymous-Paper-Review.git
cd Automatic-Revision-Skill-for-Anonymous-Paper-Review
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 同步通用 agent 定义到 Claude Code agent 目录：

```bash
python scripts/sync_agent_adapters.py
```

4. 把论文和盲审意见放到项目里，例如：

```text
paper.docx
review.pdf
```

5. 在 Claude Code 里说：

```text
使用 thesis-review-revision skill，处理 paper.docx 和 review.pdf，输出到 workdir/run1。
```

Claude Code 应读取：

```text
.claude/skills/thesis-review-revision/SKILL.md
```

并按里面的流程调用：

```bash
python scripts/run_pipeline.py --paper-docx paper.docx --review review.pdf --out workdir/run1 --title "论文标题" --mode full
```

### 方式 B：把 Skill 复制到别的 Claude Code 项目

如果你的论文项目在另一个目录，可以复制这些内容：

```text
.claude/skills/thesis-review-revision/
.claude/agents/
agent_specs/
scripts/
src/
requirements.txt
```

然后在那个项目中运行：

```bash
pip install -r requirements.txt
python scripts/sync_agent_adapters.py
```

再让 Claude Code 使用 `thesis-review-revision` 处理论文和盲审意见。

## 2. Codex 用户怎么用

Codex 不一定识别 `.claude/skills`，所以不要只依赖 `.claude` 目录。

在 Codex 中推荐这样使用：

1. 克隆仓库并安装依赖：

```bash
git clone git@github.com:dazzlingwuming/Automatic-Revision-Skill-for-Anonymous-Paper-Review.git
cd Automatic-Revision-Skill-for-Anonymous-Paper-Review
pip install -r requirements.txt
```

2. 把论文和盲审意见放到仓库目录，例如：

```text
paper.docx
review.pdf
```

3. 对 Codex 说：

```text
请读取根目录 SKILL.md 和 agent_specs/workflow.md，
使用这个盲审论文修改 skill，
处理 paper.docx 和 review.pdf，
输出到 workdir/run1。
```

Codex 应该执行的稳定底层入口是：

```bash
python scripts/run_pipeline.py --paper-docx paper.docx --review review.pdf --out workdir/run1 --title "论文标题" --mode full
```

如果需要深度 agent 审核闭环，Codex 应继续读取：

```text
agent_specs/agents/deep-revision-planner.md
agent_specs/agents/revision-solution-auditor.md
```

并在 `prepare` 后逐条调度 planner 和 auditor。

## 3. 不使用 Agent，直接命令行运行

如果只是想先跑确定性流程，可以直接执行：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/run1 --title "论文标题" --mode full
```

Windows PowerShell：

```powershell
python scripts\run_pipeline.py --paper-docx .\paper.docx --review .\review.pdf --out workdir\run1 --title "论文标题" --mode full
```

## 4. 输入文件

必需：

- `--paper-docx`：论文 Word 文件。DOCX 是主解析来源。
- `--review`：盲审意见文件，支持 PDF、DOCX、TXT、Markdown。
- `--out`：输出目录。

可选：

- `--title`：论文标题。
- `--mode`：运行模式。

## 5. 运行模式

```text
prepare  只做确定性准备：DOCX 解析、盲审意见解析、意见定位、scaffold 修改方案
report   基于已有 revision_plans 生成可读卡片、审查结果、报告和 Word 建议版
full     prepare + report，一次跑完整个确定性流程
```

当前 `full` 是稳定的确定性流程，会生成 scaffold 草稿和可检查输出，但不能代表最终深度修改质量。想要达到“完整修改版本”的效果，宿主 Agent 必须在 `prepare` 后调度 `deep-revision-planner` 和 `revision-solution-auditor`，直到审计通过或明确需要作者补真实材料。

## 6. 输出看哪里

用户主要看：

```text
workdir/run1/
├── outputs/
│   ├── 修改报告.md
│   ├── 盲审回应表.md
│   ├── 作者待补充事项.md
│   ├── 05_修改建议版.docx
│   └── 06_整合修改稿.docx
├── revision_plan_notes/
│   ├── R1-C001.md
│   ├── R1-C002.md
│   └── ...
└── audits/
    └── revision_solution_audit.json
```

说明：

- `outputs/修改报告.md`：总修改报告。
- `outputs/盲审回应表.md`：给盲审回复使用的表格。
- `outputs/作者待补充事项.md`：需要作者提供真实材料的清单。
- `outputs/05_修改建议版.docx`：Word 高亮建议版。
- `outputs/06_整合修改稿.docx`：把不需要作者补材料的修改直接整合进 DOCX 副本；需要真实实验、数据、图源或参考文献核实的内容会跳过并留在待补充事项中。
- `revision_plan_notes/*.md`：每条意见的可读修改卡片。

内部目录一般不用直接看：

```text
paper/
assets/
artifacts/
revision_plans/
review/
```

其中 `revision_plans/*.json` 是程序内部数据，不是给用户直接阅读的最终结果。

## 7. 项目结构

```text
.
├── SKILL.md                         # 通用 Skill 入口，适合 Codex/通用 Agent 读取
├── agent_specs/                     # 通用 agent 定义
│   ├── workflow.md
│   └── agents/
├── .claude/                         # Claude Code 适配层
│   ├── skills/thesis-review-revision/SKILL.md
│   └── agents/
├── scripts/                         # 确定性命令行工具
├── src/                             # Python 实现
├── tests/                           # 测试
└── requirements.txt
```

## 8. 架构流程

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
深度修改方案 JSON / Markdown 卡片
  ↓
质量审查，不合格则打回重写
  ↓
修改报告 / 回复表 / Word 建议版 / 整合修改稿
```

## 9. 常用命令

完整流程：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/run1 --title "论文标题" --mode full
```

只做准备：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/run1 --title "论文标题" --mode prepare
```

只生成报告：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/run1 --mode report
```

把内部 JSON 修改方案渲染成人可读 Markdown：

```bash
python scripts/render_revision_plan_notes.py --revision-plans-dir workdir/run1/revision_plans --output-dir workdir/run1/revision_plan_notes
```

运行测试：

```bash
python -m pytest -q
```

## 10. 学术诚信边界

本项目不会，也不应该：

- 编造实验结果；
- 编造数据；
- 编造参考文献信息；
- 编造图表源文件；
- 编造页码；
- 把“拟修改”说成“已修改”。

如果某条盲审意见需要真实实验、真实数据、导师决策、图源文件或参考文献核实，系统应将其列入 `作者待补充事项.md`。

## 11. 当前限制

- PDF-only 模式质量较低，推荐始终提供 DOCX。
- DOCX 本身没有可靠页码信息；如需精确页码，需要额外提供排版一致的 PDF 做对照。
- `修改建议版.docx` 是高亮建议版，不是 Word 修订模式 tracked changes。
- `整合修改稿.docx` 是自动整合副本，只会写入无需作者补真实材料的修改。
- `full` 当前主要是确定性流程；最终质量依赖宿主 Agent 调度深度 planner/auditor 闭环。

