"""Tests for context gathering module."""

import subprocess

from sherlockcode.core.context import (
    gather_context,
    Context,
    read_file_content,
    get_project_structure,
)


class TestReadFileContent:
    def test_reads_file_content(self, tmp_path):
        file_path = tmp_path / "test.py"
        file_path.write_text("print('hello')")
        result = read_file_content(file_path)
        assert result == "print('hello')"

    def test_returns_empty_for_binary_file(self, tmp_path):
        file_path = tmp_path / "test.bin"
        file_path.write_bytes(b"\x00\x01\x02")
        result = read_file_content(file_path)
        assert result == ""


class TestGetProjectStructure:
    def test_returns_file_tree(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "README.md").write_text("")
        structure = get_project_structure(tmp_path)
        assert "src/" in structure
        assert "main.py" in structure
        assert "README.md" in structure


class TestGatherContext:
    def test_gathers_diff_and_files(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("def main():\n    pass\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        (repo / "src" / "main.py").write_text("def main():\n    print('hello')\n")

        context = gather_context(repo)
        assert isinstance(context, Context)
        assert context.diff is not None
        assert len(context.changed_files) > 0
