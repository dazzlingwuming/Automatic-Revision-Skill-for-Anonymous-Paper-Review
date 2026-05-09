"""Render DOCX-first blocks to Markdown files."""

from __future__ import annotations

from pathlib import Path

from src.docx_ingestion.tables import rows_to_markdown


def heading_markdown(level: int, title: str) -> str:
    return f"{'#' * max(1, min(level, 6))} {title}"


def write_markdown(blocks_data: dict, structure: dict, paper_dir: Path) -> None:
    sections_dir = paper_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    section_by_id = {section["section_id"]: section for section in structure["sections"]}
    blocks_by_section: dict[str, list[dict]] = {section["section_id"]: [] for section in structure["sections"]}
    for block in blocks_data["blocks"]:
        if block.get("section_id") in blocks_by_section:
            blocks_by_section[block["section_id"]].append(block)

    paper_parts: list[str] = []
    for section in structure["sections"]:
        lines = [heading_markdown(section["level"], section["title"]), ""]
        for block in blocks_by_section.get(section["section_id"], []):
            if block["type"] == "heading":
                continue
            if block["type"] == "table":
                caption = _nearest_caption(blocks_data["blocks"], block["order"] - 1)
                lines.append(rows_to_markdown(block.get("table", {}).get("rows", []), caption).strip())
                lines.append("")
            elif block["type"] == "figure":
                asset = block.get("assets", [""])[0] if block.get("assets") else ""
                lines.extend([f"![{asset}](../assets/figures/{asset}.png)", ""])
            else:
                lines.extend([block["text"], ""])
        content = "\n".join(lines).strip() + "\n"
        (sections_dir / f"{section['section_id']}.md").write_text(content, encoding="utf-8")
        paper_parts.append(content)
    (paper_dir / "paper.md").write_text("\n".join(paper_parts), encoding="utf-8")


def _nearest_caption(blocks: list[dict], table_index: int) -> str:
    for offset in (1, 2, 3):
        index = table_index - offset
        if index >= 0 and blocks[index]["type"] == "table_caption":
            return blocks[index]["text"]
    return ""
