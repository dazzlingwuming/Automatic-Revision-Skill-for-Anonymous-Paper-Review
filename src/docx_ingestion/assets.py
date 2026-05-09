"""Build DOCX-first asset catalogs."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from src.docx_ingestion.blocks import caption_for_figure, caption_for_table
from src.docx_ingestion.captions import asset_id_from_label
from src.docx_ingestion.tables import write_table_files


def build_asset_catalog(blocks_data: dict, structure: dict, assets_dir: Path) -> dict:
    assets_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = assets_dir / "figures"
    tables_dir = assets_dir / "tables"
    section_by_id = {section["section_id"]: section for section in structure.get("sections", [])}
    blocks = blocks_data["blocks"]
    assets: list[dict] = []
    doc = Document(blocks_data["source_file"]) if blocks_data.get("source_file") else None

    for index, block in enumerate(blocks):
        if block["type"] == "figure":
            caption_block, label = caption_for_figure(blocks, index)
            label = label or f"图auto{len(assets) + 1}"
            asset_id = asset_id_from_label(label, "fig")
            image_path = _write_first_image(doc, block.get("image_rids", []), asset_id, figures_dir)
            caption = caption_block["text"] if caption_block else ""
            section = section_by_id.get(block.get("section_id"))
            before = _nearby_text(blocks, index, -1)
            after = _nearby_text(blocks, index, 1)
            block["assets"].append(asset_id)
            assets.append(
                {
                    "asset_id": asset_id,
                    "asset_type": "figure",
                    "label": label,
                    "caption": caption,
                    "page": None,
                    "section_id": block.get("section_id"),
                    "section_title": section.get("title") if section else None,
                    "block_id": block["block_id"],
                    "bbox": None,
                    "image_path": str(image_path) if image_path else None,
                    "markdown_path": None,
                    "csv_path": None,
                    "json_path": None,
                    "nearby_text_before": before,
                    "nearby_text_after": after,
                    "extraction_method": "docx_relationship_image",
                    "quality": {
                        "has_caption": caption_block is not None,
                        "has_preceding_intro": bool(before),
                        "parse_confidence": 0.91 if image_path and caption_block else 0.62,
                        "needs_manual_check": image_path is None or caption_block is None,
                    },
                }
            )
            continue
        if block["type"] != "table":
            continue
        caption_block, label = caption_for_table(blocks, index)
        label = label or f"表auto{len(assets) + 1}"
        asset_id = asset_id_from_label(label, "tab")
        caption = caption_block["text"] if caption_block else ""
        paths = write_table_files(block.get("table", {}).get("rows", []), caption, asset_id, tables_dir)
        section = section_by_id.get(block.get("section_id"))
        before = _nearby_text(blocks, index, -1)
        after = _nearby_text(blocks, index, 1)
        block["assets"].append(asset_id)
        assets.append(
            {
                "asset_id": asset_id,
                "asset_type": "table",
                "label": label,
                "caption": caption,
                "page": None,
                "section_id": block.get("section_id"),
                "section_title": section.get("title") if section else None,
                "block_id": block["block_id"],
                "bbox": None,
                "image_path": None,
                "markdown_path": paths["markdown_path"],
                "csv_path": paths["csv_path"],
                "json_path": paths["json_path"],
                "nearby_text_before": before,
                "nearby_text_after": after,
                "extraction_method": "docx_table",
                "quality": {
                    "has_caption": caption_block is not None,
                    "has_preceding_intro": bool(before),
                    "parse_confidence": 0.94 if caption_block else 0.65,
                    "needs_manual_check": caption_block is None,
                },
            }
        )
    return {"assets": assets}


def _write_first_image(document, rids: list[str], asset_id: str, figures_dir: Path) -> Path | None:
    if document is None or not rids:
        return None
    figures_dir.mkdir(parents=True, exist_ok=True)
    part = document.part.related_parts.get(rids[0])
    if part is None:
        return None
    ext = Path(str(part.partname)).suffix or ".png"
    output = figures_dir / f"{asset_id}{ext}"
    output.write_bytes(part.blob)
    return output


def _nearby_text(blocks: list[dict], index: int, direction: int) -> str:
    cursor = index + direction
    while 0 <= cursor < len(blocks):
        block = blocks[cursor]
        if block["type"] in {"paragraph", "list_item", "table_caption", "figure_caption"} and block["text"].strip():
            return block["text"]
        cursor += direction
    return ""
