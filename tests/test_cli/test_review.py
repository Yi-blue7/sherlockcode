"""Tests for the review CLI command."""

from typer.testing import CliRunner

from sherlockcode.cli.app import app


runner = CliRunner()


class TestReviewCommand:
    def test_review_not_in_git_repo(self, tmp_path):
        import os
        os.chdir(str(tmp_path))
        result = runner.invoke(app, ["review"])
        assert result.exit_code != 0

    def test_review_help(self):
        result = runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "--persona" in result.output
