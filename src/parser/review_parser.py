"""盲审意见解析模块"""

import re
from src.models import ReviewComment, ReviewCategory, SeverityLevel


class ReviewParser:
    """盲审意见解析器：从文本中提取结构化的评审意见"""

    # 严重程度关键词
    SEVERITY_KEYWORDS = {
        SeverityLevel.REQUIRED: ["必须", "强烈建议", "务必", "一定要", "缺少", "错误", "不正确"],
        SeverityLevel.SUGGESTED: ["建议", "推荐", "最好", "应当", "应该", "可以改进"],
        SeverityLevel.OPTIONAL: ["可选", "可以考虑", "仅供参考", "可酌情"],
    }

    # 分类关键词
    CATEGORY_KEYWORDS = {
        ReviewCategory.INNOVATION: ["创新", "贡献", "新颖", "新意", "研究价值"],
        ReviewCategory.EXPERIMENT: ["实验", "数据", "方法", "模型", "样本", "验证", "对比"],
        ReviewCategory.WRITING: ["写作", "逻辑", "结构", "表达", "语言", "摘要", "结论", "论述"],
        ReviewCategory.FORMAT: ["格式", "排版", "图表", "参考文献", "字体", "行距", "编号", "引用"],
    }

    def parse(self, text: str) -> list[ReviewComment]:
        """从文本中解析出所有评审意见"""
        lines = text.strip().split("\n")
        comments = []
        current_id = 1

        comment_blocks = self._split_by_number(lines)

        for block in comment_blocks:
            if not block.strip():
                continue
            comment = self._parse_single_comment(block, current_id)
            if comment:
                comments.append(comment)
                current_id += 1

        return comments

    def _split_by_number(self, lines: list[str]) -> list[str]:
        """按编号分割评审意见（如 1.、2.、①、② 等）"""
        pattern = re.compile(r'^[\s]*[\d]+[\.、\)]\s*|^[\s]*[①②③④⑤⑥⑦⑧⑨⑩]')
        blocks = []
        current = []
        for line in lines:
            if pattern.match(line) and current:
                blocks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append("\n".join(current))
        return blocks

    def _parse_single_comment(self, text: str, idx: int) -> ReviewComment | None:
        """解析单条评审意见"""
        if len(text.strip()) < 5:
            return None

        category = self._classify(text)
        severity = self._judge_severity(text)

        return ReviewComment(
            id=f"意见{idx}",
            category=category,
            severity=severity,
            original_text=text.strip(),
        )

    def _classify(self, text: str) -> ReviewCategory:
        """对评审意见进行分类"""
        scores = {cat: 0 for cat in ReviewCategory}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    scores[category] += 1

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else ReviewCategory.OTHER

    def _judge_severity(self, text: str) -> SeverityLevel:
        """判断评审意见的严重程度"""
        for severity in [SeverityLevel.REQUIRED, SeverityLevel.SUGGESTED, SeverityLevel.OPTIONAL]:
            for kw in self.SEVERITY_KEYWORDS[severity]:
                if kw in text:
                    return severity
        return SeverityLevel.SUGGESTED
