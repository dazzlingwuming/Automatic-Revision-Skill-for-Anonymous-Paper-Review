"""修改建议生成引擎"""

from src.models import ReviewComment, RevisionSuggestion, PaperInfo
from src.suggestor.ai_client import AIClient, AIMessage


class SuggestionEngine:
    """修改建议生成引擎"""

    SYSTEM_PROMPT = """你是一位资深的学术论文评审和修改专家。你的任务是帮助研究生修改盲审论文。

给定以下信息：
1. 盲审评审意见
2. 论文原文内容（相关部分）

请针对每条评审意见，生成具体的修改建议。修改建议应包括：
1. **修改方案**：具体如何修改的详细说明
2. **修改示例**：修改后的文本示例
3. **修改等级**：必须修改 / 建议修改 / 可改可不改

要求：
- 修改方案要具体、可操作，不能泛泛而谈
- 修改示例要展示修改前后的对比
- 尊重原论文的学术风格和表达习惯
- 对于格式问题，给出明确的格式规范说明"""

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    def generate_suggestion(
        self,
        comment: ReviewComment,
        paper_info: PaperInfo,
        paper_context: str = "",
    ) -> RevisionSuggestion:
        """针对单条评审意见生成修改建议"""
        prompt = self._build_prompt(comment, paper_info, paper_context)
        messages = [
            AIMessage(role="system", content=self.SYSTEM_PROMPT),
            AIMessage(role="user", content=prompt),
        ]

        response = self.ai_client.chat(messages, max_tokens=2048)

        return RevisionSuggestion(
            comment_id=comment.id,
            suggestion=response,
        )

    def generate_all(
        self,
        comments: list[ReviewComment],
        paper_info: PaperInfo,
        paper_context: str = "",
    ) -> list[RevisionSuggestion]:
        """批量生成所有修改建议"""
        results = []
        for comment in comments:
            suggestion = self.generate_suggestion(
                comment, paper_info, paper_context
            )
            results.append(suggestion)
        return results

    def _build_prompt(
        self,
        comment: ReviewComment,
        paper_info: PaperInfo,
        paper_context: str,
    ) -> str:
        """构建提示词"""
        prompt_parts = [
            f"## 评审意见\n编号：{comment.id}",
            f"分类：{comment.category.value}",
            f"严重程度：{comment.severity.value}",
            f"原文：{comment.original_text}",
        ]

        if paper_context:
            prompt_parts.append(
                f"\n## 论文相关上下文\n{paper_context[:2000]}"
            )

        prompt_parts.append(
            "\n请生成具体的修改建议，包括修改方案和修改示例。"
        )

        return "\n".join(prompt_parts)
