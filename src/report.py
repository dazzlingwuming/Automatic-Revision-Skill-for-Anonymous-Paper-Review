"""Report assembly helpers used by deterministic tooling."""

from __future__ import annotations


def status_label(revision_status: str) -> str:
    return {
        "can_revise": "拟修改",
        "needs_author_input": "需要作者补充",
        "explain_only": "建议解释回应",
        "not_applicable": "不适用",
        "uncertain": "不确定",
    }.get(revision_status, revision_status)

