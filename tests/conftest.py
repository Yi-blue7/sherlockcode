"""Shared test fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_config_yaml():
    """Return a sample configuration YAML string."""
    return """provider:
  default: claude
  models:
    claude:
      api_key: test-key
      model: claude-3-5-sonnet-20241022
      max_tokens: 4096
    openai:
      api_key: test-key
      model: gpt-4o
      max_tokens: 4096

review:
  persona: default
  max_files: 50
  max_diff_lines: 5000
  ignore_patterns:
    - "*.lock"
    - "*.min.js"

fix:
  mode: safe
  auto_validate: true
  backup: true

learn:
  enabled: true
  max_commits: 500
  auto_learn: true

output:
  format: terminal
  color: true
  show_scores: true
"""
