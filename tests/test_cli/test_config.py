"""Tests for the config CLI commands."""

import os

from typer.testing import CliRunner

from sherlockcode.cli.app import app


runner = CliRunner()


class TestConfigInit:
    def test_init_creates_config_file(self, tmp_path):
        os.chdir(str(tmp_path))
        result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 0
        config_file = tmp_path / ".sherlockconfig.yml"
        assert config_file.exists()
