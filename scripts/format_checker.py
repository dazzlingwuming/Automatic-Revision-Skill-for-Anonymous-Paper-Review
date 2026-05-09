"""Run deterministic format checks on a paper index."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _issue(issue_id: str, issue_type: str, severity: str, location: str, description: str, suggestion: str) -> dict:
    return {
        "issue_id": issue_id,
        "issue_type": issue_type,
        "severity": severity,
        "location": location,
        "description": description,
        "suggestion": suggestion,
    }


def _has_heading(index: dict, patterns: list[str]) -> bool:
    headings = "\n".join(item.get("heading", "") for item in index.get("outline", []))
    chunk_heads = "\n".join(item.get("section") or item.get("chapter") or "" for item in index.get("chunks", []))
    text = headings + "\n" + chunk_heads
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def check_format(paper_index_path: Path, output_path: Path) -> dict:
    index = json.loads(paper_index_path.read_text(encoding="utf-8"))
    issues: list[dict] = []

    checks = [
        ("F001", "missing_section", "warning", "全文", ["摘要", r"\babstract\b"], "未检测到摘要部分", "请确认论文开头是否包含摘要。"),
        ("F002", "missing_section", "warning", "全文", ["关键词", r"\bkeywords\b"], "未检测到关键词部分", "请确认摘要后是否包含关键词。"),
        ("F003", "missing_section", "warning", "全文", ["目录", r"\bcontents\b"], "未检测到目录部分", "请确认论文是否需要目录。"),
        ("F004", "missing_section", "warning", "全文", ["参考文献", r"\breferences\b"], "未检测到参考文献部分", "请确认论文末尾是否包含参考文献。"),
    ]
    for issue_id, issue_type, severity, location, patterns, description, suggestion in checks:
        if not _has_heading(index, patterns):
            issues.append(_issue(issue_id, issue_type, severity, location, description, suggestion))

    references = index.get("references", [])
    if references and len(references) < 5:
        issues.append(_issue("F005", "few_references", "warning", "参考文献", f"检测到参考文献条目较少：{len(references)} 条", "请确认参考文献数量是否符合学校要求。"))

    for kind, key, issue_id in [("图", "figures", "F006"), ("表", "tables", "F007")]:
        ids = [item.get("id", "") for item in index.get(key, [])]
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1 and item_id})
        if duplicates:
            issues.append(_issue(issue_id, "duplicate_number", "warning", "全文", f"{kind}编号存在重复：{', '.join(duplicates)}", f"请检查{kind}编号是否唯一且连续。"))

    data = {"issues": issues}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Check paper format from paper_index.json.")
    parser.add_argument("--paper-index", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    check_format(Path(args.paper_index), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

