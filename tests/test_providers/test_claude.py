"""Tests for Claude provider."""

import pytest

from sherlockcode.providers.claude import ClaudeProvider


class TestClaudeProvider:
    def test_initialization(self):
        provider = ClaudeProvider(
            api_key="sk-ant-test",
            model="claude-3-5-sonnet-20241022",
        )
        assert provider.model == "claude-3-5-sonnet-20241022"

    def test_call_api_returns_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "This is a review response"}]
        }
        mocker.patch("httpx.Client.post", return_value=mock_response)

        provider = ClaudeProvider(api_key="sk-ant-test", model="claude-3-5-sonnet")
        result = provider._call_api("Review this code")
        assert result == "This is a review response"

    def test_call_api_handles_error(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mocker.patch("httpx.Client.post", return_value=mock_response)

        provider = ClaudeProvider(api_key="sk-ant-test", model="claude-3-5-sonnet")
        with pytest.raises(Exception) as exc_info:
            provider._call_api("Review this code")
        assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)
