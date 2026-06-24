"""Tests for the abstract provider base class."""

import pytest

from sherlockcode.providers.base import BaseProvider, ProviderError


class DummyProvider(BaseProvider):
    def _call_api(self, prompt: str, **kwargs) -> str:
        return "response"


class TestBaseProvider:
    def test_call_api_returns_string(self):
        provider = DummyProvider(api_key="test", model="test")
        result = provider.generate("test prompt")
        assert isinstance(result, str)

    def test_missing_api_key_raises(self):
        with pytest.raises(ProviderError, match="API key is required"):
            DummyProvider(api_key="", model="test")

    def test_missing_model_raises(self):
        with pytest.raises(ProviderError, match="Model name is required"):
            DummyProvider(api_key="test", model="")
