"""命令行接口模块"""

import argparse
import os
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="盲审论文修改工具 - 自动解析盲审意见并生成修改报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  python main.py --paper 论文.pdf --review 盲审意见.pdf
  python main.py --paper 论文.docx --review 盲审意见.pdf -o ./修改报告
  python main.py --paper 论文.pdf --review 盲审意见.pdf --format-only
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
        help="AI API 密钥（默认从 AI_API_KEY 环境变量读取）",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="不使用 AI 生成修改建议，仅执行格式检查和基础报告",
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

    # 从环境变量读取 API 密钥
    api_key = parsed.ai_key or os.environ.get("AI_API_KEY", "")
    if not api_key and not parsed.no_ai:
        print("\n⚠ 未设置 AI API 密钥")
        print("   可通过 --ai-key 参数或 AI_API_KEY 环境变量设置")
        print("   将使用规则引擎生成基础修改建议\n")

    print("\n✅ 配置就绪，开始处理...")
    print(f"   模式: {'格式检查' if parsed.format_only else '完整处理'}")
    print(f"   AI: {'禁用' if parsed.no_ai else '启用'}")
