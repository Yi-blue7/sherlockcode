"""Tests for the learn CLI command."""

import subprocess

from typer.testing import CliRunner

from sherlockcode.cli.app import app


runner = CliRunner()


class TestLearnCommand:
    def test_learn_not_in_git_repo(self, tmp_path):
        """Test that learn command fails when not in a git repo."""
        result = runner.invoke(app, ["learn"], catch_exceptions=False)
        assert result.exit_code == 4

    def test_learn_help(self):
        """Test learn command help output."""
        result = runner.invoke(app, ["learn", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--stats" in result.output
        assert "--export" in result.output
        assert "--reset" in result.output

    def test_learn_stats_option(self):
        """Test that --stats option is available."""
        result = runner.invoke(app, ["learn", "--help"])
        assert "--stats" in result.output

    def test_learn_reset_option(self):
        """Test that --reset option is available."""
        result = runner.invoke(app, ["learn", "--help"])
        assert "--reset" in result.output
