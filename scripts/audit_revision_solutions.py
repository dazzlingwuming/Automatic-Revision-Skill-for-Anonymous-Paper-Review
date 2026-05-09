"""Audit deep revision plans for actionability and completeness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


GENERIC_TEXTS = ["建议补充相关说明", "建议加强论证", "建议完善模型解释", "建议统一格式", "建议增加实验"]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rubric_item(score: int, max_score: int, issues: list[str]) -> dict:
    return {"score": score, "max_score": max_score, "issues": issues}


def audit_plan(plan: dict) -> dict:
    blockers: list[str] = []
    required_fixes: list[str] = []
    diagnosis_issues = []
    evidence_issues = []
    action_issues = []
    multi_issues = []
    integrity_issues = []
    response_issues = []

    if len(plan.get("problem_diagnosis", "").strip()) < 40:
        diagnosis_issues.append("缺少充分的问题诊断。")
        blockers.append("缺少 problem_diagnosis。")
        required_fixes.append("说明评审为何提出该问题、论文现有不足是什么。")

    evidence = plan.get("evidence_coverage", [])
    if len(evidence) < 1:
        evidence_issues.append("缺少论文证据覆盖。")
        blockers.append("缺少 evidence_coverage。")
        required_fixes.append("至少列出核心修改章节及其用途。")
    if len(evidence) < 2 and plan.get("revision_status") not in {"format_fix_ready", "not_applicable"}:
        multi_issues.append("缺少跨章节或同步修改位置。")
        required_fixes.append("补充支撑章节、结论/摘要/创新点等同步修改位置。")

    actions = plan.get("actions", [])
    if not actions:
        action_issues.append("缺少具体修改动作。")
        blockers.append("缺少 actions。")
    for action in actions:
        target = action.get("target", {})
        new_text = action.get("new_text", "").strip()
        if not (target.get("section_id") or target.get("asset_id")):
            action_issues.append(f"{action.get('action_id', '')} 缺少 section_id 或 asset_id。")
            blockers.append("具体修改动作缺少定位。")
        if any(new_text.strip("。.") == phrase for phrase in GENERIC_TEXTS):
            action_issues.append(f"{action.get('action_id', '')} 是泛泛建议。")
            blockers.append("存在泛泛建议。")
        if action.get("type") in {"insert_after_paragraph", "replace_paragraph", "rewrite_sentence"} and len(new_text) < 150:
            action_issues.append(f"{action.get('action_id', '')} 正文级 new_text 少于 150 字。")
            blockers.append("正文级修改不够详细。")
        if any(word in new_text for word in ["提升12", "提高了", "降低了"]) and action.get("requires_author_input"):
            integrity_issues.append("需要作者输入的实验类内容疑似写成已完成结果。")
            blockers.append("可能编造实验结果。")

    if not plan.get("synchronized_updates") and plan.get("revision_status") in {"text_ready", "text_ready_with_caveat"}:
        multi_issues.append("缺少同步修改建议。")
        required_fixes.append("补充摘要、结论、创新点、图表引导语或相关章节的一致性修改。")

    response = plan.get("reviewer_response", "")
    if len(response.strip()) < 40:
        response_issues.append("盲审回复过短。")
        required_fixes.append("补充可提交的盲审回复文本。")
    if "已修改" in response and not plan.get("applied_changes"):
        response_issues.append("未实际回写时不应声称已修改。")
        blockers.append("回复表述过度承诺。")

    rubric = {
        "addresses_comment": _rubric_item(20 - min(20, len(diagnosis_issues) * 10), 20, diagnosis_issues),
        "uses_paper_evidence": _rubric_item(15 - min(15, len(evidence_issues) * 8), 15, evidence_issues),
        "actionability": _rubric_item(20 - min(20, len(action_issues) * 6), 20, action_issues),
        "multi_location_coverage": _rubric_item(15 - min(15, len(multi_issues) * 8), 15, multi_issues),
        "integrity": _rubric_item(15 - min(15, len(integrity_issues) * 15), 15, integrity_issues),
        "reviewer_response": _rubric_item(15 - min(15, len(response_issues) * 8), 15, response_issues),
    }
    score = sum(item["score"] for item in rubric.values())
    passed = not blockers and score >= 80
    decision = "pass" if passed else "revise"
    if plan.get("revision_status") == "needs_author_input" and not blockers:
        decision = "needs_author_input"
    return {
        "comment_id": plan.get("comment_id", ""),
        "passed": passed,
        "overall_score": score,
        "decision": decision,
        "rubric": rubric,
        "blockers": sorted(set(blockers)),
        "required_fixes": sorted(set(required_fixes)),
        "retry_instruction": "；".join(sorted(set(required_fixes))) if required_fixes else "无需重试。",
    }


def audit_revision_solutions(plans_dir: Path, output_path: Path) -> dict:
    audits = [audit_plan(_read_json(path)) for path in sorted(plans_dir.glob("*.json"))]
    data = {"passed": all(item["passed"] or item["decision"] == "needs_author_input" for item in audits), "audits": audits}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit deep revision solution plans.")
    parser.add_argument("--revision-plans-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit_revision_solutions(Path(args.revision_plans_dir), Path(args.output))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
