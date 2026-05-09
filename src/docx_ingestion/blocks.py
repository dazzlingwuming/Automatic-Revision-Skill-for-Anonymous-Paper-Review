"""Build v3.2 paper blocks from a DOCX file."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from src.docx_ingestion.captions import figure_label, table_label
from src.docx_ingestion.iterator import iter_docx_blocks
from src.docx_ingestion.tables import table_rows
from src.utils.text import classify_block


def _paragraph_style(paragraph) -> tuple[str | None, str | None]:
    style = paragraph.style
    return (style.name if style else None, style.style_id if style else None)


def _paragraph_type(paragraph, text: str) -> str:
    style_name, _ = _paragraph_style(paragraph)
    if style_name and (style_name.startswith("Heading") or style_name.startswith("标题")):
        return "heading"
    return classify_block(text)


def _image_rids(paragraph) -> list[str]:
    rids = []
    for blip in paragraph._p.xpath(".//a:blip"):
        rid = blip.get(qn("r:embed"))
        if rid:
            rids.append(rid)
    return rids


def _block_base(order: int, block_type: str, text: str, body_index: int, xml_tag: str) -> dict:
    return {
        "block_id": f"b_{order:06d}",
        "type": block_type,
        "text": text,
        "page": None,
        "bbox": None,
        "section_id": None,
        "section_path": [],
        "order": order,
        "style_name": None,
        "style_id": None,
        "docx_locator": {
            "body_index": body_index,
            "xml_tag": xml_tag,
            "xpath_hint": f"/w:document/w:body/*[{body_index}]",
        },
        "assets": [],
    }


def extract_docx_blocks(input_path: Path) -> dict:
    document = Document(input_path)
    blocks: list[dict] = []
    order = 0

    for item in iter_docx_blocks(document):
        if item.xml_tag == "w:p":
            paragraph = item.element
            text = " ".join(paragraph.text.split())
            image_rids = _image_rids(paragraph)
            if not text and not image_rids:
                continue
            order += 1
            style_name, style_id = _paragraph_style(paragraph)
            block_type = "figure" if image_rids and not text else _paragraph_type(paragraph, text)
            block = _block_base(order, block_type, text, item.body_index, item.xml_tag)
            block["style_name"] = style_name
            block["style_id"] = style_id
            if image_rids:
                block["image_rids"] = image_rids
            blocks.append(block)
        elif item.xml_tag == "w:tbl":
            rows = table_rows(item.element)
            text = "\n".join(" | ".join(row) for row in rows).strip()
            if not text:
                continue
            order += 1
            block = _block_base(order, "table", text, item.body_index, item.xml_tag)
            block["table"] = {"rows": rows}
            blocks.append(block)

    return {"source_file": str(input_path), "file_type": "docx", "blocks": blocks}


def caption_for_table(blocks: list[dict], table_index: int, window: int = 3) -> tuple[dict | None, str | None]:
    for offset in range(1, window + 1):
        before = table_index - offset
        if before >= 0 and blocks[before]["type"] == "table_caption":
            return blocks[before], table_label(blocks[before]["text"])
    for offset in range(1, window + 1):
        after = table_index + offset
        if after < len(blocks) and blocks[after]["type"] == "table_caption":
            return blocks[after], table_label(blocks[after]["text"])
    return None, None


def caption_for_figure(blocks: list[dict], figure_index: int, window: int = 3) -> tuple[dict | None, str | None]:
    for offset in range(1, window + 1):
        after = figure_index + offset
        if after < len(blocks) and blocks[after]["type"] == "figure_caption":
            return blocks[after], figure_label(blocks[after]["text"])
    for offset in range(1, window + 1):
        before = figure_index - offset
        if before >= 0 and blocks[before]["type"] == "figure_caption":
            return blocks[before], figure_label(blocks[before]["text"])
    return None, None
