"""Build a section tree from paper blocks."""

from __future__ import annotations

from pathlib import Path

from src.utils.text import heading_level, section_id_from_title


def _page_range(blocks: list[dict]) -> tuple[int | None, int | None]:
    pages = [block["page"] for block in blocks if block.get("page")]
    return (min(pages), max(pages)) if pages else (None, None)


def _markdown_heading(level: int, title: str) -> str:
    return f"{'#' * max(1, min(level, 6))} {title}"


def build_section_tree(blocks_data: dict, paper_dir: Path, paper_title: str | None = None) -> tuple[dict, dict]:
    paper_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = paper_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    blocks = sorted(blocks_data["blocks"], key=lambda item: item["order"])
    sections: list[dict] = []
    stack: list[dict] = []
    current: dict | None = None
    section_blocks: dict[str, list[dict]] = {}

    def create_section(title: str, level: int, page: int | None) -> dict:
        section = {
            "section_id": section_id_from_title(title, len(sections) + 1),
            "level": level,
            "title": title,
            "page_start": page,
            "page_end": page,
            "parent": None,
            "children": [],
            "blocks": [],
            "figures": [],
            "tables": [],
            "formulas": [],
        }
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        if stack:
            section["parent"] = stack[-1]["section_id"]
            stack[-1]["children"].append(section["section_id"])
        stack.append(section)
        sections.append(section)
        section_blocks[section["section_id"]] = []
        return section

    for block in blocks:
        if block["type"] == "heading":
            current = create_section(block["text"], heading_level(block["text"]), block.get("page"))
        elif current is None:
            current = create_section("前置部分", 1, block.get("page"))

        block["section_id"] = current["section_id"]
        block["section_path"] = [section["title"] for section in stack]
        current["blocks"].append(block["block_id"])
        current["page_end"] = block.get("page") or current["page_end"]
        if block["type"] == "figure_caption":
            current["figures"].append(block["block_id"])
        elif block["type"] == "table_caption":
            current["tables"].append(block["block_id"])
        elif block["type"] == "formula":
            current["formulas"].append(block["block_id"])
        section_blocks[current["section_id"]].append(block)

    for section in sections:
        bks = section_blocks.get(section["section_id"], [])
        start, end = _page_range(bks)
        section["page_start"] = section["page_start"] or start
        section["page_end"] = section["page_end"] or end

    total_pages = max((block["page"] for block in blocks if block.get("page")), default=None)
    structure = {"paper_title": paper_title, "total_pages": total_pages, "sections": sections}

    paper_lines: list[str] = []
    for section in sections:
        lines = [_markdown_heading(section["level"], section["title"]), ""]
        for block in section_blocks.get(section["section_id"], []):
            if block["type"] == "heading":
                continue
            if block["type"] == "figure_caption":
                lines.extend([f"![{block['text']}](assets/{block['block_id']}.png)", "", block["text"], ""])
            elif block["type"] == "table_caption":
                lines.extend([block["text"], ""])
            elif block["type"] == "formula":
                lines.extend(["```text", block["text"], "```", ""])
            else:
                lines.extend([block["text"], ""])
        content = "\n".join(lines).strip() + "\n"
        (sections_dir / f"{section['section_id']}.md").write_text(content, encoding="utf-8")
        paper_lines.append(content)
    (paper_dir / "paper.md").write_text("\n".join(paper_lines), encoding="utf-8")
    return {"blocks": blocks}, structure

