"""DOCX table export helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def table_rows(table) -> list[list[str]]:
    return [[" ".join(cell.text.split()) for cell in row.cells] for row in table.rows]


def rows_to_markdown(rows: list[list[str]], caption: str = "") -> str:
    if not rows:
        return caption
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    lines = []
    if caption:
        lines.extend([caption, ""])
    lines.append("| " + " | ".join(normalized[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
    for row in normalized[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def write_table_files(rows: list[list[str]], caption: str, asset_id: str, tables_dir: Path) -> dict[str, str]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    json_path = tables_dir / f"{asset_id}.json"
    markdown_path = tables_dir / f"{asset_id}.md"
    csv_path = tables_dir / f"{asset_id}.csv"
    json_path.write_text(json.dumps({"caption": caption, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(rows_to_markdown(rows, caption), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    return {"json_path": str(json_path), "markdown_path": str(markdown_path), "csv_path": str(csv_path)}
