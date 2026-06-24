"""Code review engine for SherlockCode."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sherlockcode.providers.base import BaseProvider
from sherlockcode.core.context import gather_context, Context

# Pre-compiled regex patterns for parsing LLM responses
# Primary: matches the standard format with optional emoji prefix
_ISSUE_PATTERN_PRIMARY = re.compile(
    r'(?:[🔴🟡🟢]\s*)?\*\*(high|medium|low)\*\*\s*[-–]\s*`([^`]+):(\d+)`\s*[-–]\s*(\w+)\s*\n'
    r'(.*?)(?:\n\s*Suggest:\s*(.*?))?(?=\n\n|\n\*\*|\Z)',
    re.DOTALL,
)
# Fallback: matches a simpler format without backtick line numbers
_ISSUE_PATTERN_FALLBACK = re.compile(
    r'(?:[🔴🟡🟢]\s*)?\*\*(high|medium|low)\*\*\s*[-–:\s]+`?([^`:]+)`?\s*[:\s]+(\d+)\s*[-–:\s]+(\w+)\s*\n'
    r'(.*?)(?:\n\s*Suggest(?:ion)?:\s*(.*?))?(?=\n\n|\n\*\*|\n#{1,3}\s|\Z)',
    re.DOTALL,
)


@dataclass
class ReviewIssue:
    """A single issue found during code review."""
    severity: str
    file: str
    line: str
    category: str
    description: str
    suggestion: str = ""


@dataclass
class ReviewResult:
    """Complete result of a code review."""
    issues: list[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    context: Optional[Context] = None


@dataclass
class FixIssue:
    """A single fix suggested for an issue."""
    file: str
    line: str
    category: str
    confidence: int
    original_code: str
    fixed_code: str
    explanation: str = ""


@dataclass
class FixResult:
    """Result of a fix operation."""
    fixes: list[FixIssue] = field(default_factory=list)
    applied: list[FixIssue] = field(default_factory=list)
    skipped: list[FixIssue] = field(default_factory=list)
    failed: list[FixIssue] = field(default_factory=list)
    raw_response: str = ""


def load_prompt_template(persona: str = "default") -> str:
    """Load a prompt template for the given persona."""
    template_dir = Path(__file__).parent.parent / "prompts"
    template_path = template_dir / f"review_{persona}.md"

    if not template_path.exists():
        template_path = template_dir / "review_default.md"

    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


def _truncate_diff(diff: str, max_lines: int = 5000) -> str:
    """Truncate diff to max_lines, preserving the header."""
    if not diff:
        return diff
    lines = diff.split("\n")
    if len(lines) <= max_lines:
        return diff
    # Keep the first max_lines lines and add a truncation notice
    return "\n".join(lines[:max_lines]) + f"\n\n... (truncated, showing first {max_lines} of {len(lines)} lines)"


def build_review_prompt(
    diff: str,
    changed_files: list[str],
    file_contents: dict[str, str],
    project_structure: str,
    persona: str = "default",
    max_diff_lines: int = 5000,
) -> str:
    """Build a complete review prompt with context."""
    template = load_prompt_template(persona)

    context_parts = []
    if diff:
        truncated_diff = _truncate_diff(diff, max_diff_lines)
        context_parts.append("## Code Changes (diff)\n```diff\n" + truncated_diff + "\n```")
    if changed_files:
        context_parts.append("## Changed Files\n" + "\n".join(f"- {f}" for f in changed_files))
    if file_contents:
        file_contents_str = ""
        for fname, content in file_contents.items():
            file_contents_str += f"\n### {fname}\n```\n{content}\n```"
        context_parts.append("## File Contents" + file_contents_str)
    if project_structure:
        context_parts.append("## Project Structure\n```\n" + project_structure + "\n```")

    full_prompt = template + "\n\n" + "\n\n".join(context_parts)
    return full_prompt


def _parse_with_pattern(response: str, pattern: re.Pattern) -> list[ReviewIssue]:
    """Parse issues from response using a given regex pattern."""
    issues = []
    for match in pattern.finditer(response):
        severity, file, line, category, description, suggestion = match.groups()
        issues.append(ReviewIssue(
            severity=severity,
            file=file.strip(),
            line=line.strip(),
            category=category.strip(),
            description=description.strip(),
            suggestion=suggestion.strip() if suggestion else "",
        ))
    return issues


def parse_review_response(response: str) -> list[ReviewIssue]:
    """Parse the LLM response into structured ReviewIssue objects.

    Tries the primary pattern first, then falls back to a more lenient one.
    """
    if not response:
        return []

    issues = _parse_with_pattern(response, _ISSUE_PATTERN_PRIMARY)
    if issues:
        return issues

    return _parse_with_pattern(response, _ISSUE_PATTERN_FALLBACK)


def extract_summary(response: str) -> str:
    """Extract the summary section from the review response."""
    # Try multiple summary heading patterns
    for pattern in [
        r'###\s*Summary\s*\n(.*?)(?:\Z)',
        r'###\s*\w+\s*Summary\s*\n(.*?)(?:\Z)',
        r'###\s*Assessment\s*\n(.*?)(?:\Z)',
    ]:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


def review_code(
    provider: BaseProvider,
    path: Optional[Path] = None,
    diff_target: Optional[str] = None,
    persona: str = "default",
    max_diff_lines: int = 5000,
    max_files: int = 50,
) -> ReviewResult:
    """Execute a complete code review cycle."""
    context = gather_context(path, diff_target=diff_target, max_files=max_files)

    prompt = build_review_prompt(
        diff=context.diff,
        changed_files=context.changed_files,
        file_contents=context.file_contents,
        project_structure=context.project_structure,
        persona=persona,
        max_diff_lines=max_diff_lines,
    )

    response = provider.generate(prompt)

    issues = parse_review_response(response)
    summary = extract_summary(response)

    return ReviewResult(
        issues=issues,
        summary=summary,
        raw_response=response,
        context=context,
    )
