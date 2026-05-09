"""v3.1 structured ingestion and quality tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_extract_txt_json_can_feed_section_tree(tmp_path: Path) -> None:
    raw = tmp_path / "paper_raw.json"
    result = run_script("scripts/extract_txt.py", "--input", "tests/fixtures/sample_paper.txt", "--output", str(raw))
    assert result.returncode == 0, result.stderr + result.stdout
    result = run_script("scripts/chunk_paper.py", "--input", str(raw), "--chunks-dir", str(tmp_path / "chunks"), "--metadata-output", str(tmp_path / "paper_chunks.json"))
    assert result.returncode == 0, result.stderr + result.stdout


def test_v31_pdf_blocks_and_section_tree(pdf_sample: str, tmp_path: Path) -> None:
    blocks = tmp_path / "paper" / "paper_blocks.json"
    structure = tmp_path / "paper" / "paper_structure.json"
    result = run_script("scripts/extract_pdf_blocks.py", "--input", pdf_sample, "--output", str(blocks))
    assert result.returncode == 0, result.stderr + result.stdout
    result = run_script(
        "scripts/build_section_tree.py",
        "--blocks",
        str(blocks),
        "--paper-dir",
        str(tmp_path / "paper"),
        "--blocks-output",
        str(blocks),
        "--structure-output",
        str(structure),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(structure.read_text(encoding="utf-8"))
    assert data["sections"]
    assert (tmp_path / "paper" / "paper.md").exists()


def test_v31_revision_schema_and_audit(tmp_path: Path) -> None:
    plans = tmp_path / "plans"
    plans.mkdir()
    good = {
        "comment_id": "R1-C001",
        "revision_status": "text_ready",
        "overall_strategy": "补充正文级理论解释。",
        "actions": [
            {
                "action_id": "A1",
                "type": "insert_after_paragraph",
                "target": {"section_id": "sec_4_2_1", "section_title": "4.2.1 测试", "page_range": "51-52"},
                "anchor_text": "定位到CES生产函数说明之后。",
                "original_text": "原文说明CES函数。",
                "new_text": "本文将算力服务作为新型生产要素纳入生产结构，用于刻画数字化条件下算力投入对资本、劳动和能源配置效率的影响。算力服务一方面能够提升数据处理、任务调度和资源配置效率，对部分重复性劳动和传统本地计算资本扩张形成替代效应；另一方面，其运行依赖服务器、网络设备和稳定能源供给，因而与资本和能源投入存在互补关系。本文采用CES嵌套结构描述这种有限替代关系，而不是假定算力服务可以完全替代传统要素。",
                "rationale": "回应替代关系解释不足。",
                "requires_author_input": False
            }
        ],
        "reviewer_response": "感谢专家意见。本文拟补充相关经济学解释。",
        "author_input_needed": [],
        "risks": [],
        "confidence": 0.86
    }
    path = plans / "R1-C001.json"
    path.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
    result = run_script("scripts/validate_json.py", "--schema", ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json", "--input", str(path))
    assert result.returncode == 0, result.stderr + result.stdout
    result = run_script("scripts/audit_revision_plans.py", "--revision-plans-dir", str(plans), "--output", str(tmp_path / "quality_audit.json"))
    assert result.returncode == 0, result.stderr + result.stdout


def test_quality_auditor_blocks_generic_advice(tmp_path: Path) -> None:
    plans = tmp_path / "bad_plans"
    plans.mkdir()
    bad = {
        "comment_id": "R1-C001",
        "revision_status": "text_ready",
        "overall_strategy": "补充说明。",
        "actions": [
            {
                "action_id": "A1",
                "type": "insert_after_paragraph",
                "target": {"section_id": "sec_1", "section_title": "第一章", "page_range": "1"},
                "anchor_text": "某段后",
                "original_text": "",
                "new_text": "建议补充相关说明",
                "rationale": "泛泛建议",
                "requires_author_input": False
            }
        ],
        "reviewer_response": "感谢专家意见。",
        "author_input_needed": [],
        "risks": [],
        "confidence": 0.5
    }
    (plans / "R1-C001.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    result = run_script("scripts/audit_revision_plans.py", "--revision-plans-dir", str(plans), "--output", str(tmp_path / "quality_audit.json"))
    assert result.returncode == 1
    audit = json.loads((tmp_path / "quality_audit.json").read_text(encoding="utf-8"))
    assert audit["passed"] is False

