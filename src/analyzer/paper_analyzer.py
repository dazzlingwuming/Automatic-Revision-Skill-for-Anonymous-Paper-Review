"""论文-评审意见映射分析模块"""

import re
from src.models import ReviewComment, PaperInfo


class PaperAnalyzer:
    """将评审意见映射到论文的具体章节"""

    # 常见章节标题模式
    SECTION_PATTERNS = [
        r'第[一二三四五六七八九十]+章\s+.*',
        r'[\d]+\.[\d]+\s+.*',
        r'摘\s*要',
        'Abstract',
        r'参考[文\s]献',
        'References',
        '致谢',
        '附录',
    ]

    def __init__(self):
        self.section_pattern = re.compile(
            '(' + '|'.join(self.SECTION_PATTERNS) + ')'
        )

    def analyze(self, comment: ReviewComment, paper_text: str) -> ReviewComment:
        """分析评审意见，映射到论文章节"""
        # 尝试在论文中找到与意见相关的章节
        comment_keywords = self._extract_keywords(comment.original_text)
        related_section = self._find_related_section(
            comment_keywords, paper_text
        )

        if related_section:
            comment.related_section = related_section

        return comment

    def analyze_all(
        self, comments: list[ReviewComment], paper_text: str
    ) -> list[ReviewComment]:
        """批量分析所有评审意见"""
        return [self.analyze(c, paper_text) for c in comments]

    def extract_sections(self, paper_text: str) -> list[str]:
        """提取论文的所有章节标题"""
        sections = []
        for line in paper_text.split('\n'):
            line = line.strip()
            if self.section_pattern.match(line):
                sections.append(line)
        return sections

    def _extract_keywords(self, text: str) -> list[str]:
        """从评审意见中提取关键词"""
        # 去除常见停用词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                     '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
                     '没有', '看', '好', '自己', '这', '他', '她', '它', '们'}
        words = re.findall(r'[一-鿿]{2,}', text)
        return [w for w in words if w not in stopwords]

    def _find_related_section(self, keywords: list[str], paper_text: str) -> str | None:
        """查找与关键词最相关的章节"""
        sections = self.extract_sections(paper_text)
        if not sections:
            return None

        best_section = None
        best_score = 0

        for section in sections:
            score = sum(1 for kw in keywords if kw in section)
            if score > best_score:
                best_score = score
                best_section = section

        return best_section
