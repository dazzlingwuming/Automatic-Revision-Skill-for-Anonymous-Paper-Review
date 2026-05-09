"""Build DOCX-first section trees."""

from __future__ import annotations

import re
from pathlib import Path

from src.utils.text import heading_level


CHAPTER_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def heading_level_from_block(block: dict) -> int:
    style_name = block.get("style_name") or ""
    match = re.search(r"(\d+)$", style_name)
    if style_name.startswith(("Heading", "标题")) and match:
        return int(match.group(1))
    return heading_level(block["text"])


def section_id_from_heading(title: str, fallback: int) -> str:
    clean = " ".join(title.split())
    chapter = re.match(r"^第([一二三四五六七八九十])章", clean)
    if chapter:
        return f"sec_{CHAPTER_NUM.get(chapter.group(1), fallback)}"
    numbered = re.match(r"^(\d+(?:\.\d+){0,5})", clean)
    if numbered:
        return "sec_" + numbered.group(1).replace(".", "_")
    if "参考文献" in clean:
        return "sec_references"
    if "摘要" == clean or clean.endswith("摘要"):
        return "sec_abstract"
    if "结论" in clean:
        return "sec_conclusion"
    return f"sec_{fallback:04d}"


def build_docx_section_tree(blocks_data: dict, paper_dir: Path, paper_title: str | None = None) -> tuple[dict, dict]:
    paper_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = paper_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    blocks = blocks_data["blocks"]
    sections: list[dict] = []
    stack: list[dict] = []
    current: dict | None = None
    section_blocks: dict[str, list[dict]] = {}
    heading_counters: list[int] = [0, 0, 0, 0, 0, 0]

    def create_section(title: str, level: int, auto_number: bool = False) -> dict:
        normalized_level = max(1, min(level, 6))
        section_id = section_id_from_heading(title, len(sections) + 1)
        if auto_number and section_id.startswith("sec_0"):
            heading_counters[normalized_level - 1] += 1
            for index in range(normalized_level, len(heading_counters)):
                heading_counters[index] = 0
            parts = heading_counters[:normalized_level]
            if all(part > 0 for part in parts):
                section_id = "sec_" + "_".join(str(part) for part in parts)
        section = {
            "section_id": section_id,
            "level": normalized_level,
            "title": title,
            "page_start": None,
            "page_end": None,
            "parent": None,
            "children": [],
            "blocks": [],
            "figures": [],
            "tables": [],
            "formulas": [],
        }
        while stack and stack[-1]["level"] >= section["level"]:
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
            current = create_section(block["text"], heading_level_from_block(block), auto_number=True)
        elif current is None:
            current = create_section("前置部分", 1)
        block["section_id"] = current["section_id"]
        block["section_path"] = [section["title"] for section in stack]
        current["blocks"].append(block["block_id"])
        if block["type"] == "table":
            current["tables"].append(block["block_id"])
        elif block["type"] == "figure":
            current["figures"].append(block["block_id"])
        elif block["type"] == "formula":
            current["formulas"].append(block["block_id"])
        section_blocks[current["section_id"]].append(block)

    structure = {"paper_title": paper_title, "total_pages": None, "sections": sections}
    return blocks_data, structure
