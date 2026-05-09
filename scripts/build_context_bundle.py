"""Build v3.1 context bundles from mappings and paper artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.jsonio import read_json, write_json


def _section_summary(section_id: str, summaries: dict) -> dict | None:
    return next((item for item in summaries.get("sections", []) if item["section_id"] == section_id), None)


def _section_text_path(workdir: Path, section_id: str) -> str:
    return str(workdir / "paper" / "sections" / f"{section_id}.md")


def build_bundle(comment_id: str, workdir: Path, output_path: Path) -> dict:
    comments = read_json(workdir / "artifacts" / "review_comments.json")["comments"]
    mappings = read_json(workdir / "artifacts" / "comment_mappings.json")["mappings"]
    summaries = read_json(workdir / "paper" / "section_summaries.json")
    assets = read_json(workdir / "assets" / "asset_catalog.json").get("assets", [])
    brief_path = workdir / "paper" / "paper_brief.md"
    comment = next(item for item in comments if item["comment_id"] == comment_id)
    mapping = next(item for item in mappings if item["comment_id"] == comment_id)

    must = []
    also = []
    summary_only = []
    for loc in mapping.get("locations", []):
        if not loc.get("section_id"):
            continue
        evidence = {
            "section_id": loc["section_id"],
            "title": loc.get("title") or loc["section_id"],
            "page_range": loc.get("page_range"),
            "text_path": _section_text_path(workdir, loc["section_id"]),
            "reason": loc.get("reason", ""),
        }
        if loc["role"] == "core_revision_location":
            must.append(evidence)
        elif loc["include_mode"] == "full_text":
            also.append(evidence)
        else:
            sec = _section_summary(loc["section_id"], summaries)
            if sec:
                summary_only.append({"section_id": sec["section_id"], "title": sec["title"], "summary_detailed": sec["summary_detailed"]})

    asset_ids = {item["asset_id"] for item in mapping.get("assets", [])}
    visual_assets = [asset for asset in assets if asset["asset_id"] in asset_ids and asset["asset_type"] == "figure"]
    table_assets = [asset for asset in assets if asset["asset_id"] in asset_ids and asset["asset_type"] == "table"]

    outline = [
        {"section_id": sec["section_id"], "title": sec["title"], "summary_short": sec["summary_short"]}
        for sec in summaries.get("sections", [])
        if sec.get("level", 9) <= 2
    ]
    bundle = {
        "comment_id": comment_id,
        "comment": {
            "original_text": comment["original_text"],
            "category": comment["category"],
            "severity": comment["severity"],
            "action_type": comment["action_type"],
        },
        "paper_brief": {
            "path": str(brief_path),
            "inline_summary": brief_path.read_text(encoding="utf-8")[:1200] if brief_path.exists() else "",
        },
        "global_outline": outline,
        "evidence_pack": {
            "must_read_full_text": must,
            "also_read_full_text": also,
            "summary_only_sections": summary_only,
            "formulas": [],
            "visual_assets": visual_assets,
            "table_assets": table_assets,
        },
        "output_contract": {
            "must_include_insert_position": True,
            "must_include_anchor_text": True,
            "must_include_new_or_revised_text": True,
            "must_include_reviewer_response": True,
            "forbidden_generic_advice": True,
        },
    }
    write_json(output_path, bundle)
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one v3.1 context bundle.")
    parser.add_argument("--comment-id", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build_bundle(args.comment_id, Path(args.workdir), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
