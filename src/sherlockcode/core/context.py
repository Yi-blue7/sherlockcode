"""Multi-layer context gathering for code review."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Default patterns to skip
_DEFAULT_IGNORE_PATTERNS = frozenset({
    "*.lock", "*.min.js", "*.min.css", "*.map",
    "vendor/**", "node_modules/**", "__pycache__/**",
    "*.pyc", "*.svg", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico",
    "*.woff", "*.woff2", "*.ttf", "*.eot",
})

_IGNORE_DIRS = frozenset({
    ".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode"
})


@dataclass
class Context:
    """Collected context for a code review."""
    diff: str = ""
    changed_files: list[str] = field(default_factory=list)
    file_contents: dict[str, str] = field(default_factory=dict)
    project_structure: str = ""


def read_file_content(file_path: Path, max_size: int = 50000) -> str:
    """Read file content, skipping binary files."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if "\x00" in content:
            return ""
        return content[:max_size]
    except (UnicodeDecodeError, PermissionError, OSError):
        return ""


def _should_ignore(filename: str, patterns: frozenset[str] | None = None) -> bool:
    """Check if a file should be ignored based on glob patterns."""
    ignore = patterns or _DEFAULT_IGNORE_PATTERNS
    return any(fnmatch.fnmatch(filename, pat) for pat in ignore)


def _is_ignored_dir(name: str) -> bool:
    """Check if directory should be ignored."""
    return name in _IGNORE_DIRS or name.startswith(".")


def get_project_structure(root: Path, max_depth: int = 3) -> str:
    """Get a tree-like representation of the project structure."""
    lines: list[str] = []

    def walk(path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return

        for idx, entry in enumerate(entries):
            if _is_ignored_dir(entry.name):
                continue
            is_last = idx == len(entries) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension, depth + 1)

    walk(root)
    return "\n".join(lines)


def gather_context(
    path: Path | None = None,
    diff_target: str | None = None,
    max_files: int = 50,
    max_file_size: int = 50000,
    ignore_patterns: frozenset[str] | None = None,
) -> Context:
    """Gather all context needed for a code review."""
    from sherlockcode.core.git import get_diff, get_changed_files, get_repo_root

    repo_root = get_repo_root(path)
    context = Context()

    context.diff = get_diff(repo_root, target=diff_target)
    all_files = get_changed_files(repo_root)

    # Filter and limit files
    filtered = [f for f in all_files if not _should_ignore(f, ignore_patterns)][:max_files]
    context.changed_files = filtered

    # Read file contents
    for filename in filtered:
        file_path = repo_root / filename
        if file_path.is_file():
            content = read_file_content(file_path, max_file_size)
            if content:
                context.file_contents[filename] = content

    context.project_structure = get_project_structure(repo_root)
    return context
