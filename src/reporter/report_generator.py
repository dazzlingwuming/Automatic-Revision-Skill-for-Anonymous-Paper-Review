"""修改报告生成模块"""

from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from src.models import RevisionReport


class ReportGenerator:
    """修改报告生成器"""

    def __init__(self, template_dir: str | Path | None = None):
        if template_dir:
            self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        else:
            self.env = Environment(loader=FileSystemLoader(
                str(Path(__file__).parent / "templates")
            ))

    def generate_markdown(self, report: RevisionReport) -> str:
        """生成 Markdown 格式的修改报告"""
        now = report.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M')

        lines = [
            "# 盲审论文修改报告",
            "",
            f"**论文题目**: {report.paper_info.title or '未知'}",
            f"**生成时间**: {now}",
            "",
            "---",
            "",
            "## 一、盲审意见总览",
            "",
            f"共收到 **{len(report.comments)}** 条评审意见：",
            "",
        ]

        # 按分类统计
        categories = {}
        for c in report.comments:
            cat = c.category.value
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in categories.items():
            lines.append(f"- {cat}: {count} 条")

        lines.extend([
            "",
            "## 二、逐条修改建议",
            "",
        ])

        for comment, suggestion in zip(report.comments, report.suggestions):
            lines.extend([
                f"### {comment.id}",
                "",
                f"**评审意见**: {comment.original_text}",
                "",
                f"**分类**: {comment.category.value} | "
                f"**严重程度**: {comment.severity.value}",
                "",
                "**修改建议**:",
                "",
                suggestion.suggestion,
                "",
                "---",
                "",
            ])

        if report.format_issues:
            lines.extend([
                "## 三、格式问题清单",
                "",
                "| 问题类型 | 描述 | 位置 | 修改建议 |",
                "|---------|------|------|---------|",
            ])
            for issue in report.format_issues:
                lines.append(
                    f"| {issue.issue_type} | {issue.description} | "
                    f"{issue.location} | {issue.suggestion} |"
                )
            lines.append("")

        if report.summary:
            lines.extend([
                "## 四、修改总结",
                "",
                report.summary,
            ])

        return "\n".join(lines)

    def generate_html(self, report: RevisionReport) -> str:
        """生成 HTML 格式的修改报告"""
        template = self.env.get_template("report.html")
        return template.render(
            report=report,
            generated_at=report.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M'),
            zip=zip,
        )

    def save_markdown(self, report: RevisionReport, output_path: str | Path):
        """保存 Markdown 报告"""
        content = self.generate_markdown(report)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    def save_html(self, report: RevisionReport, output_path: str | Path):
        """保存 HTML 报告"""
        content = self.generate_html(report)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
