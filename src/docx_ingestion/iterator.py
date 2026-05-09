"""Iterate DOCX body elements in their original Word order."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from docx.document import Document as DocumentObject
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


@dataclass(frozen=True)
class DocxBodyItem:
    body_index: int
    xml_tag: str
    element: Paragraph | Table


def iter_docx_blocks(document: DocumentObject) -> Iterator[DocxBodyItem]:
    """Yield paragraphs and tables in the order stored in word/document.xml."""
    for index, child in enumerate(document.element.body.iterchildren(), start=1):
        if isinstance(child, CT_P):
            yield DocxBodyItem(index, "w:p", Paragraph(child, document))
        elif isinstance(child, CT_Tbl):
            yield DocxBodyItem(index, "w:tbl", Table(child, document))
