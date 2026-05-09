"""Add simple page-level notes to a PDF from revision plans."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _first_page(page_range: str | None) -> int | None:
    if not page_range:
        return None
    match = re.search(r"\d+", page_range)
    return int(match.group(0)) if match else None


def annotate_pdf(input_path: Path, revision_plans_dir: Path, output_path: Path) -> None:
    import fitz

    with fitz.open(input_path) as doc:
        for path in sorted(revision_plans_dir.glob("*.json")):
            plan = json.loads(path.read_text(encoding="utf-8"))
            for action in plan.get("specific_actions", []):
                page_no = _first_page(action.get("location", {}).get("page_range"))
                if page_no is None or page_no < 1 or page_no > len(doc):
                    continue
                page = doc[page_no - 1]
                note = f"{plan.get('comment_id')}: {action.get('type')} - {action.get('rationale', '')}"
                annot = page.add_text_annot(fitz.Point(36, 36 + 18 * (page_no % 10)), note)
                annot.update()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Annotate PDF with page-level revision notes.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--revision-plans-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    annotate_pdf(Path(args.input), Path(args.revision_plans_dir), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

