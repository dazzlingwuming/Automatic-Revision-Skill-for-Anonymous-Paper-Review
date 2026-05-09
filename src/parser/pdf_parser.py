"""PDF 论文解析模块"""

import fitz
from pathlib import Path


class PDFParser:
    """PDF 文件解析器，提取文本内容和元信息"""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {file_path}")
        self._doc: fitz.Document | None = None

    def open(self):
        """打开 PDF 文件"""
        self._doc = fitz.open(self.file_path)
        return self

    def close(self):
        """关闭 PDF 文件"""
        if self._doc:
            self._doc.close()
            self._doc = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *args):
        self.close()

    def extract_text(self) -> str:
        """提取全部文本"""
        if not self._doc:
            self.open()
        return "\n".join(page.get_text() for page in self._doc)

    def extract_text_from_page(self, page_num: int) -> str:
        """提取指定页面的文本"""
        if not self._doc:
            self.open()
        return self._doc[page_num].get_text()

    def get_page_count(self) -> int:
        """获取总页数"""
        if not self._doc:
            self.open()
        return len(self._doc)

    def get_toc(self) -> list[tuple[int, str, int]]:
        """获取目录（如果有）"""
        if not self._doc:
            self.open()
        return self._doc.get_toc()

    def get_metadata(self) -> dict:
        """获取元数据"""
        if not self._doc:
            self.open()
        return self._doc.metadata or {}

    def annotate_pdf(self, output_path: str | Path, annotations: list[dict]):
        """在 PDF 上添加标注（高亮、注释）"""
        if not self._doc:
            self.open()

        for ann in annotations:
            page_num = ann.get("page", 0)
            if page_num >= len(self._doc):
                continue
            page = self._doc[page_num]
            rect = ann.get("rect")
            if rect:
                highlight = page.add_highlight_annot(rect)
                if ann.get("note"):
                    highlight.set_info({"content": ann["note"]})
                highlight.update()

        self._doc.save(output_path)
