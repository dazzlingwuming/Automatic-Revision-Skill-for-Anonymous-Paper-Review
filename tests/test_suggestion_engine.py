"""修改建议引擎测试"""

import pytest
from src.models import ReviewComment, ReviewCategory, SeverityLevel, PaperInfo
from src.suggestor.ai_client import AIClient, AIMessage
from src.suggestor.suggestion_engine import SuggestionEngine


class MockAIClient(AIClient):
    """模拟 AI 客户端，用于测试"""

    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        return (
            "【修改方案】\n"
            "1. 精简摘要内容，突出研究目的和主要发现\n"
            "2. 删除冗余表述\n\n"
            "【修改示例】\n"
            "修改前：...\n"
            "修改后：..."
        )

    def count_tokens(self, text: str) -> int:
        return len(text) // 2


class TestSuggestionEngine:
    """SuggestionEngine 测试"""

    def setup_method(self):
        self.engine = SuggestionEngine(MockAIClient())

    def test_generate_suggestion(self):
        """测试单条建议生成"""
        comment = ReviewComment(
            id="意见1",
            category=ReviewCategory.WRITING,
            severity=SeverityLevel.REQUIRED,
            original_text="论文摘要不够简洁，需要精简。"
        )
        paper_info = PaperInfo(title="测试论文")
        result = self.engine.generate_suggestion(comment, paper_info)
        assert result.comment_id == "意见1"
        assert len(result.suggestion) > 0
        assert "修改方案" in result.suggestion

    def test_generate_suggestion_with_context(self):
        """测试带上下文的建议生成"""
        comment = ReviewComment(
            id="意见1",
            category=ReviewCategory.WRITING,
            severity=SeverityLevel.REQUIRED,
            original_text="摘要不够简洁。"
        )
        paper_info = PaperInfo(title="测试论文")
        context = "本文研究了基于深度学习的方法..."
        result = self.engine.generate_suggestion(
            comment, paper_info, paper_context=context
        )
        assert result.comment_id == "意见1"

    def test_generate_all(self):
        """测试批量生成"""
        comments = [
            ReviewComment(
                id="意见1", category=ReviewCategory.WRITING,
                severity=SeverityLevel.REQUIRED, original_text="意见1"
            ),
            ReviewComment(
                id="意见2", category=ReviewCategory.FORMAT,
                severity=SeverityLevel.SUGGESTED, original_text="意见2"
            ),
        ]
        paper_info = PaperInfo(title="测试论文")
        results = self.engine.generate_all(comments, paper_info)
        assert len(results) == 2
        assert results[0].comment_id == "意见1"
        assert results[1].comment_id == "意见2"

    def test_engine_with_empty_comments(self):
        """测试空意见列表"""
        paper_info = PaperInfo(title="测试论文")
        results = self.engine.generate_all([], paper_info)
        assert len(results) == 0
