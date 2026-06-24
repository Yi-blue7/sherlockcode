"""Multi-layer context gathering for code review."""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sherlockcode.core.git import get_diff, get_changed_files, get_repo_root


@dataclass
class Context:
    """Collected context for a code review."""
    diff: str = ""
    changed_files: list[str] = field(default_factory=list)
    file_contents: dict[str, str] = field(default_factory=dict)
    project_structure: str = ""


# Default patterns to skip when reading file contents
_DEFAULT_IGNORE_PATTERNS = [
    "*.lock", "*.min.js", "*.min.css", "*.map",
    "vendor/**", "node_modules/**", "__pycache__/**",
    "*.pyc", "*.svg", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico",
    "*.woff", "*.woff2", "*.ttf", "*.eot",
]


def read_file_content(file_path: Path, max_size: int = 50000) -> str:
    """Read file content, skipping binary files."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if "\x00" in content:
            return ""
        return content[:max_size]
    except (UnicodeDecodeError, PermissionError, OSError):
        return ""


def _should_ignore(filename: str, ignore_patterns: list[str] | None = None) -> bool:
    """Check if a file should be ignored based on glob patterns."""
    patterns = ignore_patterns or _DEFAULT_IGNORE_PATTERNS
    return any(fnmatch.fnmatch(filename, pat) for pat in patterns)


def get_project_structure(root: Path, max_depth: int = 3) -> str:
    """Get a tree-like representation of the project structure."""
    lines = []
    ignore_dirs = {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode"}

    def walk(path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            if entry.name in ignore_dirs or entry.name.startswith("."):
                continue
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension, depth + 1)

    walk(root)
    return "\n".join(lines)


def gather_context(
    path: Optional[Path] = None,
    diff_target: Optional[str] = None,
    max_files: int = 50,
    max_file_size: int = 50000,
    ignore_patterns: list[str] | None = None,
) -> Context:
    """Gather all context needed for a code review."""
    repo_root = get_repo_root(path)
    context = Context()

    context.diff = get_diff(repo_root, target=diff_target)
    all_changed_files = get_changed_files(repo_root)

    # Filter out ignored files and respect max_files limit
    filtered_files = [
        f for f in all_changed_files
        if not _should_ignore(f, ignore_patterns)
    ][:max_files]
    context.changed_files = filtered_files

    # Only read file contents for filtered files
    for filename in context.changed_files:
        file_path = repo_root / filename
        if file_path.exists() and file_path.is_file():
            content = read_file_content(file_path, max_file_size)
            if content:
                context.file_contents[filename] = content

    context.project_structure = get_project_structure(repo_root)

    return context
