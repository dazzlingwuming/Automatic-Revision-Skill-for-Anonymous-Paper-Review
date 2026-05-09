"""Visual/table asset catalog extraction."""

from __future__ import annotations

import re
from pathlib import Path


FIG_LABEL_RE = re.compile(r"(图\s*\d+(?:[.-]\d+)?|Fig\.?\s*\d+(?:\.\d+)?)", re.IGNORECASE)
TAB_LABEL_RE = re.compile(r"(表\s*\d+(?:[.-]\d+)?|Table\s*\d+(?:\.\d+)?)", re.IGNORECASE)


def _asset_id(label: str, prefix: str) -> str:
    nums = re.findall(r"\d+", label)
    suffix = "_".join(nums) if nums else label
    return f"{prefix}_{suffix}"


def _nearby(blocks: list[dict], index: int, direction: int) -> str:
    cursor = index + direction
    while 0 <= cursor < len(blocks):
        block = blocks[cursor]
        if block["type"] in {"paragraph", "list_item"} and block["text"].strip():
            return block["text"]
        cursor += direction
    return ""


def _clip_for_caption(page, bbox: list[float], asset_type: str):
    import fitz

    page_rect = page.rect
    x0, y0, x1, y1 = bbox
    if asset_type == "figure":
        clip = fitz.Rect(max(0, x0 - 20), max(0, y0 - 360), min(page_rect.x1, x1 + 20), min(page_rect.y1, y1 + 30))
    else:
        clip = fitz.Rect(max(0, x0 - 20), max(0, y0 - 280), min(page_rect.x1, x1 + 20), min(page_rect.y1, y1 + 40))
    if clip.height < 80:
        clip = page_rect
    return clip


def extract_assets(pdf_path: Path, blocks_data: dict, structure: dict, assets_dir: Path) -> dict:
    import fitz

    assets_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = assets_dir / "pages"
    figures_dir = assets_dir / "figures"
    tables_dir = assets_dir / "tables"
    for directory in [pages_dir, figures_dir, tables_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    blocks = blocks_data["blocks"]
    section_by_id = {section["section_id"]: section for section in structure.get("sections", [])}
    assets: list[dict] = []

    with fitz.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            page_path = pages_dir / f"page_{page_number:03d}.png"
            page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(page_path)

        for index, block in enumerate(blocks):
            if block["type"] not in {"figure_caption", "table_caption"}:
                continue
            label_match = (FIG_LABEL_RE if block["type"] == "figure_caption" else TAB_LABEL_RE).search(block["text"])
            label = label_match.group(1).replace(" ", "") if label_match else block["text"][:20]
            asset_type = "figure" if block["type"] == "figure_caption" else "table"
            asset_id = _asset_id(label, "fig" if asset_type == "figure" else "tab")
            page_number = block.get("page")
            image_path = None
            if page_number and block.get("bbox"):
                page = doc[page_number - 1]
                clip = _clip_for_caption(page, block["bbox"], asset_type)
                image_dir = figures_dir if asset_type == "figure" else tables_dir
                image_path = image_dir / f"{asset_id}.png"
                page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip).save(image_path)
            section = section_by_id.get(block.get("section_id"))
            before = _nearby(blocks, index, -1)
            after = _nearby(blocks, index, 1)
            assets.append(
                {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "label": label,
                    "caption": block["text"],
                    "page": page_number,
                    "section_id": block.get("section_id"),
                    "section_title": section.get("title") if section else None,
                    "bbox": block.get("bbox"),
                    "image_path": str(image_path) if image_path else str(pages_dir / f"page_{page_number:03d}.png") if page_number else None,
                    "markdown_path": None,
                    "csv_path": None,
                    "nearby_text_before": before,
                    "nearby_text_after": after,
                    "extraction_method": "caption_region_crop" if image_path else "page_image_fallback",
                    "quality": {
                        "has_caption": True,
                        "has_preceding_intro": label in before,
                        "parse_confidence": 0.78 if image_path else 0.55,
                        "needs_manual_check": image_path is None,
                    },
                }
            )
    return {"assets": assets}

