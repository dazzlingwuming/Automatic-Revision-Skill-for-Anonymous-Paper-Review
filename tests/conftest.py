"""测试配置和夹具"""

import pytest
from pathlib import Path


@pytest.fixture
def pdf_sample(tmp_path) -> str:
    """创建一个简单的测试用 PDF 文件"""
    import fitz
    pdf_path = tmp_path / "test_paper.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "摘要：本文研究了机器学习方法在自然语言处理中的应用。")
    page.insert_text((50, 100), "关键词：机器学习；深度学习；自然语言处理")
    page.insert_text((50, 150), "第一章 绪论")
    page.insert_text((50, 200), "参考文献\n[1] 测试文献")
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path)


@pytest.fixture
def review_pdf(tmp_path) -> str:
    """创建一个测试用盲审意见 PDF"""
    import fitz
    pdf_path = tmp_path / "test_review.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "盲审意见")
    page.insert_text((50, 100), "1. 论文创新点不足")
    page.insert_text((50, 150), "2. 实验数据不充分")
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path)
