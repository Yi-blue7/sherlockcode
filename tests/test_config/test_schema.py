"""Tests for configuration schema models."""

import pytest
from pydantic import ValidationError

from sherlockcode.config.schema import (
    ProviderModelConfig,
    ProviderConfig,
    SherlockConfig,
)


class TestProviderModelConfig:
    def test_valid_model_config(self):
        config = ProviderModelConfig(api_key="sk-test", model="gpt-4o", max_tokens=4096)
        assert config.api_key == "sk-test"
        assert config.model == "gpt-4o"
        assert config.max_tokens == 4096

    def test_default_max_tokens(self):
        config = ProviderModelConfig(api_key="sk-test", model="gpt-4o")
        assert config.max_tokens == 4096

    def test_missing_api_key_raises(self):
        with pytest.raises(ValidationError):
            ProviderModelConfig(model="gpt-4o")

    def test_missing_model_raises(self):
        with pytest.raises(ValidationError):
            ProviderModelConfig(api_key="sk-test")


class TestProviderConfig:
    def test_valid_provider_config(self):
        config = ProviderConfig(
            default="claude",
            models={
                "claude": {"api_key": "sk-test", "model": "claude-3-sonnet"},
                "openai": {"api_key": "sk-test", "model": "gpt-4o"},
            },
        )
        assert config.default == "claude"


class TestSherlockConfig:
    def test_full_config(self):
        data = {
            "provider": {
                "default": "claude",
                "models": {
                    "claude": {"api_key": "sk-test", "model": "claude-3-5-sonnet"},
                },
            },
            "review": {"persona": "default", "max_files": 50},
            "fix": {"mode": "safe", "auto_validate": True, "backup": True},
            "learn": {"enabled": True, "max_commits": 500, "auto_learn": True},
            "output": {"format": "terminal", "color": True, "show_scores": True},
        }
        config = SherlockConfig(**data)
        assert config.review.persona == "default"
        assert config.review.max_files == 50
        assert config.fix.mode == "safe"
