"""Claude (Anthropic) API provider implementation."""

from typing import Optional

import httpx

from sherlockcode.providers.base import BaseProvider, ProviderError, RateLimitError


class ClaudeProvider(BaseProvider):
    """Provider for Anthropic Claude API."""

    DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION = "2023-06-01"

    def _call_api(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Call the Anthropic API with the given prompt."""
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt

        endpoint = self.endpoint or self.DEFAULT_ENDPOINT

        with httpx.Client(timeout=60) as client:
            response = client.post(
                endpoint,
                json=body,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.ANTHROPIC_VERSION,
                    "Content-Type": "application/json",
                },
            )

        if response.status_code == 429:
            raise RateLimitError(
                f"Claude rate limit exceeded: {response.text[:300]}"
            )
        if response.status_code >= 500:
            raise RateLimitError(
                f"Claude server error ({response.status_code}): {response.text[:300]}"
            )
        if response.status_code != 200:
            raise ProviderError(
                f"Claude API error ({response.status_code}): {response.text[:500]}"
            )

        data = response.json()
        return data["content"][0]["text"]
