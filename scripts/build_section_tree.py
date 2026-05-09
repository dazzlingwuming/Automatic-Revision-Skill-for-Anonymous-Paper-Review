"""Build paper_structure.json, paper.md, and sections/*.md from paper_blocks.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.section_tree import build_section_tree
from src.utils.jsonio import read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a section tree from paper blocks.")
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--paper-dir", required=True)
    parser.add_argument("--blocks-output", required=True)
    parser.add_argument("--structure-output", required=True)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()
    blocks, structure = build_section_tree(read_json(args.blocks), Path(args.paper_dir), args.title)
    write_json(args.blocks_output, blocks)
    write_json(args.structure_output, structure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
