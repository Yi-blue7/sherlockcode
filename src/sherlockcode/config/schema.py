"""Pydantic configuration models for SherlockCode."""

import os
import re
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, model_validator

_ENV_VAR_RE = re.compile(r'^\$\{(.+)\}$')


class ProviderModelConfig(BaseModel):
    """Configuration for a single LLM provider model."""

    api_key: str = Field(description="API key for the provider")
    model: str = Field(description="Model name/identifier")
    max_tokens: int = Field(default=4096, description="Maximum tokens in response")
    endpoint: Optional[str] = Field(default=None, description="Custom API endpoint for local models")

    def get_api_key(self) -> str:
        """Resolve API key, supporting ${ENV_VAR} syntax."""
        match = _ENV_VAR_RE.match(self.api_key)
        if match:
            return os.environ.get(match.group(1), "")
        return self.api_key


class ProviderConfig(BaseModel):
    """Configuration for LLM providers."""

    default: str = Field(default="claude", description="Default provider name")
    models: Dict[str, ProviderModelConfig] = Field(
        default_factory=dict, description="Provider model configurations"
    )

    @model_validator(mode='after')
    def validate_default_exists(self) -> 'ProviderConfig':
        if self.models and self.default not in self.models:
            raise ValueError(f"Default provider '{self.default}' not found in models")
        return self


class ReviewConfig(BaseModel):
    """Configuration for code review."""

    persona: str = Field(default="default", description="Review persona")
    max_files: int = Field(default=50, description="Maximum files to review")
    max_diff_lines: int = Field(default=5000, description="Maximum diff lines to review")
    ignore_patterns: List[str] = Field(
        default_factory=lambda: ["*.lock", "*.min.js", "vendor/**"],
        description="Glob patterns to ignore",
    )


class FixConfig(BaseModel):
    """Configuration for auto-fixing."""

    mode: Literal["safe", "all"] = Field(default="safe", description="Fix mode")
    auto_validate: bool = Field(default=True, description="Auto-validate fixes")
    backup: bool = Field(default=True, description="Backup files before fixing")


class LearnConfig(BaseModel):
    """Configuration for the learning system."""

    enabled: bool = Field(default=True, description="Enable learning")
    max_commits: int = Field(default=500, description="Maximum commits to analyze")
    auto_learn: bool = Field(default=True, description="Auto-learn from reviews")


class OutputConfig(BaseModel):
    """Configuration for output formatting."""

    format: Literal["terminal", "markdown", "json"] = Field(
        default="terminal", description="Output format"
    )
    color: bool = Field(default=True, description="Enable colored output")
    show_scores: bool = Field(default=True, description="Show quality scores")


class SherlockConfig(BaseModel):
    """Root configuration for SherlockCode."""

    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    fix: FixConfig = Field(default_factory=FixConfig)
    learn: LearnConfig = Field(default_factory=LearnConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
