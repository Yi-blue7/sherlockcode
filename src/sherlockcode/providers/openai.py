"""OpenAI-compatible API provider implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from sherlockcode.providers.base import BaseProvider, ProviderError, RateLimitError

if TYPE_CHECKING:
    import httpx


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI-compatible APIs (GPT-4, DeepSeek, etc.)."""

    DEFAULT_ENDPOINT = "https://api.openai.com/v1/chat/completions"

    def _call_api(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        """Call the OpenAI-compatible API with the given prompt."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.3,
        }

        endpoint = self.endpoint or self.DEFAULT_ENDPOINT

        with httpx.Client(timeout=60) as client:
            response = client.post(
                endpoint,
                json=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

        self._handle_error(response)
        data = response.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _handle_error(response: "httpx.Response") -> None:
        """Handle API error responses."""
        status = response.status_code
        if status == 429:
            raise RateLimitError(f"Rate limit exceeded: {response.text[:300]}")
        if status >= 500:
            raise RateLimitError(f"Server error ({status}): {response.text[:300]}")
        if status != 200:
            raise ProviderError(f"API error ({status}): {response.text[:500]}")
