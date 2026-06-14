import pytest
from unittest.mock import patch, MagicMock
from scripts.run_strategy_agent import run
from agents.strategy_agent.exceptions import (
    LLMConnectionError,
    LLMResponseError,
    DecisionParsingError,
)
from services.data_ingestion.exceptions  import DataIngestionError
from services.sentiment_analysis.exceptions import SentimentAnalysisError


def make_market_data():
    return {
        "ticker":      "AAPL",
        "close_price": 182.50,
        "rsi":         28.4,
        "rsi_signal":  "oversold",
        "macd":        0.5,
        "signal":      0.3,
        "macd_signal": "bullish",
        "data_rows":   60,
        "as_of":       "2026-04-10"
    }


def make_sentiment_data():
    return {
        "overall":           "positive",
        "positive":          3,
        "negative":          1,
        "neutral":           1,
        "articles_analyzed": 5,
        "weighted_score":    0.4,
        "avg_confidence":    0.91,
        "breakdown":         []
    }


def make_agent_result(decision="BUY"):
    return {
        "ticker":        "AAPL",
        "decision":      decision,
        "llm_reasoning": f"{decision}\n\nReasons:\n1. RSI oversold.\n2. Positive sentiment.",
        "market_data":   make_market_data(),
        "sentiment":     make_sentiment_data()
    }


@pytest.fixture
def mock_all():
    """Mocks DataIngestionService, SentimentAnalysisService and StrategyAgent."""
    with patch("scripts.run_strategy_agent.DataIngestionService") as mock_data_cls, \
         patch("scripts.run_strategy_agent.SentimentAnalysisService") as mock_sent_cls, \
         patch("scripts.run_strategy_agent.StrategyAgent") as mock_agent_cls:

        data_instance = MagicMock()
        data_instance.get_latest_summary.return_value = make_market_data()
        mock_data_cls.return_value = data_instance

        sent_instance = MagicMock()
        sent_instance.get_aggregated_sentiment.return_value = make_sentiment_data()
        mock_sent_cls.return_value = sent_instance

        agent_instance = MagicMock()
        agent_instance.decide.return_value = make_agent_result("BUY")
        mock_agent_cls.return_value = agent_instance

        yield {
            "data":  data_instance,
            "sent":  sent_instance,
            "agent": agent_instance
        }


class TestRunStrategyAgent:

    def test_returns_result_on_success(self, mock_all):
        result = run("AAPL")
        assert result is not None
        assert result["decision"] == "BUY"

    def test_default_ticker_is_aapl(self, mock_all):
        run()
        mock_all["data"].get_latest_summary.assert_called_once_with("AAPL")

    def test_calls_all_three_services(self, mock_all):
        run("AAPL")
        assert mock_all["data"].get_latest_summary.called
        assert mock_all["sent"].get_aggregated_sentiment.called
        assert mock_all["agent"].decide.called

    def test_sell_decision_returned(self, mock_all):
        mock_all["agent"].decide.return_value = make_agent_result("SELL")
        result = run("AAPL")
        assert result["decision"] == "SELL"

    def test_hold_decision_returned(self, mock_all):
        mock_all["agent"].decide.return_value = make_agent_result("HOLD")
        result = run("AAPL")
        assert result["decision"] == "HOLD"

    def test_returns_none_on_llm_connection_error(self, mock_all, capsys):
        mock_all["agent"].decide.side_effect = LLMConnectionError("Ollama down")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "ollama serve" in captured.out.lower() or "LLM connection" in captured.out

    def test_returns_none_on_llm_response_error(self, mock_all, capsys):
        mock_all["agent"].decide.side_effect = LLMResponseError("Empty response")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "LLM response error" in captured.out

    def test_returns_none_on_decision_parsing_error(self, mock_all, capsys):
        mock_all["agent"].decide.side_effect = DecisionParsingError("Cannot parse")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Could not parse" in captured.out

    def test_returns_none_on_data_ingestion_error(self, mock_all, capsys):
        mock_all["data"].get_latest_summary.side_effect = DataIngestionError("API down")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Market data error" in captured.out

    def test_returns_none_on_sentiment_error(self, mock_all, capsys):
        mock_all["sent"].get_aggregated_sentiment.side_effect = SentimentAnalysisError("No news")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Sentiment error" in captured.out

    def test_output_contains_decision(self, mock_all, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "BUY" in captured.out

    def test_output_contains_reasoning(self, mock_all, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "Reasons" in captured.out

    def test_custom_ticker_passed_correctly(self, mock_all):
        run("TSLA")
        mock_all["data"].get_latest_summary.assert_called_once_with("TSLA")