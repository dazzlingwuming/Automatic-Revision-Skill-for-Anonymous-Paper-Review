# Automatic Revision Skill for Anonymous Paper Review

一个用于处理论文/学位论文盲审意见的 **Skill**。

把论文 DOCX 和盲审意见交给支持 Skill 的 Agent，它会根据本仓库的 `SKILL.md` 和配套流水线完成：

- 解析论文结构和盲审意见；
- 将每条意见定位到论文相关章节、图表或参考文献；
- 生成逐条修改方案、可写入正文的建议文本和盲审回应；
- 标出需要作者补充的真实实验、数据、图源或参考文献信息；
- 输出修改报告、盲审回应表、Word 修改建议版和整合修改稿。

这个项目不是论文代写工具。它不会编造实验结果、数据、参考文献、图表或页码。

## 快速开始

### 1. 下载项目

```bash
git clone git@github.com:dazzlingwuming/Automatic-Revision-Skill-for-Anonymous-Paper-Review.git
cd Automatic-Revision-Skill-for-Anonymous-Paper-Review
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 放入论文和盲审意见

例如：

```text
paper.docx
review.pdf
```

推荐使用 DOCX 作为论文主文件。盲审意见支持 PDF、DOCX、TXT 或 Markdown。

### 4. 让 Agent 使用这个 Skill

在支持 Skill 的 Agent 中直接说：

```text
请使用这个盲审论文修改 skill，处理 paper.docx 和 review.pdf，输出到 workdir/run1。
```

Agent 会读取 `SKILL.md`，并按项目内的工作流和脚本完成处理。你不需要手动理解每一个脚本。

## 输出内容

处理完成后，重点查看：

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

- `修改报告.md`：总修改报告，包含每条意见的诊断、定位和修改方案。
- `盲审回应表.md`：可用于整理提交给评审/学院的回应说明。
- `作者待补充事项.md`：列出必须由作者提供真实材料的事项。
- `05_修改建议版.docx`：在论文副本中插入高亮修改建议，适合逐条审阅。
- `06_整合修改稿.docx`：把无需作者补材料的修改直接整合进论文副本，适合继续编辑。
- `revision_plan_notes/*.md`：每条盲审意见的可读修改卡片。

内部目录如 `paper/`、`assets/`、`artifacts/`、`revision_plans/`、`review/` 主要供流水线使用，通常不用直接阅读。

## 适用场景

适合：

- 硕士/博士论文盲审返修；
- 期刊或会议论文审稿意见返修；
- 需要生成逐条修改方案、回应表和 Word 建议稿的场景；
- 希望把“意见拆解、论文定位、修改建议、待补事项”标准化的场景。

不适合：

- 没有审稿/盲审意见的普通润色；
- 需要编造实验结果或参考文献信息的请求；
- 只提供 PDF 论文、没有 DOCX 原稿且要求高质量结构化修改的场景。

## 工作流概览

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
逐条深度修改方案
  ↓
质量审查
  ↓
修改报告 / 回应表 / Word 修改建议版 / 整合修改稿
```

## 高级用法：直接运行脚本

如果你想调试流水线，或在没有 Agent 的环境中先跑确定性流程，可以直接执行：

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/run1 --title "论文标题" --mode full
```

常用模式：

```text
prepare  只做准备：解析 DOCX、解析意见、生成初始修改方案
report   基于已有 revision_plans 生成报告和 Word 输出
full     prepare + report
```

说明：`full` 可以生成稳定的结构化草稿和输出文件；如果要达到更高质量的逐条深度修改效果，应让 Agent 按 `SKILL.md` 中的 deep planner/auditor 流程继续深化每条意见。

## 学术诚信边界

本项目不会，也不应该：

- 编造实验结果；
- 编造数据；
- 编造参考文献信息；
- 编造图表源文件；
- 编造页码；
- 在未实际修改时声称“已修改”。

如果某条盲审意见需要真实实验、真实数据、导师决策、图源文件或参考文献核实，系统会把它列入 `作者待补充事项.md`。

## 项目结构

```text
.
├── SKILL.md          # Skill 入口
├── agent_specs/      # Agent 工作流和角色定义
├── scripts/          # 确定性命令行工具
├── src/              # Python 实现
├── tests/            # 测试
└── requirements.txt  # Python 依赖
```

`.claude/` 目录是兼容适配内容，不影响把本仓库作为通用 Skill 使用。

## 当前限制

- 推荐始终提供 DOCX；PDF-only 模式结构化质量较低。
- DOCX 本身没有可靠页码信息；如需精确页码，建议额外提供排版一致的 PDF 做对照。
- `05_修改建议版.docx` 是高亮建议版，不是 Word 修订模式 tracked changes。
- `06_整合修改稿.docx` 只会整合不需要作者补真实材料的修改。
