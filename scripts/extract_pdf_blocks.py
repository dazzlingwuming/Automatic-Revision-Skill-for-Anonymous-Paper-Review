"""Extract paper_blocks.json from a PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.pdf_blocks import extract_pdf_blocks
from src.utils.jsonio import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract semantic blocks from PDF.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    write_json(args.output, extract_pdf_blocks(Path(args.input)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
