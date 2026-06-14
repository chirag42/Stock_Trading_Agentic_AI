import pytest
from agents.strategy_agent.agent import StrategyAgent
from agents.strategy_agent.exceptions import (
    DecisionParsingError,
    InvalidMarketDataError,
    LLMConnectionError,
)
from tests.strategy_agent.conftest import make_market_data, make_sentiment_data


class TestStrategyAgent:

    def test_buy_decision_parsed(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = "BUY\n\nReasons: Strong RSI signal."
        result = agent.decide(market_data, sentiment_data)
        assert result["decision"] == "BUY"

    def test_sell_decision_parsed(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = "SELL\n\nReasons: Overbought conditions."
        result = agent.decide(market_data, sentiment_data)
        assert result["decision"] == "SELL"

    def test_hold_decision_parsed(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = "HOLD\n\nReasons: Mixed signals."
        result = agent.decide(market_data, sentiment_data)
        assert result["decision"] == "HOLD"

    def test_decision_case_insensitive(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = "buy\n\nReasons: Good momentum."
        result = agent.decide(market_data, sentiment_data)
        assert result["decision"] == "BUY"

    def test_decision_with_punctuation_parsed(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = "BUY.\n\nReasons: RSI oversold."
        result = agent.decide(market_data, sentiment_data)
        assert result["decision"] == "BUY"

    def test_decision_not_in_first_word_fallback(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = (
            "Based on analysis, the recommendation is HOLD."
        )
        result = agent.decide(market_data, sentiment_data)
        assert result["decision"] == "HOLD"

    def test_unparseable_response_raises(self, agent, market_data, sentiment_data):
        agent.llm_client.query.return_value = "I cannot determine the answer."
        with pytest.raises(DecisionParsingError):
            agent.decide(market_data, sentiment_data)

    def test_result_contains_expected_keys(self, agent, market_data, sentiment_data):
        result = agent.decide(market_data, sentiment_data)
        expected = {"ticker", "decision", "llm_reasoning", "market_data", "sentiment"}
        assert expected.issubset(result.keys())

    def test_ticker_in_result(self, agent, market_data, sentiment_data):
        result = agent.decide(market_data, sentiment_data)
        assert result["ticker"] == "AAPL"

    def test_llm_reasoning_included(self, agent, market_data, sentiment_data):
        result = agent.decide(market_data, sentiment_data)
        assert "BUY" in result["llm_reasoning"]

    def test_missing_market_data_raises(self, agent, sentiment_data):
        with pytest.raises(InvalidMarketDataError):
            agent.decide({"ticker": "AAPL"}, sentiment_data)

    def test_llm_failure_propagates(self, agent, market_data, sentiment_data):
        agent.llm_client.query.side_effect = LLMConnectionError("Ollama down")
        with pytest.raises(LLMConnectionError):
            agent.decide(market_data, sentiment_data)

    def test_sentiment_summary_in_result(self, agent, market_data, sentiment_data):
        result = agent.decide(market_data, sentiment_data)
        assert result["sentiment"]["overall"] == "positive"
        assert result["sentiment"]["positive"] == 3