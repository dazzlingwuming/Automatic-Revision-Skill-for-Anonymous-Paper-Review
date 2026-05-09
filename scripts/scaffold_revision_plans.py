"""Create schema-valid revision plan scaffolds from comments and mappings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _status(comment: dict, mapping: dict) -> str:
    if comment["scope"] == "图表":
        return "visual_redraw_needed"
    if comment["action_type"] == "格式修正":
        return "format_fix_ready"
    if comment.get("requires_author_input"):
        return "needs_author_input"
    return "text_ready_with_caveat"


def _action_type(comment: dict) -> str:
    if comment["scope"] == "图表":
        return "redraw_figure" if "图" in comment["original_text"] else "fix_format"
    if comment["action_type"] == "补充实验":
        return "add_experiment_design"
    if comment["action_type"] == "补充引用":
        return "add_reference_checklist"
    if comment["action_type"] == "格式修正":
        return "fix_format"
    return "insert_after_paragraph"


def _new_text(comment: dict) -> str:
    text = comment["original_text"]
    if "量纲" in text or "归一化" in text:
        return (
            "为保证CEOP-MILP模型中不同成本项可以在同一目标函数中进行比较，本文对电价成本、碳排放成本、跨中心带宽传输成本以及SLA违约风险成本进行统一货币化或无量纲化处理。"
            "其中，电价、碳成本和带宽成本均按照单位任务在调度周期内产生的实际费用折算为货币成本；SLA风险项则先依据任务失败概率和违约惩罚系数计算期望违约损失，再与其他成本项共同进入目标函数。"
            "对于量纲差异较大的指标，本文在实验部分采用基于历史样本上下界的归一化方法进行尺度调整，并通过权重参数刻画不同成本目标的重要性。"
        )
    if "替代关系" in text or "经济学解释" in text:
        return (
            "在本文的经济-环境系统分析框架中，算力服务被视为数字经济条件下能够改变资本、劳动和能源配置效率的新型生产要素。"
            "算力投入一方面可以通过自动化计算、智能调度和数据处理能力提升，对部分重复性劳动和传统管理投入形成替代效应；另一方面，算力服务的供给依赖服务器、网络设备、数据中心基础设施以及稳定能源供给，因此又与资本投入和能源投入具有互补关系。"
            "基于上述特征，本文在CGE模型中采用有限替代关系刻画算力与传统要素之间的相互作用，而不是假定算力可以完全替代资本或劳动。"
        )
    if "双向耦合" in text or "反馈" in text:
        return (
            "本文所称“微观优化-宏观评估”双向耦合包括两个方向：一方面，CEOP-MILP模型输出的跨区域算力分配方案作为外部冲击输入宏观代理模型，用于评估不同算力布局对区域GDP、产业产出和碳排放的影响；"
            "另一方面，宏观评估得到的区域经济收益、碳排放约束和产业承载能力可反向作为微观优化模型的政策约束或权重调整依据。"
            "因此，微观模型不仅提供可执行的算力调度方案，宏观模型也为后续调度中的区域选择、绿色能源倾向和碳约束强度提供反馈信息，从而形成规划方案评估与再优化的闭环。"
        )
    if "图" in text or "表" in text:
        return (
            "建议在对应图表前补充引导句，明确该图表展示的对象、变量或流程含义；随后根据盲审意见规范图元、线条、判断条件、题注和正文引用顺序。"
            "若涉及流程图重绘，应保留原有模型逻辑，不新增论文中未说明的步骤，并请作者核对源图文件后完成正式替换。"
            "对于全文性图表问题，应逐一检查正文中“如图所示”“见表”等引出语是否位于图表之前，并将图表题注、正文引用和图表出现顺序调整为一致。"
        )
    if "参考文献" in text or "文献" in text:
        return "请作者逐条核查被点名参考文献的文献类型、作者、题名、期刊或会议名称、年份、卷期页码、DOI或预印本编号。对于已经正式发表的预印本文献，应优先替换为正式发表版本；对于缺少出处的条目，应补齐来源信息后再统一调整为学校要求的参考文献格式。"
    if "实验" in text or "场景" in text or "节点" in text:
        return "该意见涉及实验设计和真实数据支撑，不能由模型直接编造结果。建议作者补充节点选择依据、场景设置理由、可用数据范围和新增对比实验方案；在获得真实结果后，可在实验设置部分说明样本来源，在结果分析部分报告新增实验表格，并在结论中解释实验对模型有效性的支撑。"
    return "建议在对应章节补充一段针对该评审意见的解释性文字，明确现有论文表述不足、补充后的逻辑衔接以及与全文研究目标之间的关系。该补充应尽量放在原模型、实验或结论首次出现的位置之后，并在摘要、结论或创新点中保持前后一致。"


def _author_items(comment: dict) -> list[dict]:
    if not comment.get("requires_author_input"):
        return []
    return [
        {
            "item": "作者核实材料",
            "reason": "该意见涉及真实实验、图源文件、参考文献出处或作者决策，不能由模型编造。",
            "needed_material": "请提供真实数据、实验结果、图表源文件、参考文献正式出处或导师确认意见。",
        }
    ]


def _problem_diagnosis(comment: dict) -> str:
    text = comment["original_text"]
    if "替代关系" in text:
        return "评审专家关注的是CGE模型中算力作为生产要素的经济学含义。论文若只说明将算力纳入模型，而没有解释算力与资本、劳动、能源之间的替代和互补关系，会使模型设定显得缺少理论支撑。"
    if "量纲" in text or "归一化" in text:
        return "评审专家关注的是MILP目标函数中多类成本项是否可以直接相加。论文需要说明电价、碳成本、带宽成本和SLA风险如何统一尺度，否则目标函数的经济含义和权重解释会不充分。"
    if "双向耦合" in text or "反馈" in text:
        return "评审专家认为论文强调微观优化与宏观评估双向耦合，但当前表述可能更多体现从微观到宏观的单向输入，缺少宏观评估结果反向约束微观规划的机制说明。"
    if "节点数量" in text or "场景" in text or "实验" in text:
        return "评审专家关注实验设计对研究结论的支撑强度。该类问题通常不能只补一句解释，而需要补充样本选择依据、场景扩展设计、结果表模板或真实实验结果。"
    if "图" in text or "表" in text or "公式" in text:
        return "评审专家关注图表公式与正文叙述的规范性和可读性。该问题通常涉及正文引出语、图表位置、题注、图元规范和全文一致性，需要结合相关章节逐处处理。"
    if "参考文献" in text or "文献" in text:
        return "评审专家关注参考文献条目的完整性和格式一致性。该问题需要逐条核查真实出处，不能由模型编造期刊、会议、卷期页码或DOI。"
    return "评审意见指出论文当前表述存在不足，需要结合相关章节补充更具体的解释、操作或同步修改，而不是只给出泛泛修改方向。"


def _evidence_coverage(mapping: dict) -> list[dict]:
    items = []
    for loc in mapping.get("locations", [])[:4]:
        items.append(
            {
                "role": loc.get("role") or "supporting_context",
                "section_id": loc.get("section_id"),
                "section_title": loc.get("title"),
                "evidence": loc.get("reason", "该位置由确定性映射召回。"),
                "use": "作为正文修改或同步修改的依据。",
                "asset_id": None,
            }
        )
    for asset in mapping.get("assets", [])[:3]:
        items.append(
            {
                "role": asset.get("role", "core_asset"),
                "section_id": None,
                "section_title": None,
                "evidence": asset.get("reason", "该资产与意见匹配。"),
                "use": "作为图表或表格修改依据。",
                "asset_id": asset.get("asset_id"),
            }
        )
    return items


def _sync_updates(comment: dict, mapping: dict) -> list[dict]:
    text = comment["original_text"]
    updates = []
    if any(word in text for word in ["替代关系", "双向耦合", "量纲", "归一化"]):
        updates.append(
            {
                "target": {"section_id": None, "section_title": "结论或本章小结", "asset_id": None},
                "new_text": "建议在本章小结或结论中同步补充一句，说明上述模型设定、成本尺度处理或耦合机制如何增强本文方法的理论解释力和可复核性。",
                "reason": "避免正文新增解释与总结部分脱节。",
            }
        )
    if comment.get("scope") == "图表":
        updates.append(
            {
                "target": {"section_id": None, "section_title": "相关图表前后正文", "asset_id": (mapping.get("assets") or [{}])[0].get("asset_id")},
                "new_text": "建议在图表出现前增加引出语，明确该图表展示的对象、变量或流程，并在图表后补充一句解释其与模型或实验结论的关系。",
                "reason": "回应图表引出顺序和规范性问题。",
            }
        )
    return updates


def scaffold_revision_plans(review_comments_path: Path, comment_mappings_path: Path, output_dir: Path) -> list[dict]:
    comments = _read_json(review_comments_path)["comments"]
    mappings_by_id = {item["comment_id"]: item for item in _read_json(comment_mappings_path)["mappings"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    plans = []
    for comment in comments:
        mapping = mappings_by_id.get(comment["comment_id"], {"locations": [], "assets": [], "requires_author_input": comment.get("requires_author_input"), "confidence": 0.2})
        location = next((loc for loc in mapping.get("locations", []) if loc.get("role") == "core_revision_location"), mapping.get("locations", [{}])[0] if mapping.get("locations") else {})
        asset = mapping.get("assets", [{}])[0] if mapping.get("assets") else {}
        action_type = _action_type(comment)
        new_text = _new_text(comment)
        requires_author = bool(comment.get("requires_author_input") or action_type in {"add_experiment_design", "add_reference_checklist"})
        plan = {
            "comment_id": comment["comment_id"],
            "revision_status": _status(comment, mapping),
            "problem_diagnosis": _problem_diagnosis(comment),
            "evidence_coverage": _evidence_coverage(mapping),
            "overall_strategy": f"围绕评审意见“{comment['original_text']}”补充可执行修改方案，并标明需要作者确认的内容。",
            "actions": [
                {
                    "action_id": "A1",
                    "type": action_type,
                    "target": {
                        "section_id": location.get("section_id"),
                        "section_title": location.get("title"),
                        "page_range": location.get("page_range"),
                        "asset_id": asset.get("asset_id"),
                    },
                    "anchor_text": "请根据目标章节中首次出现相关概念、图表或实验设置的位置人工确认插入点。",
                    "original_text": "",
                    "new_text": new_text,
                    "rationale": "该修改用于回应盲审专家指出的问题，并避免泛泛说明。",
                    "requires_author_input": requires_author,
                    "visual_diagnosis": ["需核对图表引出顺序、题注、线条和图元规范性。"] if comment["scope"] == "图表" else [],
                    "redraw_spec": None,
                    "caption_suggestion": None,
                    "author_input_reason": "需要作者提供真实材料后才能写成已完成修改。" if requires_author else None,
                }
            ],
            "synchronized_updates": _sync_updates(comment, mapping),
            "reviewer_response": f"感谢专家意见。本文拟针对该问题在{location.get('title') or '相关章节'}中补充说明或调整，并对需要作者核实的内容进行逐项确认后再形成最终修改稿。",
            "author_input_needed": _author_items(comment),
            "risks": ["该文件为确定性 scaffold，需 revision-planner 或作者复核后作为最终修改文本。"],
            "confidence": min(0.86, max(0.45, mapping.get("confidence", 0.5))),
        }
        (output_dir / f"{comment['comment_id']}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        plans.append(plan)
    return plans


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold revision plans from comments and mappings.")
    parser.add_argument("--review-comments", required=True)
    parser.add_argument("--comment-mappings", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    scaffold_revision_plans(Path(args.review_comments), Path(args.comment_mappings), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
