"""Abstract base class for LLM providers."""

import time
from abc import ABC, abstractmethod
from typing import Optional


class ProviderError(Exception):
    """Raised when a provider operation fails."""
    pass


class RateLimitError(ProviderError):
    """Raised when the provider returns a rate-limit response."""
    pass


class BaseProvider(ABC):
    """Abstract base class for all LLM providers."""

    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 1.0  # seconds, doubles each retry

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        endpoint: Optional[str] = None,
    ):
        if not api_key:
            raise ProviderError("API key is required")
        if not model:
            raise ProviderError("Model name is required")
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.endpoint = endpoint

    @abstractmethod
    def _call_api(self, prompt: str, **kwargs) -> str:
        """Call the provider's API. Implemented by subclasses."""
        ...

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response for the given prompt, with retry logic."""
        last_exc: Exception | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return self._call_api(prompt, **kwargs)
            except RateLimitError as e:
                last_exc = e
                wait = self.RETRY_BACKOFF * (2 ** (attempt - 1))
                time.sleep(wait)
            except ProviderError as e:
                # Non-retryable errors (auth, bad request) fail immediately
                last_exc = e
                break

        raise ProviderError(f"All {self.MAX_RETRIES} attempts failed: {last_exc}") from last_exc
