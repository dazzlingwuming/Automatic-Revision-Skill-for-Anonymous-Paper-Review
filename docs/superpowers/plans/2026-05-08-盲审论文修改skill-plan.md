# 盲审论文修改 Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个完整的盲审论文修改 Claude Code Skill 及其配套 Python 工具

**Architecture:** 模块化管道架构——解析层 → 分析层 → 建议层 → 输出层，各层通过定义好的数据类通信。Skill 定义 Claude 的行为规范，Python 代码提供自动化工具支撑。

**Tech Stack:** Python 3.13, PyMuPDF, python-docx, Jinja2, pytest, argparse

---

### Task 1: 项目基础配置

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\requirements.txt`
- Create: `D:\APP_self\盲审论文修改skill\src\__init__.py`
- Modify: `D:\APP_self\盲审论文修改skill\CLAUDE.md`

- [ ] **Step 1: 创建 requirements.txt**

```txt
PyMuPDF>=1.25.0
python-docx>=1.1.0
Jinja2>=3.1.0
pytest>=8.0.0
pytest-cov>=5.0.0
```

- [ ] **Step 2: 创建 src/__init__.py**

```python
# 盲审论文修改工具包
```

- [ ] **Step 3: 更新 CLAUDE.md 完善项目结构说明**

---

### Task 2: 数据模型定义

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\models.py`
- Create: `D:\APP_self\盲审论文修改skill\tests\__init__.py`

- [ ] **Step 1: 创建 models.py 定义核心数据类**

```python
"""盲审论文修改的数据模型定义"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ReviewCategory(str, Enum):
    """评审意见分类"""
    INNOVATION = "创新性"          # 创新点、研究贡献
    EXPERIMENT = "实验设计"        # 实验方案、数据、方法
    WRITING = "写作规范"           # 论文结构、逻辑、表达
    FORMAT = "格式规范"            # 排版、引用、图表
    OTHER = "其他"                 # 其他


class SeverityLevel(str, Enum):
    """修改严重程度"""
    REQUIRED = "必须修改"
    SUGGESTED = "建议修改"
    OPTIONAL = "可改可不改"


class SuggestionStatus(str, Enum):
    """修改状态"""
    PENDING = "待修改"
    COMPLETED = "已修改"
    EXPLAINED = "已解释说明"


@dataclass
class ReviewComment:
    """单条评审意见"""
    id: str                               # 意见编号，如 "意见1"
    category: ReviewCategory              # 分类
    severity: SeverityLevel               # 严重程度
    original_text: str                    # 原始意见文本
    related_section: Optional[str] = None # 关联的论文章节
    page_ref: Optional[int] = None        # 关联的页码


@dataclass
class PaperInfo:
    """论文基本信息"""
    title: Optional[str] = None
    file_path: str = ""
    total_pages: int = 0
    sections: list[str] = field(default_factory=list)


@dataclass
class RevisionSuggestion:
    """单条修改建议"""
    comment_id: str                       # 对应的意见ID
    suggestion: str                       # 修改建议
    example_text: Optional[str] = None    # 修改示例
    status: SuggestionStatus = SuggestionStatus.PENDING


@dataclass
class FormatIssue:
    """格式问题"""
    issue_type: str                       # 问题类型
    description: str                      # 问题描述
    location: str                         # 位置
    suggestion: str                       # 修改建议


@dataclass
class RevisionReport:
    """完整的修改报告"""
    paper_info: PaperInfo
    review_source: str                    # 盲审意见来源
    comments: list[ReviewComment]         # 所有评审意见
    suggestions: list[RevisionSuggestion] # 所有修改建议
    format_issues: list[FormatIssue]      # 格式问题
    summary: str = ""                     # 修改总结
    generated_at: str = ""                # 生成时间


@dataclass
class TaskConfig:
    """任务配置"""
    paper_path: str
    review_path: str
    output_dir: str = "./output"
    ai_api_type: str = "claude"           # claude / openai
    ai_api_key: Optional[str] = None
    ai_model: str = "claude-sonnet-4-20250514"
```

- [ ] **Step 2: 创建 tests/__init__.py**

```python
# 测试包
```

---

### Task 3: PDF 解析模块

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\parser\__init__.py`
- Create: `D:\APP_self\盲审论文修改skill\src\parser\pdf_parser.py`
- Create: `D:\APP_self\盲审论文修改skill\tests\test_pdf_parser.py`

- [ ] **Step 1: 创建 parser/__init__.py**

```python
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .review_parser import ReviewParser

__all__ = ["PDFParser", "DocxParser", "ReviewParser"]
```

- [ ] **Step 2: 实现 PDF 解析器**

```python
"""PDF 论文解析模块"""

import fitz  # PyMuPDF
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
        import copy
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
```

- [ ] **Step 3: 编写 PDF 解析器测试**

```python
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
```

---

### Task 4: Word 解析模块和盲审意见解析器

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\parser\docx_parser.py`
- Create: `D:\APP_self\盲审论文修改skill\src\parser\review_parser.py`
- Create: `D:\APP_self\盲审论文修改skill\tests\test_review_parser.py`

- [ ] **Step 1: 实现 Word 解析器**

```python
"""Word 文档解析模块"""

from pathlib import Path


class DocxParser:
    """Word 文档解析器"""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Word 文件不存在: {file_path}")

    def extract_text(self) -> str:
        """提取全部文本"""
        from docx import Document
        doc = Document(self.file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    def get_paragraphs(self) -> list[dict]:
        """获取段落列表（含样式信息）"""
        from docx import Document
        doc = Document(self.file_path)
        return [
            {"text": p.text, "style": p.style.name if p.style else None}
            for p in doc.paragraphs if p.text.strip()
        ]

    def get_toc(self) -> list[str]:
        """提取目录（通过标题样式识别）"""
        from docx import Document
        doc = Document(self.file_path)
        toc = []
        for p in doc.paragraphs:
            if p.style and p.style.name.startswith("Heading"):
                level = p.style.name.replace("Heading ", "")
                indent = "  " * (int(level) - 1) if level.isdigit() else ""
                toc.append(f"{indent}{p.text}")
        return toc
```

- [ ] **Step 2: 实现盲审意见解析器**

```python
"""盲审意见解析模块"""

import re
from src.models import ReviewComment, ReviewCategory, SeverityLevel


class ReviewParser:
    """盲审意见解析器：从文本中提取结构化的评审意见"""

    # 评审意见条目匹配模式
    PATTERN_COMMENT = re.compile(
        r"(?:意见|评审意见|问题|建议)[\s]*[：:]\s*(.*?)(?=(?:意见|评审意见|问题|建议)[\s]*[：:]|$)",
        re.DOTALL
    )

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

        # 尝试按编号模式分割
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
        text_lower = text.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    scores[category] += 1

        # 返回得分最高的类别
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else ReviewCategory.OTHER

    def _judge_severity(self, text: str) -> SeverityLevel:
        """判断评审意见的严重程度"""
        for severity in [SeverityLevel.REQUIRED, SeverityLevel.SUGGESTED, SeverityLevel.OPTIONAL]:
            for kw in self.SEVERITY_KEYWORDS[severity]:
                if kw in text:
                    return severity
        return SeverityLevel.SUGGESTED
```

- [ ] **Step 3: 编写盲审意见解析器测试**

```python
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

    def test_category_classification(self):
        """测试分类准确性"""
        text = "1. 实验数据不充分，需要补充更多样本。"
        comments = self.parser.parse(text)
        assert comments[0].category == ReviewCategory.EXPERIMENT

    def test_severity_judgment(self):
        """测试严重程度判断"""
        text = "1. 务必修改摘要部分，当前表述不准确。"
        comments = self.parser.parse(text)
        assert comments[0].severity == SeverityLevel.REQUIRED

    def test_single_comment_too_short(self):
        """测试过短的文本不生成意见"""
        comments = self.parser.parse("1. 好")
        assert len(comments) == 0
```

---

### Task 5: 格式检查模块

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\analyzer\__init__.py`
- Create: `D:\APP_self\盲审论文修改skill\src\analyzer\format_checker.py`
- Create: `D:\APP_self\盲审论文修改skill\tests\test_format_checker.py`

- [ ] **Step 1: 实现格式检查器**

```python
"""论文格式规范性检查模块"""

import re
from src.models import FormatIssue


class FormatChecker:
    """论文格式检查器"""

    # 常见格式规范
    RULES = {
        "摘要字数": r"摘\s*要.{0,500}",
        "关键词数量": r"关键词.{0,200}",
        "参考文献格式": r"\[?\d+\]?",
        "图表编号": r"(图|表)\s*\d+",
        "章节编号": r"^第[一二三四五六七八九十]+章",
    }

    def check(self, text: str) -> list[FormatIssue]:
        """执行所有格式检查"""
        issues = []

        # 检查摘要
        issues.extend(self._check_abstract(text))
        # 检查关键词
        issues.extend(self._check_keywords(text))
        # 检查参考文献
        issues.extend(self._check_references(text))
        # 检查图表
        issues.extend(self._check_figures_tables(text))

        return issues

    def _check_abstract(self, text: str) -> list[FormatIssue]:
        """检查摘要格式"""
        issues = []
        match = re.search(r'摘\s*要', text)
        if not match:
            issues.append(FormatIssue(
                issue_type="缺少摘要",
                description="论文未找到'摘要'部分",
                location="论文开头",
                suggestion="请添加中文摘要，通常为200-300字"
            ))
        return issues

    def _check_keywords(self, text: str) -> list[FormatIssue]:
        """检查关键词"""
        issues = []
        match = re.search(r'关键词[\s：:](.*)', text)
        if match:
            kw_text = match.group(1)
            keywords = [k.strip() for k in re.split(r'[；;，,]', kw_text) if k.strip()]
            if len(keywords) < 3:
                issues.append(FormatIssue(
                    issue_type="关键词数量不足",
                    description=f"当前关键词数量: {len(keywords)}，建议3-5个",
                    location="关键词部分",
                    suggestion="增加关键词至3-5个"
                ))
            elif len(keywords) > 8:
                issues.append(FormatIssue(
                    issue_type="关键词过多",
                    description=f"当前关键词数量: {len(keywords)}，建议不超过8个",
                    location="关键词部分",
                    suggestion="减少关键词数量至8个以内"
                ))
        else:
            issues.append(FormatIssue(
                issue_type="缺少关键词",
                description="论文未找到'关键词'部分",
                location="摘要之后",
                suggestion="请在摘要后添加3-5个关键词"
            ))
        return issues

    def _check_references(self, text: str) -> list[FormatIssue]:
        """检查参考文献格式"""
        issues = []
        ref_section = re.search(r'参考[文\s]献(.*?)(?:\n\s*\n\s*\n|$)', text, re.DOTALL)
        if not ref_section:
            issues.append(FormatIssue(
                issue_type="缺少参考文献",
                description="未找到参考文献部分",
                location="论文末尾",
                suggestion="请添加参考文献部分"
            ))
        return issues

    def _check_figures_tables(self, text: str) -> list[FormatIssue]:
        """检查图表编号"""
        issues = []
        figures = re.findall(r'图\s*\d+', text)
        tables = re.findall(r'表\s*\d+', text)

        if figures:
            # 检查编号是否连续
            nums = [int(re.search(r'\d+', f).group()) for f in figures]
            expected = list(range(1, len(set(nums)) + 1))
            if sorted(set(nums)) != expected:
                issues.append(FormatIssue(
                    issue_type="图编号不连续",
                    description="图的编号存在跳号或重复",
                    location="全文",
                    suggestion="请检查图的编号是否连续"
                ))

        if tables:
            nums = [int(re.search(r'\d+', t).group()) for t in tables]
            expected = list(range(1, len(set(nums)) + 1))
            if sorted(set(nums)) != expected:
                issues.append(FormatIssue(
                    issue_type="表编号不连续",
                    description="表的编号存在跳号或重复",
                    location="全文",
                    suggestion="请检查表的编号是否连续"
                ))
        return issues
```

- [ ] **Step 2: 编写格式检查器测试**

```python
"""格式检查器测试"""

import pytest
from src.analyzer.format_checker import FormatChecker


class TestFormatChecker:
    """FormatChecker 测试"""

    def setup_method(self):
        self.checker = FormatChecker()

    def test_check_keywords_sufficient(self):
        text = "关键词：机器学习；深度学习；自然语言处理"
        issues = self.checker._check_keywords(text)
        assert len(issues) == 0

    def test_check_keywords_insufficient(self):
        text = "关键词：机器学习"
        issues = self.checker._check_keywords(text)
        assert len(issues) == 1
        assert "不足" in issues[0].description

    def test_check_abstract_exists(self):
        text = "摘  要：本文研究了..."
        issues = self.checker._check_abstract(text)
        assert len(issues) == 0

    def test_check_abstract_missing(self):
        text = "第一章 绪论"
        issues = self.checker._check_abstract(text)
        assert len(issues) == 1
```

---

### Task 6: AI 客户端和修改建议引擎

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\suggestor\__init__.py`
- Create: `D:\APP_self\盲审论文修改skill\src\suggestor\ai_client.py`
- Create: `D:\APP_self\盲审论文修改skill\src\suggestor\suggestion_engine.py`
- Create: `D:\APP_self\盲审论文修改skill\tests\test_suggestion_engine.py`

- [ ] **Step 1: 实现 AI 客户端抽象接口**

```python
"""AI API 客户端抽象接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIMessage:
    role: str  # "user" | "assistant" | "system"
    content: str


class AIClient(ABC):
    """AI 客户端抽象基类"""

    @abstractmethod
    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        """发送对话请求，返回响应文本"""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """估算 token 数量"""
        ...


class ClaudeClient(AIClient):
    """Claude API 客户端"""

    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        """调用 Claude API"""
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)

        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg += msg.content + "\n"
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        response = client.messages.create(
            model=self.model,
            system=system_msg.strip() or None,
            messages=chat_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.content[0].text

    def count_tokens(self, text: str) -> int:
        """估算 token 数量（粗略估计）"""
        return len(text) // 2


class OpenAIClient(AIClient):
    """OpenAI 兼容接口客户端"""

    def __init__(self, api_key: str = "", model: str = "gpt-4o", base_url: str = ""):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        """调用 OpenAI 兼容 API"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url or None)

        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.choices[0].message.content

    def count_tokens(self, text: str) -> int:
        return len(text) // 2


def create_ai_client(api_type: str = "claude", api_key: str = "", model: str = "") -> AIClient:
    """AI 客户端工厂函数"""
    if api_type == "openai":
        return OpenAIClient(api_key=api_key, model=model or "gpt-4o")
    return ClaudeClient(api_key=api_key, model=model or "claude-sonnet-4-20250514")
```

- [ ] **Step 2: 实现修改建议引擎**

```python
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
            status=comment.severity.to_status() if hasattr(comment.severity, 'to_status') else None,
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
            suggestion = self.generate_suggestion(comment, paper_info, paper_context)
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
            prompt_parts.append(f"\n## 论文相关上下文\n{paper_context[:2000]}")

        prompt_parts.append(
            "\n请生成具体的修改建议，包括修改方案和修改示例。"
        )

        return "\n".join(prompt_parts)
```

- [ ] **Step 3: 编写测试**

```python
"""修改建议引擎测试"""

import pytest
from src.models import ReviewComment, ReviewCategory, SeverityLevel, PaperInfo
from src.suggestor.ai_client import AIClient, AIMessage
from src.suggestor.suggestion_engine import SuggestionEngine


class MockAIClient(AIClient):
    """模拟 AI 客户端，用于测试"""

    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        return f"针对该意见的修改建议：\n1. 修改方案：补充相关文献\n2. 修改示例：已修改"

    def count_tokens(self, text: str) -> int:
        return len(text) // 2


class TestSuggestionEngine:
    """SuggestionEngine 测试"""

    def setup_method(self):
        self.engine = SuggestionEngine(MockAIClient())

    def test_generate_suggestion(self):
        comment = ReviewComment(
            id="意见1",
            category=ReviewCategory.WRITING,
            severity=SeverityLevel.REQUIRED,
            original_text="论文摘要不够简洁，需要精简。"
        )
        paper_info = PaperInfo(title="测试论文")
        result = self.engine.generate_suggestion(comment, paper_info)
        assert result.comment_id == "意见1"
        assert len(result.suggestion) > 0

    def test_generate_all(self):
        comments = [
            ReviewComment(id="意见1", category=ReviewCategory.WRITING, severity=SeverityLevel.REQUIRED, original_text="意见1"),
            ReviewComment(id="意见2", category=ReviewCategory.FORMAT, severity=SeverityLevel.SUGGESTED, original_text="意见2"),
        ]
        paper_info = PaperInfo(title="测试论文")
        results = self.engine.generate_all(comments, paper_info)
        assert len(results) == 2
```

---

### Task 7: 报告生成器和 PDF 标注模块

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\reporter\__init__.py`
- Create: `D:\APP_self\盲审论文修改skill\src\reporter\report_generator.py`
- Create: `D:\APP_self\盲审论文修改skill\src\reporter\pdf_annotator.py`
- Create: `D:\APP_self\盲审论文修改skill\src\reporter\templates\report.html`

- [ ] **Step 1: 创建 reporter/__init__.py**

```python
from .report_generator import ReportGenerator
from .pdf_annotator import PDFAnnotator

__all__ = ["ReportGenerator", "PDFAnnotator"]
```

- [ ] **Step 2: 实现报告生成器**

```python
"""修改报告生成模块"""

from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from src.models import RevisionReport


class ReportGenerator:
    """修改报告生成器"""

    def __init__(self, template_dir: str | Path | None = None):
        if template_dir:
            self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        else:
            self.env = Environment(loader=FileSystemLoader(
                str(Path(__file__).parent / "templates")
            ))

    def generate_markdown(self, report: RevisionReport) -> str:
        """生成 Markdown 格式的修改报告"""
        lines = [
            f"# 盲审论文修改报告",
            f"",
            f"**论文题目**: {report.paper_info.title or '未知'}",
            f"**生成时间**: {report.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"---",
            f"",
            f"## 一、盲审意见总览",
            f"",
            f"共收到 **{len(report.comments)}** 条评审意见：",
            f"",
        ]

        # 按分类统计
        categories = {}
        for c in report.comments:
            cat = c.category.value
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in categories.items():
            lines.append(f"- {cat}: {count} 条")

        lines.extend([
            f"",
            f"## 二、逐条修改建议",
            f"",
        ])

        for i, (comment, suggestion) in enumerate(zip(
            report.comments, report.suggestions
        ), 1):
            lines.extend([
                f"### {comment.id}",
                f"",
                f"**评审意见**: {comment.original_text}",
                f"",
                f"**分类**: {comment.category.value} | **严重程度**: {comment.severity.value}",
                f"",
                f"**修改建议**:",
                f"",
                f"{suggestion.suggestion}",
                f"",
                f"---",
                f"",
            ])

        if report.format_issues:
            lines.extend([
                f"## 三、格式问题清单",
                f"",
                f"| 问题类型 | 描述 | 位置 | 修改建议 |",
                f"|---------|------|------|---------|",
            ])
            for issue in report.format_issues:
                lines.append(
                    f"| {issue.issue_type} | {issue.description} | {issue.location} | {issue.suggestion} |"
                )

        if report.summary:
            lines.extend([
                f"",
                f"## 四、修改总结",
                f"",
                f"{report.summary}",
            ])

        return "\n".join(lines)

    def generate_html(self, report: RevisionReport) -> str:
        """生成 HTML 格式的修改报告"""
        template = self.env.get_template("report.html")
        return template.render(
            report=report,
            generated_at=report.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M'),
        )

    def save_markdown(self, report: RevisionReport, output_path: str | Path):
        """保存 Markdown 报告"""
        content = self.generate_markdown(report)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    def save_html(self, report: RevisionReport, output_path: str | Path):
        """保存 HTML 报告"""
        content = self.generate_html(report)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
```

- [ ] **Step 3: 实现 PDF 标注器**

```python
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
```

- [ ] **Step 4: 创建 HTML 报告模板**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>盲审论文修改报告</title>
<style>
  body { font-family: "Microsoft YaHei", "SimSun", serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }
  h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 10px; }
  h2 { color: #2c3e50; margin-top: 30px; }
  h3 { color: #34495e; background: #f8f9fa; padding: 8px 12px; border-left: 4px solid #3498db; }
  .meta { color: #666; font-size: 14px; margin-bottom: 20px; }
  .comment { background: #fef9e7; padding: 10px 15px; border-left: 4px solid #f39c12; margin: 10px 0; }
  .suggestion { background: #eaf2f8; padding: 10px 15px; border-left: 4px solid #2980b9; margin: 10px 0; white-space: pre-wrap; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin: 0 4px; }
  .tag-required { background: #fadbd8; color: #c0392b; }
  .tag-suggested { background: #fdebd0; color: #e67e22; }
  .tag-optional { background: #d5f5e3; color: #27ae60; }
  table { width: 100%; border-collapse: collapse; margin: 15px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f2f3f4; }
  .summary { background: #f0f3f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
</style>
</head>
<body>
<h1>盲审论文修改报告</h1>
<div class="meta">
  <p><strong>论文题目：</strong>{{ report.paper_info.title or '未知' }}</p>
  <p><strong>生成时间：</strong>{{ generated_at }}</p>
</div>
<hr>

<h2>一、盲审意见总览</h2>
<p>共收到 <strong>{{ report.comments|length }}</strong> 条评审意见：</p>
<ul>
{% set categories = {} %}
{% for c in report.comments %}
  {% set _ = categories.update({c.category.value: categories.get(c.category.value, 0) + 1}) %}
{% endfor %}
{% for cat, count in categories.items() %}
  <li>{{ cat }}: {{ count }} 条</li>
{% endfor %}
</ul>

<h2>二、逐条修改建议</h2>
{% for comment, suggestion in zip(report.comments, report.suggestions) %}
<h3>{{ comment.id }}</h3>
<div class="comment"><strong>评审意见：</strong>{{ comment.original_text }}</div>
<p>
  <span class="tag tag-{{ comment.severity.value }}">{{ comment.severity.value }}</span>
  <span class="tag">{{ comment.category.value }}</span>
</p>
<div class="suggestion"><strong>修改建议：</strong><br>{{ suggestion.suggestion }}</div>
{% if not loop.last %}<hr>{% endif %}
{% endfor %}

{% if report.format_issues %}
<h2>三、格式问题清单</h2>
<table>
  <tr><th>问题类型</th><th>描述</th><th>位置</th><th>修改建议</th></tr>
  {% for issue in report.format_issues %}
  <tr>
    <td>{{ issue.issue_type }}</td>
    <td>{{ issue.description }}</td>
    <td>{{ issue.location }}</td>
    <td>{{ issue.suggestion }}</td>
  </tr>
  {% endfor %}
</table>
{% endif %}

{% if report.summary %}
<h2>四、修改总结</h2>
<div class="summary">{{ report.summary }}</div>
{% endif %}
</body>
</html>
```

---

### Task 8: CLI 主入口

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\src\cli.py`
- Create: `D:\APP_self\盲审论文修改skill\main.py`

- [ ] **Step 1: 实现 CLI 模块**

```python
"""命令行接口模块"""

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="盲审论文修改工具 - 自动解析盲审意见并生成修改报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --paper 论文.pdf --review 盲审意见.pdf
  python main.py --paper 论文.docx --review 盲审意见.pdf -o ./修改报告
  python main.py --paper 论文.pdf --review 盲审意见.pdf --no-ai  # 仅格式检查
        """,
    )

    parser.add_argument(
        "--paper", "-p",
        required=True,
        help="盲审版本论文路径（PDF 或 Word 格式）",
    )
    parser.add_argument(
        "--review", "-r",
        required=True,
        help="盲审意见书路径（PDF 格式）",
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="输出目录（默认: ./output）",
    )
    parser.add_argument(
        "--ai-api",
        choices=["claude", "openai"],
        default="claude",
        help="AI 模型类型（默认: claude）",
    )
    parser.add_argument(
        "--ai-model",
        default="",
        help="AI 模型名称（如 claude-sonnet-4-20250514）",
    )
    parser.add_argument(
        "--ai-key",
        default="",
        help="AI API 密钥（默认从环境变量读取）",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="不使用 AI 生成修改建议，仅执行格式检查和报告生成",
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="仅执行格式检查，不解析盲审意见",
    )

    return parser


def detect_file_type(file_path: str) -> str:
    """检测文件类型"""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in (".doc", ".docx"):
        return "docx"
    else:
        return "unknown"


def main(args: list[str] | None = None):
    """CLI 主入口"""
    parser = build_parser()
    parsed = parser.parse_args(args)

    paper_path = Path(parsed.paper)
    review_path = Path(parsed.review)

    # 验证文件存在
    if not paper_path.exists():
        print(f"错误：论文文件不存在: {paper_path}")
        sys.exit(1)
    if not review_path.exists():
        print(f"错误：盲审意见文件不存在: {review_path}")
        sys.exit(1)

    # 检测文件类型
    paper_type = detect_file_type(str(paper_path))
    review_type = detect_file_type(str(review_path))

    print(f"📄 论文文件: {paper_path} ({paper_type})")
    print(f"📋 盲审意见: {review_path} ({review_type})")
    print(f"📁 输出目录: {parsed.output}")
    print()

    # 从环境变量读取 API 密钥
    api_key = parsed.ai_key or os.environ.get("AI_API_KEY", "")
    if not api_key and not parsed.no_ai:
        print("⚠ 未设置 AI API 密钥（可通过 --ai-key 或 AI_API_KEY 环境变量设置）")
        print("  将使用规则引擎生成修改建议")

    # 此处后续串联各模块...
    print("✅ 配置就绪，开始处理...")
```

- [ ] **Step 2: 创建 main.py**

```python
"""盲审论文修改工具 - 主入口"""

import sys
import os

# 确保能导入 src 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import main

if __name__ == "__main__":
    main()
```

---

### Task 9: SKILL.md 核心定义

**Files:**
- Create: `D:\APP_self\盲审论文修改skill\SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

See SKILL.md file for the complete content.

---

### Task 10: 安装依赖并验证

- [ ] **Step 1: 安装 Python 依赖**

Run: `pip install -r requirements.txt`
Expected: 所有依赖安装成功

- [ ] **Step 2: 运行测试**

Run: `python -m pytest tests/ -v`

- [ ] **Step 3: 验证 CLI 启动**

Run: `python main.py --help`
Expected: 显示帮助信息
