from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_validate_agent_json_reports_invalid_json_and_writes_repair_prompt(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    prompt = tmp_path / "repair_prompt.md"
    bad.write_text('{"reviewer_response": "您指出的"算力问题"需要修改"}', encoding="utf-8")

    result = run_script(
        "scripts/validate_agent_json.py",
        "--schema",
        ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json",
        "--input",
        str(bad),
        "--repair-prompt",
        str(prompt),
    )

    assert result.returncode == 1
    text = prompt.read_text(encoding="utf-8")
    assert "JSON syntax error" in text
    assert "只修复 JSON 语法或 schema 问题" in text
    assert str(bad) in text


def test_validate_agent_json_reports_schema_error_and_writes_repair_prompt(tmp_path: Path) -> None:
    invalid_schema = tmp_path / "plan.json"
    prompt = tmp_path / "repair_prompt.md"
    data = {
        "comment_id": "R1-C001",
        "revision_status": "text_ready",
        "overall_strategy": "补充说明。",
        "actions": [
            {
                "action_id": "A1",
                "type": "insert_after_paragraph",
                "target": {"section_id": "sec_1", "section_title": "第一章", "page_range": None},
                "anchor_text": "某段后",
                "original_text": "",
                "new_text": "这是一段足够长的正文建议，用于测试 schema 校验时 visual_diagnosis 字段类型错误是否会被捕获，并生成给 agent 的修复提示。",
                "rationale": "测试。",
                "requires_author_input": False,
                "visual_diagnosis": None,
            }
        ],
        "reviewer_response": "拟补充。",
        "author_input_needed": [],
        "risks": [],
        "confidence": 0.8,
    }
    invalid_schema.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "scripts/validate_agent_json.py",
        "--schema",
        ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json",
        "--input",
        str(invalid_schema),
        "--repair-prompt",
        str(prompt),
    )

    assert result.returncode == 1
    text = prompt.read_text(encoding="utf-8")
    assert "Schema validation error" in text
    assert "visual_diagnosis" in text


def test_validate_agent_json_passes_valid_deep_plan(tmp_path: Path) -> None:
    from tests.test_deep_revision_loop import deep_plan

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(deep_plan(), ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "scripts/validate_agent_json.py",
        "--schema",
        ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json",
        "--input",
        str(plan),
    )

    assert result.returncode == 0
    assert "valid" in result.stdout


def test_skill_requires_agent_json_validation_gate() -> None:
    skill = (ROOT / ".claude/skills/thesis-review-revision/SKILL.md").read_text(encoding="utf-8")
    planner = (ROOT / ".claude/agents/deep-revision-planner.md").read_text(encoding="utf-8")

    assert "scripts/validate_agent_json.py" in skill
    assert "scripts/repair_common_agent_json.py" in skill
    assert "Do not send invalid JSON to `revision-solution-auditor`" in skill
    assert "Markdown parse/schema repair prompt" in planner
