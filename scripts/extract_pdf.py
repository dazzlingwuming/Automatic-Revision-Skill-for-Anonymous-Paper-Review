"""Extract text and page data from a PDF file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def extract_pdf(input_path: Path, output_path: Path) -> dict:
    import fitz

    warnings: list[str] = []
    pages: list[dict] = []
    with fitz.open(input_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if not text.strip():
                warnings.append(f"Page {page_index} has no extractable text; it may be scanned.")
            pages.append(
                {
                    "page_number": page_index,
                    "text": text,
                    "blocks": [],
                }
            )

    data = {
        "source_file": str(input_path),
        "file_type": "pdf",
        "pages": pages,
        "warnings": warnings,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from PDF.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    extract_pdf(Path(args.input), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

