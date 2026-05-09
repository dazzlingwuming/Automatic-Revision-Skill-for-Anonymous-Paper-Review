"""Build deterministic multi-location mappings for review comments."""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(text: str) -> list[str]:
    return [part for part in re.split(r"[\s，,。；;：:（）()\[\]【】/\\-]+", text) if len(part) >= 2]


def _score_text(query: str, text: str) -> int:
    return sum(text.count(token) for token in _tokens(query))


def _recall_sections(comment_text: str, section_summaries: dict, limit: int = 20) -> list[dict]:
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
        scored.append((_score_text(comment_text, haystack), section))
    return [section for score, section in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:limit]


def _recall_assets(comment_text: str, asset_catalog: dict, limit: int = 20) -> list[dict]:
    normalized_query = comment_text.replace(" ", "")
    scored = []
    for asset in asset_catalog.get("assets", []):
        haystack = " ".join([asset.get("label", ""), asset.get("caption", ""), asset.get("nearby_text_before", ""), asset.get("nearby_text_after", "")])
        score = _score_text(comment_text, haystack)
        if asset.get("label") and asset["label"].replace(" ", "") in normalized_query:
            score += 10
        scored.append((score, asset))
    return [asset for score, asset in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:limit]


def _location_from_section(section: dict, role: str, reason: str, confidence: float) -> dict:
    return {
        "role": role,
        "section_id": section.get("section_id"),
        "title": section.get("title"),
        "page_range": section.get("page_range"),
        "reason": reason,
        "include_mode": "full_text" if role == "core_revision_location" else "summary_plus_target_paragraphs",
        "confidence": confidence,
    }


def _heuristic_sections(comment: dict, summaries: dict) -> list[dict]:
    text = comment["original_text"]
    wanted: list[str] = []
    if any(word in text for word in ["替代关系", "传统要素", "CGE", "经济学解释"]):
        wanted = ["CGE模型构建", "生产模块", "总结", "研究内容"]
    elif any(word in text for word in ["量纲", "归一化", "电价", "碳成本", "带宽成本", "SLA"]):
        wanted = ["多因子集成成本模型", "构建CEOP-MILP模型", "实验设置"]
    elif any(word in text for word in ["双向耦合", "反馈", "约束路线"]):
        wanted = ["集成验证", "本文组织架构", "主要研究内容", "总结"]
    elif any(word in text for word in ["节点数量", "节点"]):
        wanted = ["数据收集与实验设置", "问题描述", "实验结果与分析"]
    elif any(word in text for word in ["场景", "单一"]):
        wanted = ["集成验证", "实验结果对比", "实验与分析"]
    elif "段落格式" in text:
        wanted = ["前置部分", "绪论"]
    elif "破折号" in text:
        wanted = ["前置部分", "绪论"]
    elif "公式" in text:
        wanted = ["构建CEOP-MILP模型", "面向算力规划的多区域CGE模型构建"]
    elif "所有对图引出的句子" in text or "对于表格也是如此" in text:
        wanted = ["主要研究内容", "构建CEOP-MILP模型", "实验结果与分析"]
    elif "参考文献" in text or "文献" in text:
        wanted = ["参考文献"]
    sections = []
    for keyword in wanted:
        matched = None
        for section in summaries.get("sections", []):
            if keyword in section.get("title", ""):
                matched = section
                break
        if matched is None:
            for section in summaries.get("sections", []):
                if keyword in section.get("summary_short", "") or keyword in section.get("summary_detailed", ""):
                    matched = section
                    break
        if matched and matched not in sections:
            sections.append(matched)
    return sections


def build_comment_mappings(review_comments_path: Path, section_summaries_path: Path, asset_catalog_path: Path, output_path: Path) -> dict:
    comments = _read_json(review_comments_path)["comments"]
    summaries = _read_json(section_summaries_path)
    assets = _read_json(asset_catalog_path)
    mappings = []
    for comment in comments:
        text = comment["original_text"]
        recalled_assets = _recall_assets(text.replace(" ", ""), assets, limit=5)
        recalled_sections = _heuristic_sections(comment, summaries) + _recall_sections(text, summaries, limit=5)
        locations = []
        asset_refs = []
        if recalled_assets:
            for asset in recalled_assets[:3]:
                asset_refs.append(
                    {
                        "asset_id": asset["asset_id"],
                        "role": "core_asset" if len(asset_refs) == 0 else "supporting_asset",
                        "reason": f"评审意见与{asset.get('label') or asset['asset_id']}匹配。",
                    }
                )
                if asset.get("section_id"):
                    locations.append(
                        {
                            "role": "core_revision_location" if len(locations) == 0 else "visual_or_table_asset",
                            "section_id": asset.get("section_id"),
                            "title": asset.get("section_title"),
                            "page_range": None,
                            "reason": f"该图表资产与意见直接相关：{asset.get('caption') or asset.get('label')}",
                            "include_mode": "full_text" if len(locations) == 0 else "asset_only",
                            "confidence": 0.88,
                        }
                    )
        for section in recalled_sections:
            if any(loc.get("section_id") == section.get("section_id") for loc in locations):
                continue
            role = "core_revision_location" if not locations else "supporting_context"
            locations.append(_location_from_section(section, role, "章节摘要与评审意见关键词匹配。", 0.72 if role == "core_revision_location" else 0.62))
            if len(locations) >= 4:
                break
        if not locations:
            locations.append(
                {
                    "role": "author_input_location" if comment.get("requires_author_input") else "core_revision_location",
                    "section_id": None,
                    "title": None,
                    "page_range": None,
                    "reason": "确定性召回未找到可靠章节，需要人工定位。",
                    "include_mode": "summary_only",
                    "confidence": 0.2,
                }
            )
        visual = comment.get("scope") == "图表" or bool(asset_refs)
        mappings.append(
            {
                "comment_id": comment["comment_id"],
                "mapping_type": "visual_table" if visual else "multi_section" if len(locations) > 1 else "single_section",
                "locations": locations,
                "assets": asset_refs,
                "requires_author_input": bool(comment.get("requires_author_input")),
                "confidence": max(loc["confidence"] for loc in locations),
                "needs_human_location_check": locations[0].get("section_id") is None or (visual and not asset_refs),
                "notes": "确定性候选映射，供 revision-planner 使用前复核。",
            }
        )
    data = {"mappings": mappings}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Build comment_mappings.json from comments, sections, and assets.")
    parser.add_argument("--review-comments", required=True)
    parser.add_argument("--section-summaries", required=True)
    parser.add_argument("--asset-catalog", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build_comment_mappings(Path(args.review_comments), Path(args.section_summaries), Path(args.asset_catalog), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
