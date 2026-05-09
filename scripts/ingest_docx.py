"""Run the DOCX-first v3.2 ingestion pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.docx_ingestion.ingest import ingest_docx


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a DOCX paper into v3.2 artifacts.")
    parser.add_argument("--paper", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title")
    args = parser.parse_args()
    ingest_docx(Path(args.paper), Path(args.out), args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
