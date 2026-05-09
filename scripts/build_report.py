"""Build final Markdown reports from validated JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS_LABELS = {
    "can_revise": "拟修改",
    "needs_author_input": "需要作者补充",
    "explain_only": "建议解释回应",
    "not_applicable": "不适用",
    "uncertain": "不确定",
    "text_ready": "拟修改",
    "text_ready_with_caveat": "拟修改（需作者核对）",
    "visual_redraw_needed": "需要重绘图表",
    "format_fix_ready": "格式修改",
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_plans(plans_dir: Path) -> dict[str, dict]:
    plans = {}
    for path in sorted(plans_dir.glob("*.json")):
        data = _read_json(path)
        plans[data["comment_id"]] = data
    return plans


def _location_text(action: dict) -> str:
    if "target" in action:
        target = action.get("target", {})
        section = target.get("section_title") or target.get("section_id") or "未定位"
        page = target.get("page_range") or "无页码"
        asset = target.get("asset_id")
        return f"{section}，页码 {page}" + (f"，asset: {asset}" if asset else "")
    location = action.get("location", {})
    section = location.get("section") or "未定位"
    page = location.get("page_range") or "无页码"
    chunk = location.get("chunk_id") or "无chunk"
    return f"{section}，页码 {page}，chunk: {chunk}"


def _plan_strategy(plan: dict) -> str:
    return plan.get("overall_strategy") or plan.get("revision_strategy") or ""


def _plan_actions(plan: dict) -> list[dict]:
    if "actions" in plan:
        return plan["actions"]
    converted = []
    for action in plan.get("specific_actions", []):
        location = action.get("location", {})
        converted.append(
            {
                "action_id": action.get("action_id", ""),
                "type": action.get("type", ""),
                "target": {
                    "section_id": None,
                    "section_title": location.get("section"),
                    "page_range": location.get("page_range"),
                    "asset_id": None,
                },
                "anchor_text": "请根据定位位置和原文摘录人工确认插入点。",
                "original_text": action.get("before_excerpt", ""),
                "new_text": action.get("after_proposed_text", ""),
                "rationale": action.get("rationale", ""),
                "requires_author_input": bool(plan.get("author_input_needed")),
            }
        )
    return converted


def _reviewer_response(plan: dict) -> str:
    return plan.get("reviewer_response") or plan.get("response_to_reviewer") or ""


def _category_counts(comments: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for comment in comments:
        category = comment.get("category", "其他")
        counts[category] = counts.get(category, 0) + 1
    return counts


def build_reports(
    review_comments_path: Path,
    revision_plans_dir: Path,
    output_dir: Path,
    paper_file: str = "",
    review_file: str = "",
    generated_at: str = "",
    mode: str = "建议修改",
    format_issues_path: Path | None = None,
) -> dict:
    comments = _read_json(review_comments_path)["comments"]
    plans = _load_plans(revision_plans_dir)
    format_issues = _read_json(format_issues_path).get("issues", []) if format_issues_path and format_issues_path.exists() else []
    output_dir.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# 学位论文盲审意见修改报告",
        "",
        "## 一、基本信息",
        "",
        f"- 论文文件：{paper_file}",
        f"- 盲审意见文件：{review_file}",
        f"- 生成时间：{generated_at}",
        f"- 处理模式：{mode}",
        "",
        "## 二、盲审意见总览",
        "",
        f"共收到 {len(comments)} 条可处理意见。",
        "",
        "| 类别 | 数量 |",
        "|---|---:|",
    ]
    for category, count in _category_counts(comments).items():
        report_lines.append(f"| {category} | {count} |")

    response_lines = [
        "# 盲审意见回应表",
        "",
        "| 序号 | 评审意见 | 修改情况 | 修改位置 | 回复说明 |",
        "|---:|---|---|---|---|",
    ]
    author_lines = [
        "# 作者待补充事项",
        "",
        "以下事项需要作者提供真实信息、实验结果、数据、引用或决策后才能完成。",
        "",
        "| 意见编号 | 待补充事项 | 需要的材料 | 建议处理方式 |",
        "|---|---|---|---|",
    ]

    report_lines.extend(["", "## 三、逐条修改方案", ""])
    for index, comment in enumerate(comments, start=1):
        plan = plans.get(comment["comment_id"])
        if not plan:
            continue
        status = STATUS_LABELS.get(plan["revision_status"], plan["revision_status"])
        actions = _plan_actions(plan)
        first_action = actions[0] if actions else {"target": {}}
        location = _location_text(first_action)
        report_lines.extend(
            [
                f"### {comment['comment_id']}",
                "",
                "#### 评审意见",
                "",
                comment["original_text"],
                "",
                "#### 定位依据",
                "",
                f"- 核心修改位置：{location}",
                f"**分类：** {comment['category']}  ",
                f"**严重程度：** {comment['severity']}  ",
                f"**处理状态：** {status}",
                "",
                f"修改策略：{_plan_strategy(plan)}",
                "",
            ]
        )
        if plan.get("problem_diagnosis"):
            report_lines.extend(["#### 问题诊断", "", plan["problem_diagnosis"], ""])
        if plan.get("evidence_coverage"):
            report_lines.extend(["#### 论文证据与定位", "", "| 角色 | 位置 | 证据 | 用途 |", "|---|---|---|---|"])
            for evidence in plan["evidence_coverage"]:
                where = evidence.get("section_title") or evidence.get("section_id") or evidence.get("asset_id") or "未定位"
                report_lines.append(
                    f"| {evidence.get('role', '')} | {where} | {evidence.get('evidence', '')} | {evidence.get('use', '')} |"
                )
            report_lines.append("")
        for action in actions:
            report_lines.extend(
                [
                    f"#### 具体修改 {action['action_id']}：{action['type']}",
                    "",
                    f"- 插入/修改位置：{_location_text(action)}",
                    f"- 原文锚点：{action.get('anchor_text', '')}",
                    f"- 修改理由：{action.get('rationale', '')}",
                    "",
                ]
            )
            if action.get("visual_diagnosis"):
                report_lines.extend(["##### 图表问题诊断", ""])
                report_lines.extend(f"- {item}" for item in action["visual_diagnosis"])
                report_lines.append("")
            if action.get("caption_suggestion"):
                report_lines.extend(["##### 图题/表题建议", "", f"> {action['caption_suggestion']}", ""])
            report_lines.extend(
                [
                    "##### 修改前",
                    "",
                    f"> {action.get('original_text') or '原文未提供可直接引用片段，需结合定位位置人工确认。'}",
                    "",
                    "##### 新增/修改正文或操作方案",
                    "",
                    f"> {action.get('new_text', '')}",
                    "",
                ]
            )
        if plan.get("synchronized_updates"):
            report_lines.extend(["#### 同步修改建议", "", "| 位置 | 建议文本 | 原因 |", "|---|---|---|"])
            for update in plan["synchronized_updates"]:
                target = update.get("target", {})
                where = target.get("section_title") or target.get("section_id") or target.get("asset_id") or "未定位"
                report_lines.append(f"| {where} | {update.get('new_text', '')} | {update.get('reason', '')} |")
            report_lines.append("")
        report_lines.extend(["#### 给评审专家的回复", "", f"> {_reviewer_response(plan)}", "", "#### 是否需要作者补充", ""])
        if plan.get("author_input_needed"):
            report_lines.extend(f"- {item['item']}：{item['needed_material']}" for item in plan["author_input_needed"])
        else:
            report_lines.append("无。")
        report_lines.extend(["", "---", ""])
        response_lines.append(
            f"| {index} | {comment['original_text']} | {status} | {_location_text(first_action)} | {_reviewer_response(plan)} |"
        )
        for item in plan.get("author_input_needed", []):
            author_lines.append(
                f"| {plan['comment_id']} | {item['item']} | {item['needed_material']} | {item['reason']} |"
            )

    report_lines.extend(["## 四、格式问题清单", "", "| 问题编号 | 严重程度 | 位置 | 问题 | 建议 |", "|---|---|---|---|---|"])
    for issue in format_issues:
        report_lines.append(
            f"| {issue['issue_id']} | {issue['severity']} | {issue['location']} | {issue['description']} | {issue['suggestion']} |"
        )
    report_lines.extend(["", "## 五、作者待补充事项", ""])
    report_lines.extend(author_lines[4:])
    report_lines.extend(
        [
            "",
            "## 六、修改总结",
            "",
            "本报告基于已提取论文文本、盲审意见和结构化修改方案生成。所有内容均为拟修改建议；凡涉及新增实验、真实数据、图件源文件或参考文献真实性核查的事项，均已列入作者待补充事项。",
        ]
    )

    (output_dir / "修改报告.md").write_text("\n".join(report_lines), encoding="utf-8")
    (output_dir / "盲审回应表.md").write_text("\n".join(response_lines), encoding="utf-8")
    (output_dir / "作者待补充事项.md").write_text("\n".join(author_lines), encoding="utf-8")
    return {"report": str(output_dir / "修改报告.md"), "response_table": str(output_dir / "盲审回应表.md")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build final Markdown reports from JSON artifacts.")
    parser.add_argument("--review-comments", required=True)
    parser.add_argument("--revision-plans-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--paper-file", default="")
    parser.add_argument("--review-file", default="")
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--mode", default="建议修改")
    parser.add_argument("--format-issues")
    args = parser.parse_args()
    build_reports(
        Path(args.review_comments),
        Path(args.revision_plans_dir),
        Path(args.output_dir),
        paper_file=args.paper_file,
        review_file=args.review_file,
        generated_at=args.generated_at,
        mode=args.mode,
        format_issues_path=Path(args.format_issues) if args.format_issues else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
