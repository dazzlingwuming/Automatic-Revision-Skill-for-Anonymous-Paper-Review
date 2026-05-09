from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def deep_plan() -> dict:
    return {
        "comment_id": "R1-C001",
        "revision_status": "text_ready_with_caveat",
        "problem_diagnosis": "评审意见指出算力与资本、劳动之间的替代/互补关系解释不足，说明现有CGE模型设定缺少经济学含义支撑。",
        "evidence_coverage": [
            {
                "role": "core_revision_location",
                "section_id": "sec_4_2_1",
                "section_title": "面向算力规划的多区域CGE模型构建",
                "evidence": "该节定义算力进入生产模块的位置。",
                "use": "补充生产要素关系解释。",
            },
            {
                "role": "sync_update_location",
                "section_id": "sec_5_1",
                "section_title": "总结",
                "evidence": "结论需要同步回应模型设定依据。",
                "use": "同步修改结论。",
            },
        ],
        "overall_strategy": "在CGE生产模块补充算力作为新型生产要素的替代/互补机制，并在结论中同步强化模型设定依据。",
        "actions": [
            {
                "action_id": "A1",
                "type": "insert_after_paragraph",
                "target": {"section_id": "sec_4_2_1", "section_title": "面向算力规划的多区域CGE模型构建", "page_range": None, "asset_id": None},
                "anchor_text": "定位到原文介绍生产函数或算力变量进入生产模块的段落之后。",
                "original_text": "原文仅说明算力进入模型，缺少替代/互补关系解释。",
                "new_text": "在本文的CGE生产模块中，算力服务并非被视为完全独立于传统生产要素之外的外生变量，而是作为数字化生产条件下能够改变资本、劳动和能源配置效率的新型投入要素纳入生产结构。具体而言，算力服务一方面可以通过提升数据处理、任务调度和资源配置效率，对部分重复性劳动和传统管理投入形成替代效应；另一方面，算力服务的使用依赖服务器、网络设备、数据中心基础设施以及稳定能源供给，因此又与资本投入和能源投入表现出较强的互补关系。基于这一特征，本文采用有限替代关系刻画算力服务与传统要素之间的相互作用，而非假定二者可以完全替代。",
                "rationale": "直接回应替代关系解释不足。",
                "requires_author_input": False,
            }
        ],
        "synchronized_updates": [
            {
                "target": {"section_id": "sec_5_1", "section_title": "总结"},
                "new_text": "同时，本文进一步明确了算力服务与资本、劳动和能源等传统要素之间的有限替代和互补关系，从而增强了宏观模型设定的经济学解释力。",
                "reason": "避免正文和结论不一致。",
            }
        ],
        "author_input_needed": [],
        "reviewer_response": "感谢专家意见。本文拟在CGE生产模块中补充算力服务与资本、劳动等传统要素之间有限替代和互补关系的经济学解释，并在结论部分同步强化模型设定依据。",
        "risks": [],
        "confidence": 0.86,
    }


def test_revision_plan_schema_accepts_deep_revision_card() -> None:
    schema = json.loads((ROOT / ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(deep_plan())


def test_revision_solution_audit_schema_accepts_rubric_output() -> None:
    schema = json.loads((ROOT / ".claude/skills/thesis-review-revision/schemas/revision_solution_audit.schema.json").read_text(encoding="utf-8"))
    audit = {
        "comment_id": "R1-C001",
        "passed": False,
        "overall_score": 62,
        "decision": "revise",
        "rubric": {
            "addresses_comment": {"score": 14, "max_score": 20, "issues": ["没有同步结论。"]},
            "uses_paper_evidence": {"score": 12, "max_score": 15, "issues": []},
            "actionability": {"score": 10, "max_score": 20, "issues": ["正文不够可直接粘贴。"]},
            "multi_location_coverage": {"score": 5, "max_score": 15, "issues": ["缺少同步修改位置。"]},
            "integrity": {"score": 15, "max_score": 15, "issues": []},
            "reviewer_response": {"score": 6, "max_score": 15, "issues": []},
        },
        "blockers": ["缺少同步修改位置。"],
        "required_fixes": ["补充结论同步修改。"],
        "retry_instruction": "请围绕缺少同步修改位置重写。",
    }
    Draft202012Validator(schema).validate(audit)


def test_deterministic_solution_auditor_rejects_shallow_plan(tmp_path: Path) -> None:
    plan = deep_plan()
    plan.pop("problem_diagnosis")
    plan["synchronized_updates"] = []
    plan["actions"][0]["new_text"] = "建议补充相关说明。"
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "R1-C001.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "audit.json"

    result = run_script("scripts/audit_revision_solutions.py", "--revision-plans-dir", str(plans), "--output", str(output))

    assert result.returncode == 1
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["passed"] is False
    assert data["audits"][0]["decision"] == "revise"
    assert data["audits"][0]["blockers"]


def test_deterministic_solution_auditor_rejects_scaffold_plan(tmp_path: Path) -> None:
    plan = deep_plan()
    plan["actions"][0]["anchor_text"] = "请根据目标章节中首次出现相关概念、图表或实验设置的位置人工确认插入点。"
    plan["actions"][0]["original_text"] = ""
    plan["reviewer_response"] = "感谢专家意见。本文拟针对该问题在相关章节中补充说明或调整，并对需要作者核实的内容进行逐项确认后再形成最终修改稿。"
    plan["risks"] = ["该文件为确定性 scaffold，需 revision-planner 或作者复核后作为最终修改文本。"]
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "R1-C001.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "audit.json"

    result = run_script("scripts/audit_revision_solutions.py", "--revision-plans-dir", str(plans), "--output", str(output))

    assert result.returncode == 1
    data = json.loads(output.read_text(encoding="utf-8"))
    audit = data["audits"][0]
    assert audit["decision"] == "revise"
    assert "确定性 scaffold 不能作为最终深度修改方案。" in audit["blockers"]


def test_deep_agents_and_skill_workflow_are_registered() -> None:
    planner = (ROOT / ".claude/agents/deep-revision-planner.md").read_text(encoding="utf-8")
    auditor = (ROOT / ".claude/agents/revision-solution-auditor.md").read_text(encoding="utf-8")
    skill = (ROOT / ".claude/skills/thesis-review-revision/SKILL.md").read_text(encoding="utf-8")

    assert "structured Markdown Revision Card" in planner
    assert "parse_revision_plan_markdown.py" in skill
    assert "revision_plan_notes" in skill
    assert "problem_diagnosis" in planner
    assert "synchronized_updates" in planner
    assert "overall_score" in auditor
    assert "retry_instruction" in auditor
    assert "deep-revision-planner" in skill
    assert "revision-solution-auditor" in skill


def test_build_report_renders_deep_revision_fields(tmp_path: Path) -> None:
    comments = {
        "comments": [
            {
                "comment_id": "R1-C001",
                "reviewer_id": "R1",
                "original_text": "算力与传统要素替代关系缺乏讨论。",
                "normalized_text": "需要补充算力与传统要素关系。",
                "category": "理论基础",
                "severity": "重点修改",
                "scope": "章节",
                "action_type": "补充解释",
                "requires_author_input": False,
                "confidence": 0.9,
            }
        ]
    }
    plans = tmp_path / "plans"
    out = tmp_path / "outputs"
    comments_path = tmp_path / "review_comments.json"
    plans.mkdir()
    comments_path.write_text(json.dumps(comments, ensure_ascii=False), encoding="utf-8")
    (plans / "R1-C001.json").write_text(json.dumps(deep_plan(), ensure_ascii=False), encoding="utf-8")

    result = run_script("scripts/build_report.py", "--review-comments", str(comments_path), "--revision-plans-dir", str(plans), "--output-dir", str(out))

    assert result.returncode == 0, result.stderr + result.stdout
    report = (out / "修改报告.md").read_text(encoding="utf-8")
    assert "#### 问题诊断" in report
    assert "#### 论文证据与定位" in report
    assert "#### 同步修改建议" in report
    assert "#### 风险与限制" in report
