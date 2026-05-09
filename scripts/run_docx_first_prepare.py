"""Run deterministic DOCX-first preparation for a blind-review revision package."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(*args: str) -> None:
    result = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare DOCX-first artifacts, mappings, and revision scaffolds.")
    parser.add_argument("--paper-docx", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="")
    args = parser.parse_args()

    out = Path(args.out)
    review_path = Path(args.review)
    review_dir = out / "review"
    artifacts_dir = out / "artifacts"
    plans_dir = out / "revision_plans"
    review_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    plans_dir.mkdir(parents=True, exist_ok=True)

    run_step("scripts/ingest_docx.py", "--paper", args.paper_docx, "--out", str(out), "--title", args.title)
    run_step(
        "scripts/build_section_summaries.py",
        "--structure",
        str(out / "paper" / "paper_structure.json"),
        "--sections-dir",
        str(out / "paper" / "sections"),
        "--output",
        str(out / "paper" / "section_summaries.json"),
        "--brief-output",
        str(out / "paper" / "paper_brief.md"),
        "--asset-catalog",
        str(out / "assets" / "asset_catalog.json"),
    )

    review_raw = review_dir / ("review_raw.json" if review_path.suffix.lower() == ".pdf" else "review_raw.txt")
    if review_path.suffix.lower() == ".pdf":
        run_step("scripts/extract_pdf.py", "--input", args.review, "--output", str(review_raw))
    elif review_path.suffix.lower() in {".txt", ".md"}:
        run_step("scripts/extract_txt.py", "--input", args.review, "--output", str(review_raw))
    elif review_path.suffix.lower() == ".docx":
        run_step("scripts/extract_docx.py", "--input", args.review, "--output", str(review_raw.with_suffix(".json")))
        review_raw = review_raw.with_suffix(".json")
    else:
        raise ValueError(f"Unsupported review type: {review_path.suffix}")

    review_comments = artifacts_dir / "review_comments.json"
    comment_mappings = artifacts_dir / "comment_mappings.json"
    run_step("scripts/parse_review_comments.py", "--input", str(review_raw), "--output", str(review_comments))
    run_step(
        "scripts/build_comment_mappings.py",
        "--review-comments",
        str(review_comments),
        "--section-summaries",
        str(out / "paper" / "section_summaries.json"),
        "--asset-catalog",
        str(out / "assets" / "asset_catalog.json"),
        "--output",
        str(comment_mappings),
    )
    run_step("scripts/scaffold_revision_plans.py", "--review-comments", str(review_comments), "--comment-mappings", str(comment_mappings), "--output-dir", str(plans_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
