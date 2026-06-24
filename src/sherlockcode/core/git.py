"""Git operations wrapper for SherlockCode."""

import subprocess
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def _run_git(args: list[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return its stdout."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise GitError(result.stderr.strip())
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise GitError("Git command timed out")
    except FileNotFoundError:
        raise GitError("Git is not installed or not in PATH")


def is_git_repo(path: Optional[Path] = None) -> bool:
    """Check if the given path is inside a git repository."""
    try:
        _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
        return True
    except GitError:
        return False


def has_commits(path: Optional[Path] = None) -> bool:
    """Check if the repository has at least one commit."""
    try:
        _run_git(["log", "-1", "--format=%H"], cwd=path)
        return True
    except GitError:
        return False


def get_repo_root(path: Optional[Path] = None) -> Path:
    """Get the root directory of the git repository."""
    output = _run_git(["rev-parse", "--show-toplevel"], cwd=path)
    return Path(output).resolve()


def get_changed_files(path: Optional[Path] = None) -> list[str]:
    """Get list of files with unstaged or staged changes."""
    repo_root = get_repo_root(path)

    # If no commits exist, list staged files (added but not committed)
    if not has_commits(repo_root):
        try:
            output = _run_git(["diff", "--name-only", "--cached"], cwd=repo_root)
            if output:
                return [f for f in output.split("\n") if f]
        except GitError:
            pass
        # Also check for untracked files
        try:
            output = _run_git(["ls-files", "--others", "--exclude-standard"], cwd=repo_root)
            if not output:
                return []
            return [f for f in output.split("\n") if f]
        except GitError:
            return []

    try:
        output = _run_git(["diff", "--name-only", "HEAD"], cwd=repo_root)
        if not output:
            return []
        return [f for f in output.split("\n") if f]
    except GitError:
        try:
            output = _run_git(["diff", "--name-only", "--cached"], cwd=repo_root)
            if not output:
                return []
            return [f for f in output.split("\n") if f]
        except GitError:
            return []


def get_diff(path: Optional[Path] = None, target: Optional[str] = None) -> str:
    """Get the git diff output.

    Args:
        path: Working directory (defaults to current).
        target: Diff target, e.g. 'HEAD~3' or 'main..feature'.
    """
    repo_root = get_repo_root(path)
    args = ["diff"]
    if target:
        args.append(target)
    return _run_git(args, cwd=repo_root)


def get_staged_diff(path: Optional[Path] = None) -> str:
    """Get staged diff (includes both staged and unstaged)."""
    repo_root = get_repo_root(path)
    return _run_git(["diff", "HEAD"], cwd=repo_root)
