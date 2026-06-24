"""Auto-fix engine for SherlockCode."""

from __future__ import annotations

import ast
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sherlockcode.providers.base import BaseProvider

# Confidence thresholds for auto-fix
CONFIDENCE_THRESHOLDS = {"safe": 95, "all": 0}

# Categories safe to auto-fix in safe mode
SAFE_CATEGORIES = frozenset({"type_hints", "naming", "null_check"})

# Pre-compiled regex patterns
_PATTERN_BLOCK = re.compile(
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
_PATTERN_FIELD = re.compile(r'\[(\w+):\s*(.+?)\]', re.DOTALL)
_PATTERN_CODE = re.compile(r'```[\w]*\n(.*?)```', re.DOTALL)


def load_fix_prompt_template() -> str:
    """Load the fix prompt template."""
    template_path = Path(__file__).parent.parent / "prompts" / "fix_autofix.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


def _parse_fix_block(text: str) -> list:
    """Parse fix blocks from LLM response."""
    from sherlockcode.core.reviewer import FixIssue

    fixes: list[FixIssue] = []
    text = text.strip()
    file_starts = [m.start() for m in re.finditer(r'\[FILE:', text)]

    for i, start in enumerate(file_starts):
        end = file_starts[i + 1] if i + 1 < len(file_starts) else len(text)
        block = text[start:end].strip()

        file_match = re.search(r'\[FILE:\s*(.+?)\]', block)
        line_match = re.search(r'\[LINE:\s*(.+?)\]', block)
        cat_match = re.search(r'\[CATEGORY:\s*(.+?)\]', block)
        conf_match = re.search(r'\[CONFIDENCE:\s*(\d+)\]', block)
        orig_match = re.search(r'\[ORIGINAL:\]\s*```[\w]*\n(.*?)```', block, re.DOTALL)
        fixed_match = re.search(r'\[FIXED:\]\s*```[\w]*\n(.*?)```', block, re.DOTALL)
        expl_match = re.search(r'\[EXPLANATION:\]\s*(.*?)$', block, re.DOTALL | re.MULTILINE)

        if all([file_match, line_match, cat_match, conf_match]):
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
    if not code.strip():
        return True
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

        if not (1 <= line_number <= len(lines)):
            return False

        target_line = line_number - 1
        old_stripped = old_code.strip()

        # Try exact match first, then fuzzy match
        if lines[target_line].strip() == old_stripped:
            lines[target_line] = new_code
        else:
            for i in range(max(0, target_line - 2), min(len(lines), target_line + 3)):
                if old_stripped in lines[i] or lines[i].strip() == old_stripped:
                    lines[i] = new_code
                    break
            else:
                return False

        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    except (OSError, UnicodeDecodeError):
        return False


def build_fix_prompt(issues_text: str, diff: str, file_contents: dict[str, str]) -> str:
    """Build a fix prompt from review issues."""
    template = load_fix_prompt_template()

    context_parts = []
    if diff:
        context_parts.append(f"## Code Changes (diff)\n```diff\n{diff}\n```")
    if file_contents:
        file_str = "\n".join(
            f"\n### {fname}\n```\n{content}\n```"
            for fname, content in file_contents.items()
        )
        context_parts.append(f"## File Contents{file_str}")
    if issues_text:
        context_parts.append(f"## Issues to Fix\n{issues_text}")

    return f"{template}\n\n" + "\n\n".join(context_parts)


def fix_code(
    provider: "BaseProvider",
    path: Path | None = None,
    diff_target: str | None = None,
    mode: str = "safe",
    dry_run: bool = False,
    max_files: int = 50,
):
    """Execute auto-fix for identified issues."""
    from sherlockcode.core.context import gather_context
    from sherlockcode.core.reviewer import FixResult

    context = gather_context(path, diff_target=diff_target, max_files=max_files)

    issues_text = "The following issues were identified in the code changes:\n"
    if context.diff:
        issues_text += f"\n```diff\n{context.diff}\n```"

    prompt = build_fix_prompt(issues_text, context.diff, context.file_contents)
    response = provider.generate(prompt)
    fixes = _parse_fix_block(response)

    result = FixResult(fixes=fixes, raw_response=response)
    threshold = CONFIDENCE_THRESHOLDS.get(mode, 95)

    for fix in fixes:
        # Skip based on confidence and category
        if fix.confidence < threshold or (mode == "safe" and fix.category not in SAFE_CATEGORIES):
            result.skipped.append(fix)
            if dry_run:
                continue

        # Resolve file path
        base_path = Path.cwd()
        file_path = base_path / fix.file

        if not file_path.exists():
            result.failed.append(fix)
            continue

        # Validate Python syntax
        if file_path.suffix == ".py" and not _validate_python_syntax(fix.fixed_code):
            result.failed.append(fix)
            continue

        # Apply fix
        if not dry_run:
            _backup_file(file_path)

        try:
            line_num = int(fix.line) if fix.line.isdigit() else 1
            if _apply_fix(file_path, line_num, fix.original_code, fix.fixed_code):
                result.applied.append(fix)
            else:
                result.failed.append(fix)
        except Exception:
            result.failed.append(fix)

    return result
