"""Simple deterministic retrieval helpers for chunk metadata."""

from __future__ import annotations


def keyword_score(text: str, keywords: list[str]) -> int:
    return sum(text.count(keyword) for keyword in keywords if keyword)


def rank_chunks(chunks: list[dict], query: str, limit: int = 5) -> list[dict]:
    keywords = [part for part in query.replace("，", " ").replace(",", " ").split() if part]
    scored = []
    for chunk in chunks:
        searchable = " ".join(str(chunk.get(key, "")) for key in ["heading_guess", "summary", "section", "chapter"])
        scored.append((keyword_score(searchable, keywords), chunk))
    return [chunk for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True)[:limit] if score > 0]

