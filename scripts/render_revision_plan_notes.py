"""Render revision plan JSON artifacts as human-readable Markdown notes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _target_text(target: dict | str | None) -> str:
    if isinstance(target, str):
        return target
    if target is None:
        return "未定位"
    section = target.get("section_title") or target.get("section_id") or "未定位"
    asset = target.get("asset_id")
    page = target.get("page_range")
    parts = [section]
    if page:
        parts.append(f"页码：{page}")
    if asset:
        parts.append(f"资产：{asset}")
    return "；".join(parts)


def render_plan_note(plan: dict) -> str:
    lines = [
        f"# {plan['comment_id']} 修改方案卡",
        "",
        "## 状态",
        "",
        plan.get("revision_status", ""),
        "",
        "## 问题诊断",
        "",
        plan.get("problem_diagnosis", ""),
        "",
        "## 论文证据与定位",
        "",
    ]
    if plan.get("evidence_coverage"):
        lines.extend(["| 角色 | 位置 | 证据 | 用途 |", "|---|---|---|---|"])
        for item in plan["evidence_coverage"]:
            where = item.get("section_title") or item.get("section_id") or item.get("asset_id") or "未定位"
            lines.append(f"| {item.get('role', '')} | {where} | {item.get('evidence', '')} | {item.get('use', '')} |")
    else:
        lines.append("无。")
    lines.extend(["", "## 总体策略", "", plan.get("overall_strategy", ""), "", "## 具体修改", ""])
    for action in plan.get("actions", []):
        lines.extend(
            [
                f"### {action.get('action_id', '')}",
                "",
                f"- 类型：{action.get('type', '')}",
                f"- 位置：{_target_text(action.get('target', {}))}",
                f"- 锚点：{action.get('anchor_text', '')}",
                f"- 需要作者补充：{'是' if action.get('requires_author_input') else '否'}",
                "",
                "#### 原文",
                "",
                action.get("original_text") or "无原文摘录。",
                "",
                "#### 新文/操作方案",
                "",
                action.get("new_text", ""),
                "",
                "#### 修改理由",
                "",
                action.get("rationale", ""),
                "",
            ]
        )
        if action.get("author_input_reason"):
            lines.extend(["#### 作者补充原因", "", action["author_input_reason"], ""])
    lines.extend(["## 同步修改", ""])
    if plan.get("synchronized_updates"):
        for index, update in enumerate(plan["synchronized_updates"], start=1):
            lines.extend(
                [
                    f"### S{index}",
                    "",
                    f"- 位置：{_target_text(update.get('target', {}))}",
                    f"- 原因：{update.get('reason', '')}",
                    "",
                    update.get("new_text", ""),
                    "",
                ]
            )
    else:
        lines.append("无。")
        lines.append("")
    lines.extend(["## 给评审专家的回复", "", plan.get("reviewer_response", ""), "", "## 作者待补充", ""])
    if plan.get("author_input_needed"):
        for item in plan["author_input_needed"]:
            lines.append(f"- {item.get('item', '')}：{item.get('needed_material', '')}")
    else:
        lines.append("无。")
    lines.extend(["", "## 风险", ""])
    if plan.get("risks"):
        lines.extend(f"- {risk}" for risk in plan["risks"])
    else:
        lines.append("无。")
    lines.extend(["", "## 置信度", "", str(plan.get("confidence", "")), ""])
    return "\n".join(lines)


def render_revision_plan_notes(revision_plans_dir: Path, output_dir: Path) -> tuple[list[Path], list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    skipped = []
    for path in sorted(revision_plans_dir.glob("*.json")):
        try:
            plan = _read_json(path)
        except json.JSONDecodeError:
            skipped.append(path)
            continue
        output = output_dir / f"{plan['comment_id']}.md"
        output.write_text(render_plan_note(plan), encoding="utf-8")
        written.append(output)
    return written, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Render revision plan JSON files as Markdown notes.")
    parser.add_argument("--revision-plans-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    written, skipped = render_revision_plan_notes(Path(args.revision_plans_dir), Path(args.output_dir))
    print(f"wrote {len(written)} notes")
    if skipped:
        print(f"skipped {len(skipped)} invalid JSON files")
        for path in skipped:
            print(f"- {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
