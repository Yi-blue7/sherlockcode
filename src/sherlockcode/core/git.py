"""Git operations for SherlockCode."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    """Run a git command and return the output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitError(f"Git command failed: {' '.join(args)}\n{e.stderr.strip()}") from e
    except FileNotFoundError as e:
        raise GitError(f"Git not found: {e}") from e


def is_git_repo(path: Path | None = None) -> bool:
    """Check if the given path is a git repository."""
    try:
        _run_git(["rev-parse", "--git-dir"], cwd=path)
        return True
    except GitError:
        return False


def get_repo_root(path: Path | None = None) -> Path:
    """Get the root directory of the git repository."""
    if path is None:
        path = Path.cwd()
    try:
        root = _run_git(["rev-parse", "--show-toplevel"], cwd=path)
        return Path(root)
    except GitError:
        return path


def get_diff(repo_path: Path, target: str | None = None) -> str:
    """Get git diff for the given target."""
    args = ["diff"]
    if target:
        args.append(target)
    try:
        return _run_git(args, cwd=repo_path)
    except GitError:
        return ""


def get_changed_files(repo_path: Path) -> list[str]:
    """Get list of changed files in the repository."""
    try:
        output = _run_git(["diff", "--name-only", "HEAD"], cwd=repo_path)
        if output:
            return output.split("\n")
    except GitError:
        try:
            output = _run_git(["diff", "--name-only", "--cached"], cwd=repo_path)
            if output:
                return output.split("\n")
        except GitError:
            pass
    return []


def get_commit_history(repo_path: Path, max_count: int = 100) -> list[dict[str, str]]:
    """Get commit history as a list of dicts."""
    args = ["log", f"--max-count={max_count}", "--format=%H|%s|%an|%ad", "--date=iso"]
    try:
        output = _run_git(args, cwd=repo_path)
        commits = []
        for line in output.split("\n"):
            if "|" in line:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "subject": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                    })
        return commits
    except GitError:
        return []
