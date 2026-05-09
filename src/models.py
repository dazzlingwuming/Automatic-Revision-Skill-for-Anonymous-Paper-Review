"""盲审论文修改的数据模型定义"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ReviewCategory(str, Enum):
    """评审意见分类"""
    INNOVATION = "创新性"
    EXPERIMENT = "实验设计"
    WRITING = "写作规范"
    FORMAT = "格式规范"
    OTHER = "其他"


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
    id: str
    category: ReviewCategory
    severity: SeverityLevel
    original_text: str
    related_section: Optional[str] = None
    page_ref: Optional[int] = None


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
    comment_id: str
    suggestion: str
    example_text: Optional[str] = None
    status: SuggestionStatus = SuggestionStatus.PENDING


@dataclass
class FormatIssue:
    """格式问题"""
    issue_type: str
    description: str
    location: str
    suggestion: str


@dataclass
class RevisionReport:
    """完整的修改报告"""
    paper_info: PaperInfo
    review_source: str
    comments: list[ReviewComment]
    suggestions: list[RevisionSuggestion]
    format_issues: list[FormatIssue]
    summary: str = ""
    generated_at: str = ""


@dataclass
class TaskConfig:
    """任务配置"""
    paper_path: str
    review_path: str
    output_dir: str = "./output"
    ai_api_type: str = "claude"
    ai_api_key: Optional[str] = None
    ai_model: str = "claude-sonnet-4-20250514"
    use_ai: bool = True
    format_only: bool = False
