"""Tests for OpenAI provider."""

import json

import pytest

from sherlockcode.providers.openai import OpenAIProvider


class TestOpenAIProvider:
    def test_initialization(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        assert provider.api_key == "sk-test"
        assert provider.model == "gpt-4o"

    def test_call_api_returns_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is a review response"}}]
        }
        mocker.patch("httpx.Client.post", return_value=mock_response)

        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        result = provider._call_api("Review this code")
        assert result == "This is a review response"

    def test_call_api_handles_error(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mocker.patch("httpx.Client.post", return_value=mock_response)

        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        with pytest.raises(Exception) as exc_info:
            provider._call_api("Review this code")
        assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)
