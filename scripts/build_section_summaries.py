"""Build deterministic MVP section_summaries.json and paper_brief.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.jsonio import read_json, write_json


KEYWORDS = ["CGE", "CES", "MILP", "SLA", "碳", "电价", "带宽", "算力", "图", "表", "参考文献", "实验", "集成验证", "双向耦合"]


def _read_section_text(sections_dir: Path, section_id: str) -> str:
    path = sections_dir / f"{section_id}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _summary(text: str, max_chars: int) -> str:
    clean = " ".join(text.split())
    return clean[:max_chars]


def _terms(text: str) -> list[str]:
    return [keyword for keyword in KEYWORDS if keyword.lower() in text.lower()]


def _topics(text: str, title: str) -> list[str]:
    corpus = title + " " + text
    topics = []
    if any(word in corpus for word in ["CGE", "CES", "生产函数", "替代"]):
        topics.append("理论基础")
    if any(word in corpus for word in ["MILP", "模型", "约束", "成本"]):
        topics.append("方法设计")
    if any(word in corpus for word in ["实验", "验证", "场景", "结果"]):
        topics.append("数据实验")
    if any(word in corpus for word in ["图", "表", "公式", "格式"]):
        topics.append("格式规范")
    if "参考文献" in corpus:
        topics.append("参考文献")
    return topics or ["其他"]


def build_summaries(structure_path: Path, sections_dir: Path, output_path: Path, brief_output: Path, asset_catalog_path: Path | None = None) -> dict:
    structure = read_json(structure_path)
    assets = read_json(asset_catalog_path).get("assets", []) if asset_catalog_path and asset_catalog_path.exists() else []
    assets_by_section: dict[str, list[str]] = {}
    for asset in assets:
        if asset.get("section_id"):
            assets_by_section.setdefault(asset["section_id"], []).append(asset["asset_id"])

    summaries = []
    brief_lines = ["# 论文压缩上下文", "", "## 论文主题", "", structure.get("paper_title") or "未识别论文题目", "", "## 章节结构"]
    for section in structure.get("sections", []):
        text = _read_section_text(sections_dir, section["section_id"])
        page_range = f"{section.get('page_start')}-{section.get('page_end')}" if section.get("page_start") else None
        terms = _terms(text + section["title"])
        item = {
            "section_id": section["section_id"],
            "title": section["title"],
            "level": section["level"],
            "page_range": page_range,
            "summary_short": _summary(text, 120),
            "summary_detailed": _summary(text, 500),
            "key_claims": re.findall(r"本文[^。]{5,80}。", text)[:5],
            "key_terms": terms,
            "related_assets": assets_by_section.get(section["section_id"], []),
            "potential_review_topics": _topics(text, section["title"]),
        }
        summaries.append(item)
        if section["level"] <= 2:
            brief_lines.append(f"- {section['title']}：{item['summary_short']}")
    brief_lines.extend(["", "## 图表目录摘要"])
    for asset in assets:
        brief_lines.append(f"- {asset['label']}：{asset['caption']}（{asset.get('section_title') or '未定位章节'}）")

    data = {"sections": summaries}
    write_json(output_path, data)
    brief_output.parent.mkdir(parents=True, exist_ok=True)
    brief_output.write_text("\n".join(brief_lines), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Build section summaries and paper brief.")
    parser.add_argument("--structure", required=True)
    parser.add_argument("--sections-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--brief-output", required=True)
    parser.add_argument("--asset-catalog")
    args = parser.parse_args()
    build_summaries(Path(args.structure), Path(args.sections_dir), Path(args.output), Path(args.brief_output), Path(args.asset_catalog) if args.asset_catalog else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
