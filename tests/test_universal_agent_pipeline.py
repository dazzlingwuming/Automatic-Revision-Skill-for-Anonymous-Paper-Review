from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PAPER = ROOT / "例子" / "盲审版本.docx"
EXAMPLE_REVIEW = ROOT / "例子" / "盲审评价.pdf"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_universal_agent_specs_exist_outside_claude_adapter() -> None:
    agents_dir = ROOT / "agent_specs" / "agents"
    claude_agents_dir = ROOT / ".claude" / "agents"
    workflow = ROOT / "agent_specs" / "workflow.md"

    assert workflow.exists()
    assert (agents_dir / "deep-revision-planner.md").exists()
    assert (agents_dir / "revision-solution-auditor.md").exists()

    planner = (agents_dir / "deep-revision-planner.md").read_text(encoding="utf-8")
    assert "structured Markdown Revision Card" in planner
    assert ".claude" not in planner
    assert {path.name for path in claude_agents_dir.glob("*.md")} <= {path.name for path in agents_dir.glob("*.md")}


def test_sync_agent_adapters_copies_universal_specs_to_claude(tmp_path: Path) -> None:
    source = tmp_path / "agent_specs" / "agents"
    target = tmp_path / ".claude" / "agents"
    source.mkdir(parents=True)
    (source / "demo-agent.md").write_text("---\nname: demo-agent\n---\n\nGeneric instructions.\n", encoding="utf-8")

    result = run_script(
        "scripts/sync_agent_adapters.py",
        "--source",
        str(source),
        "--claude-agents-dir",
        str(target),
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (target / "demo-agent.md").read_text(encoding="utf-8") == "---\nname: demo-agent\n---\n\nGeneric instructions.\n"


def test_run_pipeline_prepare_and_report_creates_user_facing_outputs(tmp_path: Path) -> None:
    if not EXAMPLE_PAPER.exists() or not EXAMPLE_REVIEW.exists():
        pytest.skip("private example thesis files are not included in public repository")

    out = tmp_path / "run"
    result = run_script(
        "scripts/run_pipeline.py",
        "--paper-docx",
        str(EXAMPLE_PAPER),
        "--review",
        str(EXAMPLE_REVIEW),
        "--out",
        str(out),
        "--title",
        "盲审版本",
        "--mode",
        "full",
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert len(list((out / "revision_plans").glob("*.json"))) == 13
    assert len(list((out / "revision_plan_notes").glob("*.md"))) == 13
    assert (out / "outputs" / "修改报告.md").exists()
    assert (out / "outputs" / "盲审回应表.md").exists()
    assert (out / "outputs" / "05_修改建议版.docx").exists()
    assert (out / "outputs" / "06_整合修改稿.docx").exists()
    audit = json.loads((out / "audits" / "revision_solution_audit.json").read_text(encoding="utf-8"))
    assert "audits" in audit
    assert audit["passed"] is False
