"""Unified entrypoint for the provider-neutral thesis revision pipeline."""

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


def run_step_allow_failure(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False)


def prepare(args: argparse.Namespace) -> None:
    if not args.paper_docx:
        raise ValueError("--paper-docx is required for prepare/full mode")
    if not args.review:
        raise ValueError("--review is required for prepare/full mode")
    run_step(
        "scripts/run_docx_first_prepare.py",
        "--paper-docx",
        args.paper_docx,
        "--review",
        args.review,
        "--out",
        args.out,
        "--title",
        args.title or "",
    )


def report(args: argparse.Namespace) -> None:
    out = Path(args.out)
    review_comments = out / "artifacts" / "review_comments.json"
    revision_plans = out / "revision_plans"
    notes_dir = out / "revision_plan_notes"
    outputs_dir = out / "outputs"
    audits_dir = out / "audits"
    audits_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    run_step("scripts/render_revision_plan_notes.py", "--revision-plans-dir", str(revision_plans), "--output-dir", str(notes_dir))
    audit_result = run_step_allow_failure("scripts/audit_revision_solutions.py", "--revision-plans-dir", str(revision_plans), "--output", str(audits_dir / "revision_solution_audit.json"))
    if audit_result.returncode != 0:
        print("warning: revision solution audit did not pass; continuing to render draft outputs", file=sys.stderr)
    run_step(
        "scripts/build_report.py",
        "--review-comments",
        str(review_comments),
        "--revision-plans-dir",
        str(revision_plans),
        "--output-dir",
        str(outputs_dir),
        "--paper-file",
        args.paper_docx or "",
        "--review-file",
        args.review or "",
        "--generated-at",
        args.generated_at or "",
        "--mode",
        args.report_mode,
    )
    if args.paper_docx:
        run_step(
            "scripts/patch_docx.py",
            "--input-docx",
            args.paper_docx,
            "--revision-plans-dir",
            str(revision_plans),
            "--output",
            str(outputs_dir / "05_修改建议版.docx"),
        )
        run_step(
            "scripts/patch_docx.py",
            "--input-docx",
            args.paper_docx,
            "--revision-plans-dir",
            str(revision_plans),
            "--output",
            str(outputs_dir / "06_整合修改稿.docx"),
            "--mode",
            "apply",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the universal thesis revision agent pipeline.")
    parser.add_argument("--paper-docx", help="Primary thesis DOCX file.")
    parser.add_argument("--review", help="Blind-review comments file: PDF, DOCX, TXT, or Markdown.")
    parser.add_argument("--out", required=True, help="Run directory.")
    parser.add_argument("--title", default="")
    parser.add_argument("--mode", choices=["prepare", "report", "full"], default="full")
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--report-mode", default="建议修改")
    args = parser.parse_args()

    if args.mode in {"prepare", "full"}:
        prepare(args)
    if args.mode in {"report", "full"}:
        report(args)
    print(f"pipeline {args.mode} complete: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
