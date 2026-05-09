"""Parse raw blind-review text into review_comments.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ISSUE_RE = re.compile(r"^\s*(?:[（(]?\d+[）)、,.，]|[①②③④⑤⑥⑦⑧⑨⑩])\s*(.+)")


def _load_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if "pages" in data:
            return "\n".join(page.get("text", "") for page in data["pages"])
        return data.get("text", text)
    return text


def _reviewer_sections(text: str) -> list[str]:
    marker = "学位论文存在的不足及需要修改之处"
    parts = text.split(marker)
    if len(parts) <= 1:
        return [text]
    sections = []
    for part in parts[1:]:
        section = part.split("中南林业科技大学学术型硕士学位论文评阅意见书")[0]
        sections.append(section)
    return sections


def _numbered_issues(section: str) -> list[str]:
    issues: list[str] = []
    current: list[str] = []
    for raw_line in section.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue
        match = ISSUE_RE.match(line)
        if match:
            if current:
                issues.append("".join(current).strip())
            current = [match.group(1).strip()]
        elif current and not _is_boilerplate(line):
            current.append(line)
    if current:
        issues.append("".join(current).strip())
    return [issue for issue in issues if len(issue) >= 8]


def _is_boilerplate(line: str) -> bool:
    return any(token in line for token in ["【打印】", "【关闭】", "【TOP】", "问题和建议", "此外，论文在写作中还要注意"])


def _category(text: str) -> str:
    if any(word in text for word in ["参考文献", "文献", "出处", "预印"]):
        return "参考文献"
    if any(word in text for word in ["CGE", "经济学", "理论", "替代关系", "传统要素"]):
        return "理论基础"
    if any(word in text for word in ["MILP", "模型", "归一化", "量纲", "约束", "双向耦合", "反馈"]):
        return "方法设计"
    if any(word in text for word in ["实验", "场景", "节点", "数据", "有效性"]):
        return "数据实验"
    if any(word in text for word in ["图", "表", "公式", "段落格式", "破折号", "格式"]):
        return "格式规范"
    if any(word in text for word in ["写作", "逻辑", "描述", "论证"]):
        return "结构逻辑"
    return "其他"


def _scope(text: str) -> str:
    if "参考文献" in text or "文献" in text:
        return "参考文献"
    if "图" in text or "公式" in text or "表格" in text or re.search(r"表\s*\d", text):
        return "图表"
    if any(word in text for word in ["全文", "所有", "多处"]):
        return "全文"
    if any(word in text for word in ["页", "章节", "章", "节"]):
        return "章节"
    return "章节"


def _action_type(text: str) -> str:
    if "参考文献" in text or "文献" in text:
        return "补充引用"
    if any(word in text for word in ["实验", "场景", "节点数量"]):
        return "补充实验"
    if any(word in text for word in ["图", "表", "公式", "格式", "破折号"]):
        return "格式修正"
    if any(word in text for word in ["补充", "论证", "描述", "解释"]):
        return "补充解释"
    return "其他"


def _requires_author_input(text: str) -> bool:
    return any(word in text for word in ["实验", "节点数量", "场景", "数据", "参考文献", "文献", "出处", "正式发表"])


def parse_review_comments(input_path: Path, output_path: Path) -> dict:
    text = _load_text(input_path)
    comments = []
    for reviewer_index, section in enumerate(_reviewer_sections(text), start=1):
        for issue_index, issue in enumerate(_numbered_issues(section), start=1):
            comment_id = f"R{reviewer_index}-C{issue_index:03d}"
            comments.append(
                {
                    "comment_id": comment_id,
                    "reviewer_id": f"R{reviewer_index}",
                    "original_text": issue,
                    "normalized_text": issue,
                    "category": _category(issue),
                    "severity": "重点修改" if reviewer_index <= 2 else "建议修改",
                    "scope": _scope(issue),
                    "action_type": _action_type(issue),
                    "requires_author_input": _requires_author_input(issue),
                    "confidence": 0.82,
                    "notes": "由确定性规则从盲审意见文本中抽取，建议后续由 review-parser 复核。",
                }
            )
    data = {"comments": comments}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse blind-review comments into schema JSON.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    parse_review_comments(Path(args.input), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
