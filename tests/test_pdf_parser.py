"""PDF 解析器测试"""

import pytest
from pathlib import Path
from src.parser.pdf_parser import PDFParser


class TestPDFParser:
    """PDFParser 测试类"""

    def test_file_not_found(self):
        """测试文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            PDFParser("nonexistent.pdf")

    def test_open_and_close(self, pdf_sample):
        """测试打开和关闭 PDF"""
        parser = PDFParser(pdf_sample)
        parser.open()
        assert parser.get_page_count() > 0
        parser.close()
        assert parser._doc is None

    def test_context_manager(self, pdf_sample):
        """测试上下文管理器"""
        with PDFParser(pdf_sample) as parser:
            assert parser.get_page_count() > 0

    def test_extract_text(self, pdf_sample):
        """测试文本提取"""
        with PDFParser(pdf_sample) as parser:
            text = parser.extract_text()
            assert isinstance(text, str)
            assert len(text) > 0

    def test_extract_text_from_page(self, pdf_sample):
        """测试单页文本提取"""
        with PDFParser(pdf_sample) as parser:
            text = parser.extract_text_from_page(0)
            assert len(text) > 0

    def test_get_page_count(self, pdf_sample):
        """测试获取页数"""
        with PDFParser(pdf_sample) as parser:
            assert parser.get_page_count() >= 1

    def test_get_metadata(self, pdf_sample):
        """测试获取元数据"""
        with PDFParser(pdf_sample) as parser:
            metadata = parser.get_metadata()
            assert isinstance(metadata, dict)
