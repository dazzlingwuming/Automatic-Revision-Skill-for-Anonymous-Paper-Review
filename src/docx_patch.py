"""DOCX patch helper exports."""

from __future__ import annotations

from pathlib import Path


def save_docx_table(rows: list[list[str]], headers: list[str], output_path: str | Path) -> None:
    from docx import Document

    doc = Document()
    table = doc.add_table(rows=1, cols=len(headers))
    for cell, header in zip(table.rows[0].cells, headers):
        cell.text = header
    for row_data in rows:
        row = table.add_row().cells
        for cell, value in zip(row, row_data):
            cell.text = value
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)

