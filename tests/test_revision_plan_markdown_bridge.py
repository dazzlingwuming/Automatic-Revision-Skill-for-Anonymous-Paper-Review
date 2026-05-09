from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from tests.test_deep_revision_loop import deep_plan


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def test_parse_revision_plan_markdown_to_schema_valid_json(tmp_path: Path) -> None:
    markdown = tmp_path / "R1-C001.md"
    output = tmp_path / "R1-C001.json"
    markdown.write_text(
        """# R1-C001

## 修改状态
text_ready_with_caveat

## 问题诊断
评审专家认为论文对算力与资本、劳动之间的替代和互补关系解释不足，导致CGE模型设定缺少经济学支撑。

## 论文证据与定位
### E1
- role: core_revision_location
- section_id: sec_4_2_1
- section_title: 面向算力规划的多区域CGE模型构建
- asset_id:
- evidence: 该节给出嵌套CES生产函数，但缺少要素关系解释。
- use: 在生产函数后补充经济学解释。

## 总体策略
在4.2.1节补充算力与资本、劳动、能源之间的替代和互补关系解释，并在结论中同步呼应。

## 具体修改
### A1
- type: insert_after_paragraph
- section_id: sec_4_2_1
- section_title: 面向算力规划的多区域CGE模型构建
- page_range:
- asset_id:
- anchor_text: 定位到生产函数说明之后。
- requires_author_input: false
- author_input_reason:

#### 原文
原文仅给出公式。

#### 新文
本文将算力服务视为数字经济条件下改变资本、劳动和能源配置效率的新型生产要素。算力一方面能够通过自动化计算和智能调度替代部分重复性劳动，另一方面又依赖服务器、网络设备和稳定能源供应，因此与资本和能源具有互补关系。

#### 修改理由
该修改直接回应评审专家关于替代关系解释不足的问题。

## 同步修改
### S1
- section_id: sec_5_1
- section_title: 总结
- asset_id:
- reason: 正文补充后结论需要同步。

#### 建议文本
本文进一步明确算力与传统要素之间的有限替代和互补关系，增强了CGE模型设定的经济学解释力。

## 给评审专家的回复
感谢专家意见。本文拟在CGE生产模块中补充算力与资本、劳动和能源之间有限替代与互补关系的经济学解释，并在结论中同步回应。

## 作者待补充
无

## 风险
- 需要作者核实替代弹性参数是否与模型实际设置一致。

## 置信度
0.86
""",
        encoding="utf-8",
    )

    result = run_script(
        "scripts/parse_revision_plan_markdown.py",
        "--input",
        str(markdown),
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(output.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / ".claude/skills/thesis-review-revision/schemas/revision_plan.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)
    assert data["comment_id"] == "R1-C001"
    assert data["actions"][0]["new_text"].startswith("本文将算力服务视为")


def test_render_revision_plan_notes_from_json(tmp_path: Path) -> None:
    plans = tmp_path / "plans"
    notes = tmp_path / "notes"
    plans.mkdir()
    (plans / "R1-C001.json").write_text(json.dumps(deep_plan(), ensure_ascii=False), encoding="utf-8")

    result = run_script("scripts/render_revision_plan_notes.py", "--revision-plans-dir", str(plans), "--output-dir", str(notes))

    assert result.returncode == 0, result.stderr + result.stdout
    note = (notes / "R1-C001.md").read_text(encoding="utf-8")
    assert "# R1-C001 修改方案卡" in note
    assert "## 问题诊断" in note
    assert "## 具体修改" in note
    assert "### A1" in note
    assert "## 给评审专家的回复" in note


def test_render_revision_plan_notes_accepts_legacy_string_sync_target(tmp_path: Path) -> None:
    plans = tmp_path / "plans"
    notes = tmp_path / "notes"
    plans.mkdir()
    plan = deep_plan()
    plan["synchronized_updates"][0]["target"] = "总结章节"
    (plans / "R1-C001.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    result = run_script("scripts/render_revision_plan_notes.py", "--revision-plans-dir", str(plans), "--output-dir", str(notes))

    assert result.returncode == 0, result.stderr + result.stdout
    note = (notes / "R1-C001.md").read_text(encoding="utf-8")
    assert "总结章节" in note


def test_render_revision_plan_notes_skips_invalid_json_and_continues(tmp_path: Path) -> None:
    plans = tmp_path / "plans"
    notes = tmp_path / "notes"
    plans.mkdir()
    (plans / "R1-C001.json").write_text(json.dumps(deep_plan(), ensure_ascii=False), encoding="utf-8")
    (plans / "bad.json").write_text('{"comment_id": "bad", "reviewer_response": "未转义"错误"}', encoding="utf-8")

    result = run_script("scripts/render_revision_plan_notes.py", "--revision-plans-dir", str(plans), "--output-dir", str(notes))

    assert result.returncode == 0, result.stderr + result.stdout
    assert (notes / "R1-C001.md").exists()
    assert "skipped 1 invalid JSON files" in result.stdout
    assert "bad.json" in result.stdout
