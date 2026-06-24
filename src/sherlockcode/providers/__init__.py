"""LLM provider adapters for SherlockCode."""

from sherlockcode.providers.base import BaseProvider, ProviderError
from sherlockcode.providers.openai import OpenAIProvider
from sherlockcode.providers.claude import ClaudeProvider

__all__ = ["BaseProvider", "ProviderError", "OpenAIProvider", "ClaudeProvider", "create_provider"]

# --- Provider registry ---
_PROVIDERS: dict[str, type[BaseProvider]] = {}


def register(name: str, cls: type[BaseProvider]) -> None:
    """Register a provider class under a given name."""
    _PROVIDERS[name.lower()] = cls


def available_providers() -> list[str]:
    """Return sorted list of registered provider names."""
    return sorted(_PROVIDERS.keys())


def create_provider(name: str, api_key: str, model: str, max_tokens: int = 4096, endpoint: str | None = None) -> BaseProvider:
    """Instantiate a registered provider by name."""
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        raise ProviderError(
            f"Unknown provider '{name}'. Available: {', '.join(available_providers())}"
        )
    return cls(api_key=api_key, model=model, max_tokens=max_tokens, endpoint=endpoint)


# Auto-register built-in providers
register("openai", OpenAIProvider)
register("claude", ClaudeProvider)
register("deepseek", OpenAIProvider)  # DeepSeek is OpenAI-compatible
