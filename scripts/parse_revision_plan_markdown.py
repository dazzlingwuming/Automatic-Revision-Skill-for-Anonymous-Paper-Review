"""Parse human-readable revision plan Markdown into schema-valid JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "yes", "1", "是", "需要"}


def _top_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current:
            sections[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def _plain(section: str) -> str:
    lines = [line.strip() for line in section.splitlines() if line.strip() and not line.startswith("### ")]
    return "\n".join(lines).strip()


def _kv_block(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^-\s*([^:：]+)[:：]\s*(.*)$", line.strip())
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def _subsections(section: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in section.splitlines():
        if line.startswith("### "):
            if current_title is not None:
                result.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[4:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        result.append((current_title, "\n".join(current_lines).strip()))
    return result


def _nested_text(block: str, heading: str) -> str:
    pattern = re.compile(rf"^####\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(block)
    if not match:
        return ""
    tail = block[match.end() :].strip("\n")
    next_heading = re.search(r"^####\s+", tail, re.MULTILINE)
    if next_heading:
        tail = tail[: next_heading.start()]
    return tail.strip()


def _parse_evidence(section: str) -> list[dict]:
    evidence = []
    for _, block in _subsections(section):
        values = _kv_block(block)
        evidence.append(
            {
                "role": values.get("role", "supporting_context"),
                "section_id": _empty_to_none(values.get("section_id")),
                "section_title": _empty_to_none(values.get("section_title")),
                "evidence": values.get("evidence", ""),
                "use": values.get("use", ""),
                "asset_id": _empty_to_none(values.get("asset_id")),
            }
        )
    return evidence


def _parse_actions(section: str) -> list[dict]:
    actions = []
    for title, block in _subsections(section):
        values = _kv_block(block)
        actions.append(
            {
                "action_id": title,
                "type": values.get("type", "insert_after_paragraph"),
                "target": {
                    "section_id": _empty_to_none(values.get("section_id")),
                    "section_title": _empty_to_none(values.get("section_title")),
                    "page_range": _empty_to_none(values.get("page_range")),
                    "asset_id": _empty_to_none(values.get("asset_id")),
                },
                "anchor_text": values.get("anchor_text", ""),
                "original_text": _nested_text(block, "原文"),
                "new_text": _nested_text(block, "新文"),
                "rationale": _nested_text(block, "修改理由"),
                "requires_author_input": _bool(values.get("requires_author_input")),
                "visual_diagnosis": [],
                "redraw_spec": None,
                "caption_suggestion": None,
                "author_input_reason": _empty_to_none(values.get("author_input_reason")),
            }
        )
    return actions


def _parse_sync_updates(section: str) -> list[dict]:
    updates = []
    for _, block in _subsections(section):
        values = _kv_block(block)
        updates.append(
            {
                "target": {
                    "section_id": _empty_to_none(values.get("section_id")),
                    "section_title": _empty_to_none(values.get("section_title")),
                    "asset_id": _empty_to_none(values.get("asset_id")),
                },
                "new_text": _nested_text(block, "建议文本"),
                "reason": values.get("reason", ""),
            }
        )
    return updates


def _parse_author_items(section: str) -> list[dict]:
    if not section.strip() or section.strip() == "无":
        return []
    items = []
    for line in section.splitlines():
        if line.strip().startswith("- "):
            text = line.strip()[2:]
            items.append({"item": text, "reason": "需要作者提供真实材料。", "needed_material": text})
    return items


def _parse_risks(section: str) -> list[str]:
    return [line.strip()[2:] for line in section.splitlines() if line.strip().startswith("- ")]


def parse_revision_plan_markdown(input_path: Path) -> dict:
    text = input_path.read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), input_path.stem)
    comment_id = title.split()[0]
    sections = _top_sections(text)
    confidence_text = _plain(sections.get("置信度", "0.5"))
    return {
        "comment_id": comment_id,
        "revision_status": _plain(sections.get("修改状态", "text_ready_with_caveat")) or "text_ready_with_caveat",
        "problem_diagnosis": _plain(sections.get("问题诊断", "")),
        "evidence_coverage": _parse_evidence(sections.get("论文证据与定位", "")),
        "overall_strategy": _plain(sections.get("总体策略", "")),
        "actions": _parse_actions(sections.get("具体修改", "")),
        "synchronized_updates": _parse_sync_updates(sections.get("同步修改", "")),
        "reviewer_response": _plain(sections.get("给评审专家的回复", "")),
        "author_input_needed": _parse_author_items(sections.get("作者待补充", "")),
        "risks": _parse_risks(sections.get("风险", "")),
        "confidence": float(confidence_text or 0.5),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse revision plan Markdown into JSON.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = parse_revision_plan_markdown(Path(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
