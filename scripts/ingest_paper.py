"""Run the v3.1 MVP paper ingestion pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.pdf_blocks import extract_pdf_blocks
from src.ingestion.section_tree import build_section_tree
from src.ingestion.assets import extract_assets
from src.docx_ingestion.ingest import ingest_docx
from src.utils.jsonio import write_json


def ingest_paper(paper: Path, out: Path, title: str | None = None) -> None:
    if paper.suffix.lower() == ".docx":
        ingest_docx(paper, out, title)
        return

    paper_dir = out / "paper"
    assets_dir = out / "assets"
    artifacts_dir = out / "artifacts"
    paper_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if paper.suffix.lower() == ".pdf":
        blocks = extract_pdf_blocks(paper)
    else:
        raise ValueError(f"Unsupported paper type: {paper.suffix}")

    blocks, structure = build_section_tree(blocks, paper_dir, title)
    write_json(paper_dir / "paper_blocks.json", blocks)
    write_json(paper_dir / "paper_structure.json", structure)
    if paper.suffix.lower() == ".pdf":
        catalog = extract_assets(paper, blocks, structure, assets_dir)
        write_json(assets_dir / "asset_catalog.json", catalog)
    else:
        write_json(assets_dir / "asset_catalog.json", {"assets": []})


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest paper into v3.1 structured artifacts.")
    parser.add_argument("--paper", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title")
    args = parser.parse_args()
    ingest_paper(Path(args.paper), Path(args.out), args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
