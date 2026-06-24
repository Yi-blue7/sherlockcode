"""Configuration management for SherlockCode."""

from sherlockcode.config.schema import SherlockConfig
from sherlockcode.config.loader import load_config

__all__ = ["SherlockConfig", "load_config"]
