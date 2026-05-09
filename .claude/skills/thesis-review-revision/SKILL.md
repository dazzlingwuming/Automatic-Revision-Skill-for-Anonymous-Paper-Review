---
name: thesis-review-revision
description: Process thesis or dissertation blind-review comments. Use when the user provides a DOCX manuscript and blind-review comments, and wants detailed analysis, manuscript-ready revisions, reviewer responses, or final DOCX outputs.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash(python *), Bash(pytest *), Agent(review-parser), Agent(paper-indexer), Agent(comment-mapper), Agent(revision-planner), Agent(deep-revision-planner), Agent(revision-solution-auditor), Agent(quality-auditor), Agent(response-writer)
---

# Thesis Blind Review Revision Skill

This is the Claude Code adapter for the provider-neutral Thesis Revision Agent Pipeline. The portable workflow and agent specs live under `agent_specs/`; `.claude/agents` is a Claude Code adapter copy.

You are the Orchestrator in the main Claude Code session.

Do not run this skill as `context: fork`. This workflow needs the main Claude Code session to spawn specialized subagents. Subagents must not spawn further subagents.

## Inputs

Accept the following arguments:

```text
$ARGUMENTS
```

Expected user inputs:

- thesis manuscript: DOCX is the primary high-quality source
- blind review comments: PDF, DOCX, TXT, or Markdown
- optional manuscript PDF: only for page/layout cross-checks and PDF annotation
- optional university formatting rules
- optional mode:
  - `--suggest-only`: only produce revision plans and reports
  - `--apply-docx`: attempt to create a DOCX revision draft
  - `--annotate-pdf`: attempt to create annotated PDF

## Core Workflow

1. Create `workdir/<run_id>/`.
2. Copy input files into `workdir/<run_id>/inputs/`.
3. If portable agent specs changed, run `python scripts/sync_agent_adapters.py`.
4. Use `scripts/run_pipeline.py --mode prepare` or equivalent deterministic scripts to build DOCX-first artifacts.
5. Use `review-parser` and `comment-mapper` only when deterministic review parsing or mapping needs agent refinement.
6. For each review comment, invoke `deep-revision-planner` independently and write human-readable Markdown cards under `revision_plan_notes/`.
7. Convert every planner Markdown card with `scripts/parse_revision_plan_markdown.py --input <note.md> --output <plan.json>`.
8. Validate every parsed planner JSON with `scripts/validate_agent_json.py` before any audit.
9. If JSON syntax or schema validation fails, first run `scripts/repair_common_agent_json.py` for common formatting issues such as unescaped inner quotes or `null` where an array is required; then re-run validation.
10. If local common repair still fails, generate a repair prompt and retry the same agent in Markdown repair-only mode. Do not continue to `revision-solution-auditor` until parsed JSON validation passes.
11. For each validated deep plan, invoke `revision-solution-auditor`.
12. If `revision-solution-auditor` returns `decision: revise`, retry only that `deep-revision-planner` task with `retry_instruction`; allow up to 3 attempts.
13. After every retry, parse Markdown to JSON and run `scripts/validate_agent_json.py` again before re-auditing.
14. If still not passing, mark the plan as `needs_author_input` or `manual_review` with exact reasons.
15. Use `quality-auditor` and deterministic `scripts/audit_revision_solutions.py` to detect hallucinations, unsupported claims, missing evidence, shallow advice, underdeveloped final edits, and over-promising.
16. Use `scripts/run_pipeline.py --mode report` or equivalent scripts to render final reports and DOCX outputs.
17. Return a concise summary and list all generated files.

## Hard Rules

- Never fabricate experiments, data, statistics, references, tables, figures, page numbers, or results.
- Treat DOCX as the main thesis fact source. Do not use PDF as the structural source when DOCX is available.
- If a review comment requires new experiments, extra data, author decision, or domain-specific facts not present in the manuscript, mark `requires_author_input: true`.
- Distinguish between `proposed revision` and `completed revision`.
- Every specific action must include source section, page range if available, and chunk id.
- Keep all intermediate artifacts as JSON files.
- Do not pass the full manuscript to every subagent.
- Do not ask the user to repeat paths already present in `$ARGUMENTS`.
- If a file cannot be extracted, report that exact limitation and continue with what is available.

## Non-Negotiable v3.1 Rules

1. Do not split thesis text by fixed character count.
2. Always build a section tree from headings, paragraphs, formulas, figures, and tables.
3. Every review comment must be mapped to multiple possible locations unless it is clearly local.
4. Every `revision-planner` call must receive:
   - paper brief;
   - global outline;
   - full text of core revision sections;
   - summaries of non-core sections;
   - relevant formulas, figures, and tables.
5. Figure/table comments must include visual/table assets in the context bundle.
6. Do not output generic advice only.
7. For substantive comments, provide concrete insert/rewrite text.
8. For experimental comments, do not invent results; provide experiment design and author-input checklist.
9. For reference comments, do not invent bibliographic details.
10. All outputs must be JSON-valid before report rendering.

## DOCX-First v3.2 Rules

1. The primary thesis source is DOCX.
2. Preserve Word document order across paragraphs, tables, images, captions, and formulas.
3. Build section trees from Word Heading styles first, then numbering regex fallback.
4. Extract figures and tables into `asset_catalog.json`.
5. Table assets must include Markdown and CSV files when possible.
6. Figure/table review comments must include matching assets in the context bundle; if not found, mark `needs_human_location_check`.
7. Every substantive revision must provide exact `anchor_text` plus concrete `new_text` or `revised_text`.
8. Generate a suggestion DOCX copy when possible; do not overwrite the original DOCX.

## Deep Revision v3.3 Rules

1. Shallow advice is a failed output. A plan must be a full Revision Card.
2. The expected deliverable is a near-final revision package. Do not stop at a few consultation paragraphs.
3. Every substantive plan must include `problem_diagnosis`, `evidence_coverage`, concrete `actions`, `synchronized_updates`, and `reviewer_response`.
4. Each text-level action must provide manuscript-ready replacement/addition text, not "建议补充/进一步完善" style instructions.
5. For major theory, model, experiment, conclusion, or contribution issues, split the solution into multiple actions across all affected sections.
6. If a new experiment is needed, provide protocol, variables, comparison groups, result table template, narrative placeholders, and exact author inputs. Do not invent numeric results.
7. The auditor must reject advice-only output and any plan that cannot materially improve the manuscript after direct integration.
8. A broad conceptual issue must consider multiple affected locations, such as method section plus conclusion/innovation/abstract.
9. Experiment issues must use existing manuscript evidence when available. If new results are required, provide experiment design and result-table templates, but do not invent results.
10. Reference issues must list fields to verify and replacement format, but do not invent publication details.
11. Figure/table issues must include matched assets, diagnosis, introduction/caption text, and redraw or formatting spec.
12. `revision-solution-auditor` must judge each plan before final report generation.
13. Failed plans must be retried with the auditor's `retry_instruction` up to 3 times.
14. Final reports must clearly distinguish proposed revisions, completed applied changes, and author-required materials.

## JSON Validation and Repair Rules

1. Planner output should be structured Markdown, not long-form JSON.
2. Convert planner Markdown with `scripts/parse_revision_plan_markdown.py`; parsed JSON is the internal contract for tools.
3. Agent output is not trusted until the parsed JSON passes strict JSON syntax validation and schema validation.
4. Always run `scripts/validate_agent_json.py --schema <schema> --input <parsed-json> --repair-prompt <prompt-path>`.
5. If validation fails on common formatting issues, run `scripts/repair_common_agent_json.py --input <parsed-json> --output <repaired-output> --schema <schema>` and validate the repaired file.
6. If local repair fails, send the generated repair prompt back to the same agent and ask it to repair the Markdown card only.
7. Repair mode may only fix headings, field types, missing required fields, or over-claiming language explicitly called out by the prompt.
8. Do not send invalid JSON to `revision-solution-auditor`.
9. Do not render final reports from unvalidated plans.

## Output Files

At minimum produce:

- `outputs/修改报告.md`
- `outputs/盲审回应表.md`
- `outputs/作者待补充事项.md`
- `outputs/05_修改建议版.docx`
- `outputs/06_整合修改稿.docx`

When possible also produce:

- `outputs/修改报告.html`
- `outputs/盲审回应表.docx`
- `outputs/标注版论文.pdf`
