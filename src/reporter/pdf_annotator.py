"""PDF 标注模块"""

from pathlib import Path
from src.parser.pdf_parser import PDFParser


class PDFAnnotator:
    """PDF 标注器：在 PDF 上标注修改位置"""

    def annotate(
        self,
        input_pdf: str | Path,
        output_pdf: str | Path,
        annotations: list[dict],
    ):
        """在 PDF 上添加标注"""
        with PDFParser(input_pdf) as parser:
            parser.annotate_pdf(output_pdf, annotations)
