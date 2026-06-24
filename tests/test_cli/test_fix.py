"""Tests for the fix CLI command."""

import subprocess

import pytest
from typer.testing import CliRunner

from sherlockcode.cli.app import app


runner = CliRunner()


class TestFixCommand:
    def test_fix_not_in_git_repo(self, tmp_path):
        """Test that fix command fails when not in a git repo."""
        result = runner.invoke(app, ["fix"], catch_exceptions=False)
        assert result.exit_code == 4

    def test_fix_help(self):
        """Test fix command help output."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "--preview" in result.output
        assert "--apply" in result.output
        assert "--safe" in result.output
        assert "--all" in result.output

    def test_fix_preview_option(self):
        """Test that --preview option is available."""
        result = runner.invoke(app, ["fix", "--help"])
        assert "--preview" in result.output or "--preview/--apply" in result.output

    def test_fix_safe_option(self):
        """Test that --safe option is available."""
        result = runner.invoke(app, ["fix", "--help"])
        assert "--safe" in result.output or "--safe/--all" in result.output
