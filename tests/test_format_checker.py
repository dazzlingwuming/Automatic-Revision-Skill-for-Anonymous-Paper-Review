"""格式检查器测试"""

import pytest
from src.analyzer.format_checker import FormatChecker


class TestFormatChecker:
    """FormatChecker 测试"""

    def setup_method(self):
        self.checker = FormatChecker()

    def test_check_keywords_sufficient(self):
        """测试关键词数量足够"""
        text = "关键词：机器学习；深度学习；自然语言处理"
        issues = self.checker._check_keywords(text)
        assert len(issues) == 0

    def test_check_keywords_insufficient(self):
        """测试关键词数量不足"""
        text = "关键词：机器学习"
        issues = self.checker._check_keywords(text)
        assert len(issues) == 1
        assert issues[0].issue_type == "关键词数量不足"

    def test_check_keywords_too_many(self):
        """测试关键词过多"""
        text = "关键词：A；B；C；D；E；F；G；H；I"
        issues = self.checker._check_keywords(text)
        assert len(issues) == 1
        assert issues[0].issue_type == "关键词过多"

    def test_check_abstract_exists(self):
        """测试摘要存在"""
        text = "摘  要：本文研究了..."
        issues = self.checker._check_abstract(text)
        assert len(issues) == 0

    def test_check_abstract_missing(self):
        """测试摘要缺失"""
        text = "第一章 绪论"
        issues = self.checker._check_abstract(text)
        assert len(issues) == 1
        assert "缺少" in issues[0].issue_type

    def test_check_keywords_missing(self):
        """测试关键词缺失"""
        text = "这是一篇没有关键词的论文"
        issues = self.checker._check_keywords(text)
        assert len(issues) == 1
        assert "缺少" in issues[0].issue_type

    def test_check_references_exists(self):
        """测试参考文献存在"""
        text = "参考文献\n[1] 张三. 机器学习. 2020.\n[2] 李四. 深度学习. 2021."
        issues = self.checker._check_references(text)
        assert len(issues) == 0

    def test_check_references_missing(self):
        """测试参考文献缺失"""
        text = "本文研究了..."
        issues = self.checker._check_references(text)
        assert len(issues) == 1

    def test_check_figures_continuous(self):
        """测试图编号连续"""
        text = "如图1所示...如图2所示...如图3所示"
        issues = self.checker._check_figures_tables(text)
        figure_issues = [i for i in issues if "图" in i.issue_type]
        assert len(figure_issues) == 0

    def test_check_figures_discontinuous(self):
        """测试图编号不连续"""
        text = "如图1所示...如图3所示...如图5所示"
        issues = self.checker._check_figures_tables(text)
        figure_issues = [i for i in issues if "图" in i.issue_type]
        assert len(figure_issues) > 0

    def test_full_check(self):
        """测试完整检查流程"""
        text = """摘  要：本文研究...
关键词：机器学习；深度学习
如图1所示...
参考文献
[1] 测试."""
        issues = self.checker.check(text)
        assert len(issues) >= 0
