"""Tests for ClaudeClient — mocks the Anthropic SDK; no real API calls."""
import pytest
from unittest.mock import patch, MagicMock

import agents.strategy_agent.claude_client as cc_mod
from agents.strategy_agent.claude_client import ClaudeClient
from agents.strategy_agent.exceptions import LLMConnectionError, LLMResponseError


def _text_response(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def _make(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch.object(cc_mod.anthropic, "Anthropic") as mock_anthropic:
        inst = MagicMock()
        mock_anthropic.return_value = inst
        client = ClaudeClient()
    return client, inst


class TestInit:
    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(LLMConnectionError):
            ClaudeClient()

    def test_with_key_sets_defaults(self, monkeypatch):
        client, _ = _make(monkeypatch)
        assert client.model == "claude-sonnet-4-6"
        assert client.max_tokens == 512

    def test_custom_model_and_tokens(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        with patch.object(cc_mod.anthropic, "Anthropic"):
            client = ClaudeClient(model="claude-x", max_tokens=99)
        assert client.model == "claude-x"
        assert client.max_tokens == 99


class TestQuery:
    def test_empty_prompt_raises(self, monkeypatch):
        client, _ = _make(monkeypatch)
        with pytest.raises(LLMResponseError):
            client.query("   ")

    def test_success_returns_text(self, monkeypatch):
        client, inst = _make(monkeypatch)
        inst.messages.create.return_value = _text_response("BUY. Strong momentum.")
        assert client.query("analyze AAPL") == "BUY. Strong momentum."

    def test_empty_response_raises(self, monkeypatch):
        client, inst = _make(monkeypatch)
        inst.messages.create.return_value = _text_response("   ")
        with pytest.raises(LLMResponseError):
            client.query("analyze AAPL")

    def test_auth_error_maps_to_connection_error(self, monkeypatch):
        client, inst = _make(monkeypatch)
        class FakeAuth(Exception): pass
        monkeypatch.setattr(cc_mod.anthropic, "AuthenticationError", FakeAuth)
        inst.messages.create.side_effect = FakeAuth("bad key")
        with pytest.raises(LLMConnectionError):
            client.query("hi")

    def test_rate_limit_maps_to_connection_error(self, monkeypatch):
        client, inst = _make(monkeypatch)
        class FakeRate(Exception): pass
        monkeypatch.setattr(cc_mod.anthropic, "RateLimitError", FakeRate)
        inst.messages.create.side_effect = FakeRate("slow down")
        with pytest.raises(LLMConnectionError):
            client.query("hi")

    def test_connection_error_maps_to_connection_error(self, monkeypatch):
        client, inst = _make(monkeypatch)
        class FakeConn(Exception): pass
        monkeypatch.setattr(cc_mod.anthropic, "APIConnectionError", FakeConn)
        inst.messages.create.side_effect = FakeConn("no net")
        with pytest.raises(LLMConnectionError):
            client.query("hi")

    def test_generic_error_maps_to_connection_error(self, monkeypatch):
        client, inst = _make(monkeypatch)
        inst.messages.create.side_effect = ValueError("weird")
        with pytest.raises(LLMConnectionError):
            client.query("hi")
