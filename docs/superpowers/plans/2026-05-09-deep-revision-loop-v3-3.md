# Deep Revision Loop v3.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the blind-review workflow from shallow suggestion scaffolds to a deep revision loop with planner/auditor retry semantics.

**Architecture:** Keep DOCX-first ingestion and deterministic artifacts, then make AI planning responsible for full `Revision Card`-level solutions. Add a dedicated solution auditor schema and deterministic pre-audit script so weak plans are rejected before report generation.

**Tech Stack:** Claude Code agents, JSON Schema 2020-12, Python deterministic audit scripts, pytest.

---

### Task 1: Define Deep Revision Contract

**Files:**
- Modify: `.claude/skills/thesis-review-revision/schemas/revision_plan.schema.json`
- Create: `.claude/skills/thesis-review-revision/schemas/revision_solution_audit.schema.json`
- Test: `tests/test_deep_revision_loop.py`

- [ ] Write tests for deep revision plan schema requirements.
- [ ] Run tests and observe schema validation failure.
- [ ] Add required fields for diagnosis, evidence coverage, synchronized updates, patch actions, and reviewer response.
- [ ] Run tests and verify pass.

### Task 2: Add Deep Planner and Solution Auditor Agents

**Files:**
- Create: `.claude/agents/deep-revision-planner.md`
- Create: `.claude/agents/revision-solution-auditor.md`
- Modify: `.claude/skills/thesis-review-revision/SKILL.md`
- Test: `tests/test_deep_revision_loop.py`

- [ ] Test agent files contain required rubric and retry terminology.
- [ ] Add agent prompts.
- [ ] Update Skill workflow to call planner, auditor, and retry.
- [ ] Run tests and verify pass.

### Task 3: Deterministic Solution Audit

**Files:**
- Create: `scripts/audit_revision_solutions.py`
- Test: `tests/test_deep_revision_loop.py`

- [ ] Test rejection of shallow single-paragraph plans.
- [ ] Implement deterministic gates for diagnosis, multi-location evidence, paste-ready text, sync updates, author-input boundaries, and reviewer response.
- [ ] Run tests and verify pass.

### Task 4: Report Integration Readiness

**Files:**
- Modify: `scripts/build_report.py`
- Test: existing report tests plus deep revision loop tests

- [ ] Ensure legacy plans still render.
- [ ] Render deep fields when present.
- [ ] Run full tests.
