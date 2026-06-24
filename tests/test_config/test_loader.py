"""Tests for configuration loader."""

import os

from sherlockcode.config.loader import load_config
from sherlockcode.config.schema import SherlockConfig


class TestLoadConfig:
    def test_load_from_yaml_file(self, temp_dir, sample_config_yaml):
        config_path = temp_dir / ".sherlockconfig.yml"
        config_path.write_text(sample_config_yaml)
        config = load_config(config_path)
        assert config.provider.default == "claude"
        assert config.review.persona == "default"
        assert config.review.max_files == 50

    def test_load_missing_file_uses_defaults(self, temp_dir):
        config_path = temp_dir / "nonexistent.yml"
        config = load_config(config_path)
        assert isinstance(config, SherlockConfig)

    def test_env_var_overrides_default(self, temp_dir, sample_config_yaml):
        config_path = temp_dir / ".sherlockconfig.yml"
        config_path.write_text(sample_config_yaml)
        os.environ["SHERLOCK_PROVIDER"] = "openai"
        config = load_config(config_path)
        assert config.provider.default == "openai"
        del os.environ["SHERLOCK_PROVIDER"]

    def test_env_var_overrides_persona(self, temp_dir, sample_config_yaml):
        config_path = temp_dir / ".sherlockconfig.yml"
        config_path.write_text(sample_config_yaml)
        os.environ["SHERLOCK_PERSONA"] = "security"
        config = load_config(config_path)
        assert config.review.persona == "security"
        del os.environ["SHERLOCK_PERSONA"]
