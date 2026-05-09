"""Compatibility wrapper to create paper.md from paper_blocks via section tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.section_tree import build_section_tree
from src.utils.jsonio import read_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize paper blocks to Markdown.")
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--paper-dir", required=True)
    args = parser.parse_args()
    build_section_tree(read_json(args.blocks), Path(args.paper_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
