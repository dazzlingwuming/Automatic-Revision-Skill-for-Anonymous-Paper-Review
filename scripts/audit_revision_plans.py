"""Deterministic quality audit for v3.1 revision plans."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.jsonio import read_json, write_json


GENERIC_PHRASES = ["建议补充相关说明", "建议加强论证", "建议完善模型解释", "建议统一格式", "建议增加实验"]


def audit_plans(plans_dir: Path, output_path: Path) -> dict:
    issues = []
    for path in sorted(plans_dir.glob("*.json")):
        plan = read_json(path)
        comment_id = plan.get("comment_id", path.stem)
        for action in plan.get("actions", []):
            target = action.get("target", {})
            new_text = action.get("new_text", "")
            status = plan.get("revision_status", "")
            if not (target.get("section_id") or target.get("asset_id") or target.get("section_title")):
                issues.append({"comment_id": comment_id, "severity": "blocker", "problem": "缺少 section_id 或 asset_id 定位。", "required_fix": "补充 target.section_id/page_range 或 target.asset_id。"})
            if any(phrase == new_text.strip("。.") for phrase in GENERIC_PHRASES):
                issues.append({"comment_id": comment_id, "severity": "blocker", "problem": "修改方案只有泛泛建议。", "required_fix": "补充具体 new_text、实验模板、图表方案或检查清单。"})
            if status in {"text_ready", "text_ready_with_caveat"} and len(new_text) < 150:
                issues.append({"comment_id": comment_id, "severity": "blocker", "problem": "正文级修改意见 new_text 少于 150 个中文字符。", "required_fix": "补充可直接放入论文的新正文。"})
            if "已修改" in plan.get("reviewer_response", ""):
                issues.append({"comment_id": comment_id, "severity": "warning", "problem": "回复中出现已修改表述。", "required_fix": "没有 applied_changes 时应使用拟修改。"})
    data = {"passed": not any(issue["severity"] == "blocker" for issue in issues), "issues": issues}
    write_json(output_path, data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v3.1 revision plans.")
    parser.add_argument("--revision-plans-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit_plans(Path(args.revision_plans_dir), Path(args.output))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
