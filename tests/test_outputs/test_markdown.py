"""Tests for markdown output formatter."""

from sherlockcode.core.reviewer import ReviewResult, ReviewIssue, Context
from sherlockcode.outputs.markdown import MarkdownOutput


class TestMarkdownOutput:
    def test_format_result_no_issues(self):
        result = ReviewResult(
            issues=[],
            summary="All good.",
            context=Context(diff="+x", changed_files=["test.py"]),
        )
        output = MarkdownOutput()
        formatted = output.format(result)
        assert "SherlockCode Review Report" in formatted
        assert "1 files changed" in formatted
        assert "No issues found" in formatted

    def test_format_result_with_issues(self):
        result = ReviewResult(
            issues=[
                ReviewIssue(
                    severity="high",
                    file="auth.py",
                    line="10",
                    category="security",
                    description="Hardcoded API key found",
                    suggestion="Use environment variable",
                ),
            ],
            summary="Code needs fixes.",
            context=Context(changed_files=["auth.py"]),
        )
        output = MarkdownOutput()
        formatted = output.format(result)
        assert "auth.py" in formatted
        assert "security" in formatted
        assert "Hardcoded API key" in formatted
        assert "Code needs fixes" in formatted

    def test_save_to_file(self, temp_dir):
        result = ReviewResult(
            issues=[],
            summary="All good.",
            context=Context(changed_files=["test.py"]),
        )
        output = MarkdownOutput()
        output_path = temp_dir / "report.md"
        output.save(result, output_path)
        assert output_path.exists()
        content = output_path.read_text()
        assert "SherlockCode" in content
