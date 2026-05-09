"""论文格式规范性检查模块"""

import re
from src.models import FormatIssue


class FormatChecker:
    """论文格式检查器"""

    def check(self, text: str) -> list[FormatIssue]:
        """执行所有格式检查"""
        issues = []
        issues.extend(self._check_abstract(text))
        issues.extend(self._check_keywords(text))
        issues.extend(self._check_references(text))
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
        ref_section = re.search(
            r'参考[文\s]献(.*?)(?:\n\s*\n\s*\n|$)',
            text, re.DOTALL
        )
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
