"""Tests for Git operations module."""

import subprocess

import pytest

from sherlockcode.core.git import (
    get_diff,
    get_changed_files,
    is_git_repo,
    get_repo_root,
    GitError,
)


class TestIsGitRepo:
    def test_in_git_repo_returns_true(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        assert is_git_repo(repo) is True

    def test_not_in_git_repo_returns_false(self, tmp_path):
        assert is_git_repo(tmp_path) is False


class TestGetRepoRoot:
    def test_returns_repo_root(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subdir = repo / "sub" / "deep"
        subdir.mkdir(parents=True)
        root = get_repo_root(subdir)
        assert root == repo.resolve()


class TestGetChangedFiles:
    def test_empty_repo_no_files(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        files = get_changed_files(repo)
        assert files == []

    def test_staged_file_detected(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "test.py").write_text("print('hello')")
        subprocess.run(["git", "add", "test.py"], cwd=repo, capture_output=True)
        files = get_changed_files(repo)
        assert "test.py" in files


class TestGetDiff:
    def test_empty_diff_when_no_changes(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "test.py").write_text("print('hello')")
        subprocess.run(["git", "add", "test.py"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        diff = get_diff(repo)
        assert diff == ""

    def test_diff_shows_unstaged_changes(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "test.py").write_text("line1")
        subprocess.run(["git", "add", "test.py"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        (repo / "test.py").write_text("line1\nline2")
        diff = get_diff(repo)
        assert "line2" in diff
