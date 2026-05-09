"""Unpack a DOCX file for inspection."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def unpack_docx(input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_path) as archive:
        archive.extractall(output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Unpack a DOCX package.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    unpack_docx(Path(args.input), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
