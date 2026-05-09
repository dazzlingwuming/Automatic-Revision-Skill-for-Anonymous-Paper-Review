"""数据模型测试"""

from src.models import (
    ReviewComment, ReviewCategory, SeverityLevel,
    SuggestionStatus, PaperInfo, RevisionSuggestion,
    FormatIssue, RevisionReport, TaskConfig,
)


class TestModels:
    """数据模型测试"""

    def test_review_comment_creation(self):
        """测试评审意见创建"""
        comment = ReviewComment(
            id="意见1",
            category=ReviewCategory.WRITING,
            severity=SeverityLevel.REQUIRED,
            original_text="摘要不够简洁"
        )
        assert comment.id == "意见1"
        assert comment.category == ReviewCategory.WRITING
        assert comment.severity == SeverityLevel.REQUIRED

    def test_review_comment_optional_fields(self):
        """测试评审意见可选字段"""
        comment = ReviewComment(
            id="意见1",
            category=ReviewCategory.FORMAT,
            severity=SeverityLevel.SUGGESTED,
            original_text="格式问题",
            related_section="参考文献",
            page_ref=42,
        )
        assert comment.related_section == "参考文献"
        assert comment.page_ref == 42

    def test_paper_info_defaults(self):
        """测试论文信息默认值"""
        info = PaperInfo(file_path="test.pdf")
        assert info.title is None
        assert info.total_pages == 0
        assert info.sections == []

    def test_revision_suggestion_status_default(self):
        """测试修改建议默认状态"""
        suggestion = RevisionSuggestion(
            comment_id="意见1",
            suggestion="请修改摘要"
        )
        assert suggestion.status == SuggestionStatus.PENDING

    def test_format_issue_all_fields(self):
        """测试格式问题所有字段"""
        issue = FormatIssue(
            issue_type="缺少摘要",
            description="未找到摘要部分",
            location="论文开头",
            suggestion="添加200-300字摘要"
        )
        assert issue.issue_type == "缺少摘要"

    def test_revision_report_creation(self):
        """测试修改报告创建"""
        from datetime import datetime
        report = RevisionReport(
            paper_info=PaperInfo(title="测试论文"),
            review_source="盲审意见.pdf",
            comments=[],
            suggestions=[],
            format_issues=[],
            generated_at=datetime.now().isoformat(),
        )
        assert report.paper_info.title == "测试论文"
        assert len(report.comments) == 0

    def test_task_config_defaults(self):
        """测试任务配置默认值"""
        config = TaskConfig(
            paper_path="paper.pdf",
            review_path="review.pdf"
        )
        assert config.output_dir == "./output"
        assert config.use_ai is True
        assert config.format_only is False
