"""Deterministic candidate recall for sections and assets."""

from __future__ import annotations

import re


def _tokens(text: str) -> list[str]:
    parts = re.split(r"[\s，,。；;：:（）()\[\]【】/\\-]+", text)
    return [part for part in parts if len(part) >= 2]


def score_text(query: str, text: str) -> int:
    return sum(text.count(token) for token in _tokens(query))


def recall_sections(comment_text: str, section_summaries: dict, limit: int = 20) -> list[dict]:
    scored = []
    for section in section_summaries.get("sections", []):
        haystack = " ".join(
            [
                section.get("title", ""),
                section.get("summary_short", ""),
                section.get("summary_detailed", ""),
                " ".join(section.get("key_terms", [])),
                " ".join(section.get("potential_review_topics", [])),
            ]
        )
        score = score_text(comment_text, haystack)
        scored.append((score, section))
    ranked = [section for score, section in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0]
    return ranked[:limit]


def recall_assets(comment_text: str, asset_catalog: dict, limit: int = 20) -> list[dict]:
    scored = []
    for asset in asset_catalog.get("assets", []):
        haystack = " ".join([asset.get("label", ""), asset.get("caption", ""), asset.get("nearby_text_before", ""), asset.get("nearby_text_after", "")])
        score = score_text(comment_text, haystack)
        if asset.get("label") and asset["label"] in comment_text.replace(" ", ""):
            score += 10
        scored.append((score, asset))
    ranked = [asset for score, asset in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0]
    return ranked[:limit]

