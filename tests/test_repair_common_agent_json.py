from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_repair_common_agent_json_fixes_unescaped_inner_quotes(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    fixed = tmp_path / "fixed.json"
    bad.write_text(
        '{\n'
        '  "comment_id": "R1-C001",\n'
        '  "reviewer_response": "感谢意见。您指出的"算力与传统要素替代关系缺乏深入讨论"问题确实切中要害。"\n'
        '}\n',
        encoding="utf-8",
    )

    result = run_script("scripts/repair_common_agent_json.py", "--input", str(bad), "--output", str(fixed))

    assert result.returncode == 0, result.stderr
    data = json.loads(fixed.read_text(encoding="utf-8"))
    assert data["reviewer_response"] == "感谢意见。您指出的”算力与传统要素替代关系缺乏深入讨论”问题确实切中要害。"


def test_repair_common_agent_json_replaces_known_null_arrays_and_validates(tmp_path: Path) -> None:
    from tests.test_deep_revision_loop import deep_plan

    bad = tmp_path / "bad.json"
    fixed = tmp_path / "fixed.json"
    data = deep_plan()
    data["actions"][0]["visual_diagnosis"] = None
    bad.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "scripts/repair_common_agent_json.py",
        "--input",
        str(bad),
        "--output",
        str(fixed),
        "--schema",
        ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json",
    )

    assert result.returncode == 0, result.stderr
    fixed_data = json.loads(fixed.read_text(encoding="utf-8"))
    assert fixed_data["actions"][0]["visual_diagnosis"] == []
