"""Caption parsing for DOCX figures and tables."""

from __future__ import annotations

import re


FIGURE_RE = re.compile(r"^(图\s*\d+(?:[.-]\d+)?|Figure\s+\d+(?:\.\d+)?|Fig\.?\s*\d+(?:\.\d+)?)\s*(.*)", re.IGNORECASE)
TABLE_RE = re.compile(r"^(表\s*\d+(?:[.-]\d+)?|Table\s+\d+(?:\.\d+)?)\s*(.*)", re.IGNORECASE)


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", "", label.strip())


def asset_id_from_label(label: str, prefix: str) -> str:
    nums = re.findall(r"\d+", label)
    suffix = "_".join(nums) if nums else re.sub(r"\W+", "_", label).strip("_").lower()
    return f"{prefix}_{suffix or 'auto'}"


def figure_label(text: str) -> str | None:
    match = FIGURE_RE.match(" ".join(text.split()))
    return normalize_label(match.group(1)) if match else None


def table_label(text: str) -> str | None:
    match = TABLE_RE.match(" ".join(text.split()))
    return normalize_label(match.group(1)) if match else None
