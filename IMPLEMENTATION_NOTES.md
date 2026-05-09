# Implementation Notes

## v3 Direction

This repository now targets the v3 Claude Code Skill architecture:

- Main Claude Code session is the orchestrator.
- `.claude/agents/*.md` define specialized subagents.
- Python scripts do deterministic file work only.
- Intermediate artifacts are stored in `workdir/<run_id>/`.
- JSON artifacts are validated against schemas under `.claude/skills/thesis-review-revision/schemas/`.

## Legacy Code

The existing `src/suggestor` package belongs to an older API-driven design. It is not part of the v3 MVP orchestration path because v3 requires AI reasoning to happen in Claude Code subagents rather than Python API clients.

## MVP Verification

Use:

```bash
pytest
```

Manual checks:

```bash
python scripts/validate_json.py --schema .claude/skills/thesis-review-revision/schemas/review_comments.schema.json --input tests/fixtures/sample_review_comments.json
python scripts/render_report.py --input tests/fixtures/sample_report.md --html-output workdir/test/outputs/修改报告.html
```

