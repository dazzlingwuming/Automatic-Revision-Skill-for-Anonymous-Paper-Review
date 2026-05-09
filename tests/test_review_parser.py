"""盲审意见解析器测试"""

import pytest
from src.parser.review_parser import ReviewParser
from src.models import ReviewCategory, SeverityLevel


class TestReviewParser:
    """ReviewParser 测试"""

    def setup_method(self):
        self.parser = ReviewParser()

    def test_parse_multiple_comments(self):
        """测试解析多条评审意见"""
        text = """1. 论文创新点不足，缺乏理论贡献。
2. 实验样本量过小，需要增加对比实验。
3. 参考文献格式不规范。"""
        comments = self.parser.parse(text)
        assert len(comments) == 3
        assert comments[0].category == ReviewCategory.INNOVATION

    def test_parse_empty_text(self):
        """测试空文本"""
        comments = self.parser.parse("")
        assert len(comments) == 0

    def test_category_innovation(self):
        """测试创新性分类"""
        text = "1. 论文创新点不足，需要突出研究贡献。"
        comments = self.parser.parse(text)
        assert comments[0].category == ReviewCategory.INNOVATION

    def test_category_experiment(self):
        """测试实验设计分类"""
        text = "1. 实验数据不充分，需要补充更多样本。"
        comments = self.parser.parse(text)
        assert comments[0].category == ReviewCategory.EXPERIMENT

    def test_category_writing(self):
        """测试写作规范分类"""
        text = "1. 论文摘要不够简洁，逻辑结构需要调整。"
        comments = self.parser.parse(text)
        assert comments[0].category == ReviewCategory.WRITING

    def test_category_format(self):
        """测试格式规范分类"""
        text = "1. 参考文献格式不规范，图表编号有误。"
        comments = self.parser.parse(text)
        assert comments[0].category == ReviewCategory.FORMAT

    def test_severity_required(self):
        """测试必须修改"""
        text = "1. 必须修改摘要部分，当前表述不准确。"
        comments = self.parser.parse(text)
        assert comments[0].severity == SeverityLevel.REQUIRED

    def test_severity_suggested(self):
        """测试建议修改"""
        text = "1. 建议调整章节顺序，使逻辑更清晰。"
        comments = self.parser.parse(text)
        assert comments[0].severity == SeverityLevel.SUGGESTED

    def test_severity_optional(self):
        """测试可改可不改"""
        text = "1. 可以考虑增加一些文献对比。"
        comments = self.parser.parse(text)
        assert comments[0].severity == SeverityLevel.OPTIONAL

    def test_single_comment_too_short(self):
        """测试过短的文本不生成意见"""
        comments = self.parser.parse("1. 好")
        assert len(comments) == 0

    def test_parse_chinese_numbered(self):
        """测试中文编号格式"""
        text = """① 论文创新性有待加强。
② 实验部分缺少对比实验。"""
        comments = self.parser.parse(text)
        assert len(comments) == 2

    def test_parse_no_number(self):
        """测试无编号的段落也能解析为一条意见"""
        text = "论文整体创新性不足，需要进一步突出研究贡献。"
        comments = self.parser.parse(text)
        assert len(comments) == 1
        assert comments[0].category == ReviewCategory.INNOVATION
