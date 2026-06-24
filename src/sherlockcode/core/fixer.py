"""Auto-fix engine for SherlockCode."""

import ast
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from sherlockcode.providers.base import BaseProvider
from sherlockcode.core.context import gather_context, Context
from sherlockcode.core.reviewer import FixIssue, FixResult

# Confidence thresholds for auto-fix
CONFIDENCE_THRESHOLDS = {
    "safe": 95,   # High confidence, can be auto-applied
    "all": 0,     # Apply all fixes
}

# Categories that are safe to auto-fix in safe mode
SAFE_CATEGORIES = {"type_hints", "naming", "null_check"}


def load_fix_prompt_template() -> str:
    """Load the fix prompt template."""
    template_path = Path(__file__).parent.parent / "prompts" / "fix_autofix.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


def _parse_fix_block(text: str) -> list[FixIssue]:
    """Parse fix blocks from LLM response."""
    fixes = []
    # Pattern to match fix blocks - look for [FILE: as the start of a new block
    pattern = re.compile(
        r'\[FILE:\s*(.+?)\]\s*'
        r'\[LINE:\s*(.+?)\]\s*'
        r'\[CATEGORY:\s*(.+?)\]\s*'
        r'\[CONFIDENCE:\s*(\d+)\]\s*'
        r'\[ORIGINAL:\]\s*```[\w]*\n(.*?)```\s*'
        r'\[FIXED:\]\s*```[\w]*\n(.*?)```\s*'
        r'(?:\[EXPLANATION:\]\s*(.*?))?\s*'
        r'(?=\n\[FILE:|\Z)',
        re.DOTALL,
    )

    # Split text by [FILE: to process each block separately
    # First strip leading/trailing whitespace
    text = text.strip()

    # Find all [FILE: positions
    file_starts = [m.start() for m in re.finditer(r'\[FILE:', text)]

    for i, start in enumerate(file_starts):
        # Extract block text (from this [FILE: to just before next [FILE: or end)
        end = file_starts[i + 1] if i + 1 < len(file_starts) else len(text)
        block_text = text[start:end].strip()

        # Now extract fields from this block
        file_match = re.search(r'\[FILE:\s*(.+?)\]', block_text)
        line_match = re.search(r'\[LINE:\s*(.+?)\]', block_text)
        cat_match = re.search(r'\[CATEGORY:\s*(.+?)\]', block_text)
        conf_match = re.search(r'\[CONFIDENCE:\s*(\d+)\]', block_text)

        # Extract code between ``` markers
        orig_match = re.search(r'\[ORIGINAL:\]\s*```[\w]*\n(.*?)```', block_text, re.DOTALL)
        fixed_match = re.search(r'\[FIXED:\]\s*```[\w]*\n(.*?)```', block_text, re.DOTALL)
        expl_match = re.search(r'\[EXPLANATION:\]\s*(.*?)$', block_text, re.DOTALL | re.MULTILINE)

        if file_match and line_match and cat_match and conf_match:
            fixes.append(FixIssue(
                file=file_match.group(1).strip(),
                line=line_match.group(1).strip(),
                category=cat_match.group(1).strip(),
                confidence=int(conf_match.group(1).strip()),
                original_code=orig_match.group(1).strip() if orig_match else "",
                fixed_code=fixed_match.group(1).strip() if fixed_match else "",
                explanation=expl_match.group(1).strip() if expl_match else "",
            ))

    return fixes


def _validate_python_syntax(code: str) -> bool:
    """Validate Python syntax by parsing with ast."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _backup_file(file_path: Path) -> Path:
    """Create a backup of a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak.{timestamp}")
    shutil.copy2(file_path, backup_path)
    return backup_path


def _apply_fix(file_path: Path, line_number: int, old_code: str, new_code: str) -> bool:
    """Apply a fix to a file at the specified line."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        if line_number < 1 or line_number > len(lines):
            return False

        target_line = line_number - 1  # Convert to 0-indexed

        # Try exact match first
        if lines[target_line].strip() == old_code.strip():
            lines[target_line] = new_code
        else:
            # Try fuzzy match - find lines with similar content
            for i in range(max(0, target_line - 2), min(len(lines), target_line + 3)):
                if old_code.strip() in lines[i] or lines[i].strip() == old_code.strip():
                    lines[i] = new_code
                    target_line = i
                    break
            else:
                return False

        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    except (OSError, UnicodeDecodeError):
        return False


def build_fix_prompt(
    issues_text: str,
    diff: str,
    file_contents: dict[str, str],
) -> str:
    """Build a fix prompt from review issues."""
    template = load_fix_prompt_template()

    context_parts = []
    if diff:
        context_parts.append("## Code Changes (diff)\n```diff\n" + diff + "\n```")
    if file_contents:
        file_contents_str = ""
        for fname, content in file_contents.items():
            file_contents_str += f"\n### {fname}\n```\n{content}\n```"
        context_parts.append("## File Contents" + file_contents_str)
    if issues_text:
        context_parts.append("## Issues to Fix\n" + issues_text)

    return template + "\n\n" + "\n\n".join(context_parts)


def fix_code(
    provider: BaseProvider,
    path: Optional[Path] = None,
    diff_target: Optional[str] = None,
    mode: str = "safe",
    dry_run: bool = False,
    max_files: int = 50,
) -> FixResult:
    """Execute auto-fix for identified issues.

    Args:
        provider: LLM provider for generating fixes
        path: Path to the repository (defaults to current directory)
        diff_target: Git diff target (commit/branch)
        mode: Fix mode - 'safe' (high confidence only) or 'all' (all fixes)
        dry_run: If True, don't apply fixes, just show them
        max_files: Maximum number of files to process

    Returns:
        FixResult with applied, skipped, and failed fixes
    """
    context = gather_context(path, diff_target=diff_target, max_files=max_files)

    # Format issues from diff for the fix prompt
    issues_text = "The following issues were identified in the code changes:\n"
    if context.diff:
        issues_text += f"\n```diff\n{context.diff}\n```"

    prompt = build_fix_prompt(
        issues_text=issues_text,
        diff=context.diff,
        file_contents=context.file_contents,
    )

    response = provider.generate(prompt)
    fixes = _parse_fix_block(response)

    result = FixResult(
        fixes=fixes,
        raw_response=response,
    )

    # Apply or skip fixes based on mode and confidence
    threshold = CONFIDENCE_THRESHOLDS.get(mode, 95)

    for fix in fixes:
        if fix.confidence < threshold:
            result.skipped.append(fix)
            continue

        if mode == "safe" and fix.category not in SAFE_CATEGORIES:
            result.skipped.append(fix)
            continue

        if dry_run:
            result.skipped.append(fix)
            continue

        # Apply the fix
        file_path = Path(context.diff.split(":")[0]) if ":" not in fix.file else None
        if not file_path:
            # Try to find the file in the repository
            repo_path = context.diff.split(":")[0] if ":" in context.diff else ""
            if repo_path:
                base_path = Path(repo_path).parent if "/" in repo_path else Path.cwd()
            else:
                base_path = Path.cwd()
            file_path = base_path / fix.file

        if not file_path.exists():
            result.failed.append(fix)
            continue

        # Validate syntax for Python files
        if file_path.suffix == ".py" and not _validate_python_syntax(fix.fixed_code):
            result.failed.append(fix)
            continue

        # Create backup
        if not dry_run:
            _backup_file(file_path)

        # Apply the fix
        try:
            line_num = int(fix.line) if fix.line.isdigit() else 1
            if _apply_fix(file_path, line_num, fix.original_code, fix.fixed_code):
                result.applied.append(fix)
            else:
                result.failed.append(fix)
        except Exception:
            result.failed.append(fix)

    return result
