"""Compatibility wrapper for DOCX-first block extraction."""

from __future__ import annotations

from pathlib import Path

from src.docx_ingestion.blocks import extract_docx_blocks


__all__ = ["extract_docx_blocks"]
