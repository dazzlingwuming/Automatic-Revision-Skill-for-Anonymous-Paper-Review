from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_parse_review_comments_extracts_numbered_issues(tmp_path: Path) -> None:
    review_text = """
学位论文存在的不足及需要修改之处：
问题和建议
（1）虽引入CGE模型，但对算力与传统要素（资本、劳动力）的替代关系缺乏深入讨论，建议补充经济学解释。
（2）MILP模型涉及电价、碳成本、带宽成本和SLA风险，但未明确各项是否同量纲，例如是否归一化？
此外，论文在写作中还要注意：
1，图3.2，建议重新绘制，注意判断条件图元和相应线条的规范化。
2，参考文献13、14等多条文献的组织格式，需与同类型文献保持一致。
"""
    raw = tmp_path / "review_raw.txt"
    output = tmp_path / "review_comments.json"
    raw.write_text(review_text, encoding="utf-8")

    result = run_script("scripts/parse_review_comments.py", "--input", str(raw), "--output", str(output))
    assert result.returncode == 0, result.stderr + result.stdout

    data = json.loads(output.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / ".claude/skills/thesis-review-revision/schemas/review_comments.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)
    assert [comment["comment_id"] for comment in data["comments"]] == ["R1-C001", "R1-C002", "R1-C003", "R1-C004"]
    assert data["comments"][0]["category"] == "理论基础"
    assert data["comments"][2]["scope"] == "图表"
    assert data["comments"][3]["category"] == "参考文献"


def test_build_comment_mappings_matches_sections_and_assets(tmp_path: Path) -> None:
    comments = {
        "comments": [
            {
                "comment_id": "R1-C001",
                "reviewer_id": "R1",
                "original_text": "图3.2，建议重新绘制，注意判断条件图元和相应线条的规范化。",
                "normalized_text": "图3.2需要重绘并规范图元。",
                "category": "格式规范",
                "severity": "重点修改",
                "scope": "图表",
                "action_type": "格式修正",
                "requires_author_input": True,
                "confidence": 0.86,
            }
        ]
    }
    summaries = {
        "sections": [
            {
                "section_id": "sec_3_4",
                "title": "3.4 基于贝叶斯优化的混合MILP求解算法",
                "summary_short": "包含图3.2整体架构和求解流程。",
                "summary_detailed": "图3.2展示判断条件和流程线条。",
                "key_terms": ["MILP", "图"],
                "potential_review_topics": ["格式规范"],
            }
        ]
    }
    assets = {
        "assets": [
            {
                "asset_id": "fig_3_2",
                "asset_type": "figure",
                "label": "图3.2",
                "caption": "图3.2 整体架构",
                "section_id": "sec_3_4",
                "section_title": "3.4 基于贝叶斯优化的混合MILP求解算法",
                "nearby_text_before": "整体架构如图3.2所示。",
                "nearby_text_after": "该流程首先初始化。",
            }
        ]
    }
    comments_path = tmp_path / "review_comments.json"
    summaries_path = tmp_path / "section_summaries.json"
    assets_path = tmp_path / "asset_catalog.json"
    output = tmp_path / "comment_mappings.json"
    comments_path.write_text(json.dumps(comments, ensure_ascii=False), encoding="utf-8")
    summaries_path.write_text(json.dumps(summaries, ensure_ascii=False), encoding="utf-8")
    assets_path.write_text(json.dumps(assets, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "scripts/build_comment_mappings.py",
        "--review-comments",
        str(comments_path),
        "--section-summaries",
        str(summaries_path),
        "--asset-catalog",
        str(assets_path),
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(output.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / ".claude/skills/thesis-review-revision/schemas/comment_mappings.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)
    mapping = data["mappings"][0]
    assert mapping["mapping_type"] == "visual_table"
    assert mapping["assets"][0]["asset_id"] == "fig_3_2"
    assert mapping["locations"][0]["section_id"] == "sec_3_4"


def test_scaffold_revision_plans_outputs_schema_valid_plans(tmp_path: Path) -> None:
    comments = {
        "comments": [
            {
                "comment_id": "R1-C001",
                "reviewer_id": "R1",
                "original_text": "MILP模型涉及电价、碳成本、带宽成本和SLA风险，但未明确各项是否同量纲，例如是否归一化？",
                "normalized_text": "需要说明MILP成本项量纲和归一化处理。",
                "category": "方法设计",
                "severity": "重点修改",
                "scope": "章节",
                "action_type": "补充解释",
                "requires_author_input": False,
                "confidence": 0.88,
            }
        ]
    }
    mappings = {
        "mappings": [
            {
                "comment_id": "R1-C001",
                "mapping_type": "multi_section",
                "locations": [
                    {
                        "role": "core_revision_location",
                        "section_id": "sec_3_3",
                        "title": "构建CEOP-MILP模型",
                        "page_range": None,
                        "reason": "该节定义MILP目标函数和成本项。",
                        "include_mode": "full_text",
                        "confidence": 0.8,
                    }
                ],
                "assets": [],
                "requires_author_input": False,
                "confidence": 0.8,
            }
        ]
    }
    comments_path = tmp_path / "review_comments.json"
    mappings_path = tmp_path / "comment_mappings.json"
    output_dir = tmp_path / "plans"
    comments_path.write_text(json.dumps(comments, ensure_ascii=False), encoding="utf-8")
    mappings_path.write_text(json.dumps(mappings, ensure_ascii=False), encoding="utf-8")

    result = run_script(
        "scripts/scaffold_revision_plans.py",
        "--review-comments",
        str(comments_path),
        "--comment-mappings",
        str(mappings_path),
        "--output-dir",
        str(output_dir),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    plan = json.loads((output_dir / "R1-C001.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(plan)
    assert plan["revision_status"] == "text_ready_with_caveat"
    assert len(plan["actions"][0]["new_text"]) >= 150
