"""Tests for the CLI application."""

from typer.testing import CliRunner

from sherlockcode.cli.app import app


runner = CliRunner()


def test_app_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "review" in result.output


def test_app_version():
    result = runner.invoke(app, ["--version"])
    assert "SherlockCode" in result.output
