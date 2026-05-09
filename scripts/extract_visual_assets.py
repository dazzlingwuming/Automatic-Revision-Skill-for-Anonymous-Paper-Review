"""Extract visual/table/page assets from PDF and paper_blocks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.assets import extract_assets
from src.utils.jsonio import read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract visual and table assets.")
    parser.add_argument("--paper", required=True)
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--structure", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--catalog-output", required=True)
    args = parser.parse_args()
    catalog = extract_assets(Path(args.paper), read_json(args.blocks), read_json(args.structure), Path(args.out))
    write_json(args.catalog_output, catalog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
