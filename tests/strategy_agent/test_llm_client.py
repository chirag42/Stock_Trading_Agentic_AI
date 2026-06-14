import pytest
from unittest.mock import patch, MagicMock
from agents.strategy_agent.llm_client import LLMClient
from agents.strategy_agent.exceptions import LLMConnectionError, LLMResponseError


class TestLLMClient:

    @pytest.fixture
    def client(self):
        return LLMClient(model="llama3.2")

    def test_successful_query_returns_string(self, client):
        with patch("agents.strategy_agent.llm_client.ollama.chat") as mock_chat:
            mock_chat.return_value = {
                "message": {"content": "BUY\n\nReason: Strong momentum."}
            }
            result = client.query("Some prompt")
            assert isinstance(result, str)
            assert "BUY" in result

    def test_empty_prompt_raises(self, client):
        with pytest.raises(LLMResponseError, match="empty prompt"):
            client.query("")

    def test_whitespace_prompt_raises(self, client):
        with pytest.raises(LLMResponseError, match="empty prompt"):
            client.query("   ")

    def test_empty_llm_response_raises(self, client):
        with patch("agents.strategy_agent.llm_client.ollama.chat") as mock_chat:
            mock_chat.return_value = {"message": {"content": ""}}
            with pytest.raises(LLMResponseError, match="empty response"):
                client.query("Some prompt")

    def test_connection_refused_raises(self, client):
        with patch("agents.strategy_agent.llm_client.ollama.chat") as mock_chat:
            mock_chat.side_effect = Exception("connection refused")
            with pytest.raises(LLMConnectionError, match="Ollama"):
                client.query("Some prompt")

    def test_response_is_stripped(self, client):
        with patch("agents.strategy_agent.llm_client.ollama.chat") as mock_chat:
            mock_chat.return_value = {
                "message": {"content": "  BUY\n\nSome reasoning.  "}
            }
            result = client.query("Some prompt")
            assert result == result.strip()

    def test_generic_exception_raises_connection_error(self, client):
        with patch("agents.strategy_agent.llm_client.ollama.chat") as mock_chat:
            mock_chat.side_effect = Exception("something went wrong")
            with pytest.raises(LLMConnectionError):
                client.query("Some prompt")