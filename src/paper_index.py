"""Small utilities for paper index artifacts."""

from __future__ import annotations

from collections.abc import Iterable


def make_minimal_index(chunks: Iterable[dict], title: str | None = None) -> dict:
    chunk_items = []
    for chunk in chunks:
        heading = chunk.get("heading_guess")
        chunk_items.append(
            {
                "chunk_id": chunk["chunk_id"],
                "chapter": heading,
                "section": heading,
                "heading_path": [heading] if heading else [],
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "summary": "",
                "keywords": [],
                "text_ref": chunk["text_ref"],
            }
        )
    return {
        "metadata": {"title": title, "author": None, "degree_type": "unknown", "language": "unknown"},
        "outline": [],
        "chunks": chunk_items,
        "figures": [],
        "tables": [],
        "references": [],
    }

