import pytest
from unittest.mock import MagicMock
from agents.strategy_agent.prompt_builder import PromptBuilder
from agents.strategy_agent.llm_client     import LLMClient
from agents.strategy_agent.agent          import StrategyAgent


def make_market_data(
    ticker="AAPL", price=150.0, rsi=55.0,
    macd=0.5, signal=0.3
) -> dict:
    return {
        "ticker":      ticker,
        "close_price": price,
        "rsi":         rsi,
        "macd":        macd,
        "signal":      signal,
    }


def make_sentiment_data(
    overall="positive", positive=3,
    negative=1, neutral=1
) -> dict:
    return {
        "overall":           overall,
        "positive":          positive,
        "negative":          negative,
        "neutral":           neutral,
        "articles_analyzed": positive + negative + neutral,
    }


@pytest.fixture
def market_data():
    return make_market_data()


@pytest.fixture
def sentiment_data():
    return make_sentiment_data()


@pytest.fixture
def prompt_builder():
    return PromptBuilder()


@pytest.fixture
def mock_llm():
    client = MagicMock(spec=LLMClient)
    client.query.return_value = "BUY\n\nReasons:\n1. RSI is neutral.\n2. Sentiment is positive."
    return client


@pytest.fixture
def agent(mock_llm):
    a = StrategyAgent.__new__(StrategyAgent)
    a.prompt_builder = PromptBuilder()
    a.llm_client     = mock_llm
    return a