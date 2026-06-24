"""Configuration loader with YAML file and environment variable support."""

import os
from pathlib import Path
from typing import Optional

import yaml

from sherlockcode.config.schema import SherlockConfig

DEFAULT_CONFIG_PATH = ".sherlockconfig.yml"


def _apply_env_overrides(config: SherlockConfig) -> SherlockConfig:
    """Apply environment variable overrides to configuration."""
    env_mappings = {
        "SHERLOCK_PROVIDER": ("provider", "default"),
        "SHERLOCK_PERSONA": ("review", "persona"),
        "SHERLOCK_FIX_MODE": ("fix", "mode"),
    }

    for env_var, (section, field) in env_mappings.items():
        value = os.environ.get(env_var)
        if value:
            section_obj = getattr(config, section)
            setattr(section_obj, field, value)

    return config


def load_config(config_path: Optional[Path] = None) -> SherlockConfig:
    """Load SherlockCode configuration from file, with env var overrides."""
    if config_path is None:
        config_path = Path(DEFAULT_CONFIG_PATH)

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = SherlockConfig(**data)
    else:
        config = SherlockConfig()

    config = _apply_env_overrides(config)
    return config
