"""Create simple Markdown/CSV placeholders for table assets in asset_catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.jsonio import read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Create MVP table Markdown/CSV files for table assets.")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--catalog-output", required=True)
    args = parser.parse_args()
    catalog = read_json(args.catalog)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for asset in catalog.get("assets", []):
        if asset["asset_type"] != "table":
            continue
        md_path = out / f"{asset['asset_id']}.md"
        csv_path = out / f"{asset['asset_id']}.csv"
        md_path.write_text(f"| 表题 |\n|---|\n| {asset['caption']} |\n", encoding="utf-8")
        csv_path.write_text(f"caption\n\"{asset['caption']}\"\n", encoding="utf-8")
        asset["markdown_path"] = str(md_path)
        asset["csv_path"] = str(csv_path)
    write_json(args.catalog_output, catalog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
