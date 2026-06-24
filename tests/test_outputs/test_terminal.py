"""Tests for terminal output formatter."""

from sherlockcode.core.reviewer import ReviewResult, ReviewIssue, Context
from sherlockcode.outputs.terminal import TerminalOutput


class TestTerminalOutput:
    def test_format_result_no_issues(self):
        result = ReviewResult(
            issues=[],
            summary="All good.",
            context=Context(diff="+x", changed_files=["test.py"]),
        )
        output = TerminalOutput()
        formatted = output.format(result)
        assert "All good" in formatted
        assert "Files changed: 1" in formatted

    def test_format_result_with_issues(self):
        result = ReviewResult(
            issues=[
                ReviewIssue(
                    severity="high",
                    file="auth.py",
                    line="10",
                    category="security",
                    description="Hardcoded API key",
                    suggestion="Use env var",
                ),
                ReviewIssue(
                    severity="medium",
                    file="utils.py",
                    line="5",
                    category="performance",
                    description="Slow loop",
                    suggestion="Use comprehension",
                ),
            ],
            summary="Needs fixes.",
            context=Context(diff="+x", changed_files=["auth.py", "utils.py"]),
        )
        output = TerminalOutput()
        formatted = output.format(result)
        assert "auth.py" in formatted
        assert "security" in formatted
        assert "Hardcoded API key" in formatted
