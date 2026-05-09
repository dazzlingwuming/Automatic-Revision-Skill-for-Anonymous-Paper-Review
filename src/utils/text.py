"""Text classification helpers for structured paper ingestion."""

from __future__ import annotations

import re


CHAPTER_RE = re.compile(r"^(第[一二三四五六七八九十百]+章)\s+(.+)$")
NUM_HEADING_RE = re.compile(r"^(\d+(?:\.\d+){0,4})\s+(.{1,80})$")
FIGURE_RE = re.compile(r"^(图\s*\d+(?:[.-]\d+)?|Fig\.?\s*\d+(?:\.\d+)?)\s*(.*)", re.IGNORECASE)
TABLE_RE = re.compile(r"^(表\s*\d+(?:[.-]\d+)?|Table\s*\d+(?:\.\d+)?)\s*(.*)", re.IGNORECASE)
FORMULA_RE = re.compile(r"[（(]\d+(?:\.\d+)?[）)]$")
REFERENCE_RE = re.compile(r"^\[\d+\]\s*.+")


def classify_block(text: str) -> str:
    clean = " ".join(text.strip().split())
    if not clean:
        return "unknown"
    if FIGURE_RE.match(clean):
        return "figure_caption"
    if TABLE_RE.match(clean):
        return "table_caption"
    if REFERENCE_RE.match(clean):
        return "reference_item"
    if CHAPTER_RE.match(clean) or NUM_HEADING_RE.match(clean):
        if len(clean) <= 90:
            return "heading"
    if FORMULA_RE.search(clean) and len(clean) <= 160:
        return "formula"
    if clean[:2] in {"（1", "（2", "（3", "（4", "(1", "(2", "(3", "(4"}:
        return "list_item"
    return "paragraph"


def heading_level(text: str) -> int:
    clean = " ".join(text.strip().split())
    if CHAPTER_RE.match(clean):
        return 1
    match = NUM_HEADING_RE.match(clean)
    if match:
        return match.group(1).count(".") + 1
    return 9


def section_id_from_title(title: str, index: int) -> str:
    match = NUM_HEADING_RE.match(" ".join(title.strip().split()))
    if match:
        return "sec_" + match.group(1).replace(".", "_")
    chap = CHAPTER_RE.match(" ".join(title.strip().split()))
    if chap:
        return f"sec_ch_{index:03d}"
    return f"sec_{index:04d}"

