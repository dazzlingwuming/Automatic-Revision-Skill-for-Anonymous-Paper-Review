# thesis-blind-review-revision

Provider-neutral agent pipeline for processing thesis blind-review comments and generating revision cards, reviewer response tables, revision reports, and a DOCX suggestion copy.

Claude Code support is an adapter: `.claude/skills/thesis-review-revision/SKILL.md` tells Claude Code how to use the pipeline, while portable agent specs live in `agent_specs/`.

## Installation

Install deterministic Python dependencies:

```bash
pip install -r requirements.txt
```

For Claude Code, copy `.claude/skills/thesis-review-revision` into a project root and sync portable agent specs into the Claude adapter:

```bash
python scripts/sync_agent_adapters.py
```

## Usage

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/example-run --title "论文标题" --mode full
```

Any host agent can act as the orchestrator. Python scripts handle deterministic work such as DOCX ingestion, asset extraction, validation, format checks, deterministic pre-audits, report rendering, and suggestion DOCX generation.

The v3.3 workflow adds a deep revision loop:

```text
context bundle -> deep-revision-planner -> revision-solution-auditor -> retry if needed
```

Shallow advice is treated as a failed output. Substantive comments must include diagnosis, evidence coverage, paste-ready text, synchronized updates, author-input boundaries, and a blind-review response.

## Inputs

- Thesis manuscript: DOCX is the primary high-quality source
- Blind-review comments: PDF, DOCX, TXT, or Markdown
- Optional thesis PDF: page/layout cross-checks and annotation only
- Optional university formatting rules

## Outputs

Minimum outputs:

- `outputs/修改报告.md`
- `outputs/盲审回应表.md`
- `outputs/作者待补充事项.md`
- `outputs/05_修改建议版.docx`

Optional outputs:

- `outputs/修改报告.html`
- `outputs/盲审回应表.docx`
- `outputs/标注版论文.pdf`
- `outputs/标注版论文.pdf`

## Academic Integrity

This tool does not fabricate experiments, data, references, figures, tables, statistics, page numbers, or completed revisions. If a review comment requires new evidence or author decisions, the workflow marks it as requiring author input.

## Deterministic Tools

Examples:

```bash
python scripts/run_pipeline.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/example-run --title "论文标题" --mode full
python scripts/ingest_docx.py --paper ./paper.docx --out workdir/example-run --title "论文标题"
python scripts/run_docx_first_prepare.py --paper-docx ./paper.docx --review ./review.pdf --out workdir/example-run --title "论文标题"
python scripts/render_revision_plan_notes.py --revision-plans-dir workdir/example-run/revision_plans --output-dir workdir/example-run/revision_plan_notes
python scripts/audit_revision_solutions.py --revision-plans-dir workdir/example-run/revision_plans --output workdir/example-run/audits/revision_solution_audit.json
python scripts/extract_txt.py --input tests/fixtures/sample_paper.txt --output workdir/test/extracted/paper_raw.txt
python scripts/chunk_paper.py --input tests/fixtures/sample_paper_raw.json --chunks-dir workdir/test/chunks --metadata-output workdir/test/artifacts/paper_chunks.json
python scripts/validate_json.py --schema .claude/skills/thesis-review-revision/schemas/review_comments.schema.json --input tests/fixtures/sample_review_comments.json
python scripts/patch_docx.py --input-docx ./paper.docx --revision-plans-dir workdir/example-run/revision_plans --output workdir/example-run/outputs/05_修改建议版.docx
```

## Architecture

- `agent_specs/`: provider-neutral agent definitions and workflow contract.
- `.claude/`: Claude Code adapter, including the Skill trigger and Claude-readable agent files.
- `scripts/run_pipeline.py`: universal deterministic entrypoint for `prepare`, `report`, and `full` modes.
- `scripts/parse_revision_plan_markdown.py`: converts planner Markdown cards into internal JSON.
- `scripts/render_revision_plan_notes.py`: converts internal JSON plans into human-readable Markdown cards.

The user-facing files are `outputs/`, `revision_plan_notes/`, and `audits/`. JSON directories are internal artifacts.

## Limitations

- PDF-only mode is degraded and no longer the high-quality main path.
- DOCX page numbers are not reliably available unless an aligned PDF is supplied.
- PDF annotation is page-level in the MVP and does not promise exact coordinates.
- DOCX patch output is a highlighted suggestion copy, not a tracked-changes rewrite.
