"""Run the DOCX-first ingestion pipeline."""

from __future__ import annotations

from pathlib import Path

from src.docx_ingestion.assets import build_asset_catalog
from src.docx_ingestion.blocks import extract_docx_blocks
from src.docx_ingestion.markdown import write_markdown
from src.docx_ingestion.sections import build_docx_section_tree
from src.utils.jsonio import write_json


def ingest_docx(paper: Path, out: Path, title: str | None = None) -> None:
    paper_dir = out / "paper"
    assets_dir = out / "assets"
    paper_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    blocks = extract_docx_blocks(paper)
    blocks, structure = build_docx_section_tree(blocks, paper_dir, title)
    catalog = build_asset_catalog(blocks, structure, assets_dir)
    write_markdown(blocks, structure, paper_dir)

    write_json(paper_dir / "paper_blocks.json", blocks)
    write_json(paper_dir / "paper_structure.json", structure)
    write_json(assets_dir / "asset_catalog.json", catalog)
