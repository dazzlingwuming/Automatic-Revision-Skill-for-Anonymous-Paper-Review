"""Extract semantic-ish blocks from PDF pages."""

from __future__ import annotations

from pathlib import Path

from src.utils.text import classify_block


def extract_pdf_blocks(input_path: Path) -> dict:
    import fitz

    blocks: list[dict] = []
    order = 0
    with fitz.open(input_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            raw_blocks = page.get_text("blocks")
            raw_blocks = sorted(raw_blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))
            for item in raw_blocks:
                text = " ".join(str(item[4]).split())
                if not text:
                    continue
                order += 1
                blocks.append(
                    {
                        "block_id": f"b_{order:06d}",
                        "type": classify_block(text),
                        "text": text,
                        "page": page_index,
                        "bbox": [float(item[0]), float(item[1]), float(item[2]), float(item[3])],
                        "section_id": None,
                        "section_path": [],
                        "order": order,
                    }
                )
    return {"blocks": blocks}

