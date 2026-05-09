"""Chunk extracted paper text into files plus metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADING_RE = re.compile(r"^\s*((第[一二三四五六七八九十百]+章|[0-9]+(?:\.[0-9]+)*)(\s+|[、.．]).{0,80})$")


def _load_text(raw: dict) -> list[dict]:
    if raw.get("file_type") == "pdf":
        return [
            {"text": page.get("text", ""), "page_start": page.get("page_number"), "page_end": page.get("page_number")}
            for page in raw.get("pages", [])
        ]
    if raw.get("file_type") == "docx":
        return [
            {"text": para.get("text", ""), "page_start": None, "page_end": None, "style": para.get("style")}
            for para in raw.get("paragraphs", [])
        ]
    return [{"text": raw.get("text", ""), "page_start": None, "page_end": None}]


def _heading_guess(text: str, current: str | None) -> str | None:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if HEADING_RE.match(first_line):
        return first_line
    return current


def chunk_paper(input_path: Path, chunks_dir: Path, metadata_output: Path, target_chars: int = 1200) -> dict:
    raw_text = input_path.read_text(encoding="utf-8")
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError:
        raw = {"source_file": str(input_path), "file_type": "txt", "text": raw_text}
    units = _load_text(raw)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    chunks: list[dict] = []
    buffer: list[str] = []
    page_start = None
    page_end = None
    heading = None

    def flush() -> None:
        nonlocal buffer, page_start, page_end, heading
        text = "\n".join(part for part in buffer if part.strip()).strip()
        if not text:
            buffer = []
            return
        chunk_id = f"ch_{len(chunks) + 1:04d}"
        text_ref = chunks_dir / f"{chunk_id}.txt"
        text_ref.write_text(text, encoding="utf-8")
        chunks.append(
            {
                "chunk_id": chunk_id,
                "page_start": page_start,
                "page_end": page_end,
                "heading_guess": heading,
                "text_ref": str(text_ref),
                "char_count": len(text),
            }
        )
        buffer = []
        page_start = None
        page_end = None

    for unit in units:
        text = unit.get("text", "").strip()
        if not text:
            continue
        next_heading = _heading_guess(text, heading)
        is_new_heading = next_heading != heading and buffer
        if is_new_heading:
            flush()
        heading = next_heading
        if page_start is None:
            page_start = unit.get("page_start")
        page_end = unit.get("page_end") or page_end
        buffer.append(text)
        if sum(len(part) for part in buffer) >= target_chars:
            flush()
    flush()

    data = {"source_file": raw.get("source_file"), "chunks": chunks}
    metadata_output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Chunk extracted paper JSON.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--chunks-dir", required=True)
    parser.add_argument("--metadata-output", required=True)
    parser.add_argument("--target-chars", type=int, default=1200)
    args = parser.parse_args()
    chunk_paper(Path(args.input), Path(args.chunks_dir), Path(args.metadata_output), args.target_chars)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
