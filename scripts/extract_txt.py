"""Extract plain text or Markdown into a text or JSON artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def extract_txt(input_path: Path, output_path: Path) -> None:
    text = input_path.read_text(encoding="utf-8-sig")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        data = {
            "source_file": str(input_path),
            "file_type": "txt",
            "text": text,
            "warnings": [],
        }
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TXT/Markdown text.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    extract_txt(Path(args.input), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
