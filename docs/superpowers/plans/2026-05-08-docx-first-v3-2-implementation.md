# DOCX-First v3.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the PDF-first deterministic ingestion path with a DOCX-native path that preserves Word document order, extracts sections/assets, and can produce a highlighted suggestion DOCX.

**Architecture:** Add a focused `src/docx_ingestion/` package that reads DOCX body XML order, resolves styles and relationships, and produces the existing v3 artifact set. Keep PDF code as degraded legacy support while making DOCX the preferred `ingest_paper.py` path.

**Tech Stack:** Python 3.10+, `python-docx`, `lxml` through python-docx internals, standard `zipfile`, `csv`, `json`, pytest.

---

### Task 1: DOCX Body-Order Blocks

**Files:**
- Create: `src/docx_ingestion/__init__.py`
- Create: `src/docx_ingestion/iterator.py`
- Create: `src/docx_ingestion/blocks.py`
- Modify: `src/ingestion/docx_blocks.py`
- Test: `tests/test_docx_first_ingestion.py`

- [ ] **Step 1: Write failing tests**

Test that a DOCX with paragraph, table, paragraph preserves body order and includes style/docx locator fields.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_docx_blocks_preserve_body_order_and_locators -q`

- [ ] **Step 3: Implement body iterator and block extraction**

Use `document.element.body.iterchildren()` and emit `paragraph` or `table` blocks in body order.

- [ ] **Step 4: Run test and verify pass**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_docx_blocks_preserve_body_order_and_locators -q`

### Task 2: DOCX Sections and Markdown

**Files:**
- Create: `src/docx_ingestion/sections.py`
- Create: `src/docx_ingestion/markdown.py`
- Modify: `scripts/ingest_docx.py`
- Test: `tests/test_docx_first_ingestion.py`

- [ ] **Step 1: Write failing tests**

Test that Heading styles become nested sections and that `paper.md` plus `sections/*.md` are generated.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_ingest_docx_builds_sections_and_markdown -q`

- [ ] **Step 3: Implement section tree and markdown writer**

Build sections from Word heading styles first, then numbering regex fallback.

- [ ] **Step 4: Run test and verify pass**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_ingest_docx_builds_sections_and_markdown -q`

### Task 3: DOCX Assets

**Files:**
- Create: `src/docx_ingestion/captions.py`
- Create: `src/docx_ingestion/images.py`
- Create: `src/docx_ingestion/tables.py`
- Modify: `src/docx_ingestion/blocks.py`
- Test: `tests/test_docx_first_ingestion.py`

- [ ] **Step 1: Write failing tests**

Test that DOCX tables are exported as JSON/Markdown/CSV assets and that captions are matched.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_ingest_docx_extracts_table_assets -q`

- [ ] **Step 3: Implement asset catalog builders**

Attach table and image assets to nearby captions and include manual-check quality flags when matching is uncertain.

- [ ] **Step 4: Run test and verify pass**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_ingest_docx_extracts_table_assets -q`

### Task 4: Schema and Entrypoints

**Files:**
- Modify: `.claude/skills/thesis-review-revision/schemas/paper_blocks.schema.json`
- Modify: `.claude/skills/thesis-review-revision/schemas/asset_catalog.schema.json`
- Modify: `scripts/ingest_paper.py`
- Create: `scripts/ingest_docx.py`
- Create: `scripts/unpack_docx.py`
- Test: `tests/test_docx_first_ingestion.py`

- [ ] **Step 1: Write failing script test**

Test `scripts/ingest_docx.py` outputs v3.2 artifacts and schemas validate.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_ingest_docx_script_outputs_schema_valid_artifacts -q`

- [ ] **Step 3: Implement scripts and schema updates**

Make DOCX the high-quality path in `ingest_paper.py`; keep PDF as legacy fallback.

- [ ] **Step 4: Run test and verify pass**

Run: `python -m pytest tests/test_docx_first_ingestion.py::test_ingest_docx_script_outputs_schema_valid_artifacts -q`

### Task 5: Suggestion DOCX Patch MVP

**Files:**
- Create: `src/patching/__init__.py`
- Create: `src/patching/docx_writer.py`
- Modify: `scripts/patch_docx.py`
- Test: `tests/test_docx_patch_suggestions.py`

- [ ] **Step 1: Write failing tests**

Test that revision plan actions insert highlighted paragraphs into a DOCX copy.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/test_docx_patch_suggestions.py::test_patch_docx_inserts_highlighted_suggestions -q`

- [ ] **Step 3: Implement patch writer**

Find anchor text when possible, otherwise append to the matching section or document end with a manual-check marker.

- [ ] **Step 4: Run test and verify pass**

Run: `python -m pytest tests/test_docx_patch_suggestions.py::test_patch_docx_inserts_highlighted_suggestions -q`

### Task 6: Docs and Regression

**Files:**
- Modify: `.claude/skills/thesis-review-revision/SKILL.md`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Test: all tests

- [ ] **Step 1: Update docs**

Document DOCX-first inputs, generated artifacts, degraded PDF-only mode, and suggestion DOCX output.

- [ ] **Step 2: Run full tests**

Run: `python -m pytest tests -q --basetemp workdir\pytest-tmp`

- [ ] **Step 3: Fix regressions**

Fix any failures without weakening DOCX-first behavior.
