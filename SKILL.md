---
name: blind-review-paper-revision
description: Use when a user needs to revise an academic paper or thesis based on anonymous/blind review feedback. This skill guides an agent to run the provider-neutral revision pipeline, generate revision cards, reviewer responses, reports, and DOCX suggestion output.
---

# Blind Review Paper Revision Skill

This is the provider-neutral Skill entry for Codex-style agents, Claude Code, or any other agent host.

The executable system is an Agent Pipeline:

- `agent_specs/` contains portable workflow and agent definitions.
- `.claude/` contains Claude Code adapter files.
- `scripts/` and `src/` contain deterministic Python tools.

## When To Use

Use this skill when the user provides:

- a thesis/paper manuscript, preferably DOCX;
- anonymous/blind review comments in PDF, DOCX, TXT, or Markdown;
- a request to generate revision suggestions, reviewer responses, revision reports, or a Word suggestion copy.

Do not use this for generic proofreading without review comments.

## User-Facing Behavior

The user should not need to understand every script. If they say:

```text
请使用这个盲审论文修改 skill，处理 paper.docx 和 review.pdf，输出到 workdir/run1。
```

the orchestrating agent should:

1. Read this `SKILL.md`.
2. Read `agent_specs/workflow.md`.
3. Confirm the manuscript and review files exist.
4. Run the deterministic pipeline.
5. Return the output paths that matter to the user.

## Stable Command

The stable deterministic entrypoint is:

```bash
python scripts/run_pipeline.py --paper-docx <paper.docx> --review <review.pdf|review.docx|review.txt|review.md> --out <workdir/run-id> --title "<title>" --mode full
```

Use `--mode prepare` when the host agent will run deep planner/auditor agents after preparation.

Use `--mode report` when valid `revision_plans/*.json` already exist and only final outputs need to be rendered.

## Important Output Paths

Return these to the user:

- `workdir/<run-id>/outputs/修改报告.md`
- `workdir/<run-id>/outputs/盲审回应表.md`
- `workdir/<run-id>/outputs/作者待补充事项.md`
- `workdir/<run-id>/outputs/05_修改建议版.docx`
- `workdir/<run-id>/revision_plan_notes/*.md`

Internal JSON directories such as `paper/`, `assets/`, `artifacts/`, `revision_plans/`, and `review/` are implementation artifacts.

## Deep Agent Loop

For higher-quality revision plans, after `--mode prepare`:

1. For each review comment, use `agent_specs/agents/deep-revision-planner.md`.
2. The planner should write a structured Markdown revision card under `revision_plan_notes/`.
3. Convert it to JSON with `scripts/parse_revision_plan_markdown.py`.
4. Validate JSON with `scripts/validate_agent_json.py`.
5. Audit with `agent_specs/agents/revision-solution-auditor.md`.
6. If the audit says `revise`, retry the planner with the audit's `retry_instruction`.
7. Render final outputs with `scripts/run_pipeline.py --mode report`.

## Non-Negotiable Rules

- Treat DOCX as the primary thesis source.
- Do not fabricate experiments, data, references, figures, tables, statistics, page numbers, or completed revisions.
- If real data, new experiments, source figures, references, or author decisions are missing, put them in `作者待补充事项.md`.
- Do not claim "已修改" unless changes were actually applied.
- Prefer user-facing Markdown cards and reports over raw JSON.
