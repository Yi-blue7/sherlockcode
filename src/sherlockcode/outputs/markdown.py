"""Markdown report output formatter for SherlockCode."""

from pathlib import Path

from sherlockcode.core.reviewer import ReviewResult, ReviewIssue


class MarkdownOutput:
    """Formats review results as Markdown for PR comments or reports."""

    def format(self, result: ReviewResult) -> str:
        """Build a Markdown-formatted review report."""
        lines = []

        lines.append("# 🔍 SherlockCode Review Report")
        lines.append("")

        if result.context:
            lines.append(f"**审查范围**: {len(result.context.changed_files)} files changed")
            if result.context.diff:
                diff_lines = result.context.diff.count("\n")
                lines.append(f"**变更行数**: ~{diff_lines} lines")
            lines.append("")

        if result.issues:
            high = [i for i in result.issues if i.severity == "high"]
            med = [i for i in result.issues if i.severity == "medium"]
            low = [i for i in result.issues if i.severity == "low"]

            if high:
                lines.append(f"## 🔴 高优先级 ({len(high)})")
                for issue in high:
                    lines.extend(self._format_issue(issue))
                lines.append("")

            if med:
                lines.append(f"## 🟡 中优先级 ({len(med)})")
                for issue in med:
                    lines.extend(self._format_issue(issue))
                lines.append("")

            if low:
                lines.append(f"## 🟢 低优先级 ({len(low)})")
                for issue in low:
                    lines.extend(self._format_issue(issue))
                lines.append("")
        else:
            lines.append("## ✅ No issues found!")
            lines.append("")

        if result.summary:
            lines.append("## 📋 总结")
            lines.append(result.summary)
            lines.append("")

        lines.append("---")
        lines.append("*由 SherlockCode 提供*")

        return "\n".join(lines)

    def _format_issue(self, issue: ReviewIssue) -> list[str]:
        """Format a single issue as Markdown."""
        lines = []
        lines.append(f"### [{issue.category}] `{issue.file}:{issue.line}`")
        lines.append(issue.description)
        if issue.suggestion:
            lines.append(f"\n**建议**: {issue.suggestion}")
        lines.append("")
        return lines

    def save(self, result: ReviewResult, path: Path):
        """Save the formatted report to a file."""
        content = self.format(result)
        path.write_text(content, encoding="utf-8")
