"""OpenAI API provider implementation."""

from typing import Optional

import httpx

from sherlockcode.providers.base import BaseProvider, ProviderError, RateLimitError


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI API (GPT-4o, GPT-4, etc.)."""

    DEFAULT_ENDPOINT = "https://api.openai.com/v1/chat/completions"

    def _call_api(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Call the OpenAI API with the given prompt."""
        messages = []
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

        if response.status_code == 429:
            raise RateLimitError(
                f"OpenAI rate limit exceeded: {response.text[:300]}"
            )
        if response.status_code >= 500:
            raise RateLimitError(
                f"OpenAI server error ({response.status_code}): {response.text[:300]}"
            )
        if response.status_code != 200:
            raise ProviderError(
                f"OpenAI API error ({response.status_code}): {response.text[:500]}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]
