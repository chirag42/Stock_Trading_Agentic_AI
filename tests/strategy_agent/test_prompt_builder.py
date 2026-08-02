import pytest
from agents.strategy_agent.prompt_builder import PromptBuilder
from agents.strategy_agent.exceptions import (
    InvalidMarketDataError,
    InvalidSentimentDataError,
)
from tests.strategy_agent.conftest import make_market_data, make_sentiment_data


class TestPromptBuilder:

    def test_builds_prompt_successfully(self, prompt_builder, market_data, sentiment_data):
        result = prompt_builder.build(market_data, sentiment_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_prompt_contains_ticker(self, prompt_builder, market_data, sentiment_data):
        result = prompt_builder.build(market_data, sentiment_data)
        assert "AAPL" in result

    def test_prompt_contains_price(self, prompt_builder, market_data, sentiment_data):
        result = prompt_builder.build(market_data, sentiment_data)
        assert str(market_data["close_price"]) in result

    def test_prompt_contains_rsi(self, prompt_builder, market_data, sentiment_data):
        result = prompt_builder.build(market_data, sentiment_data)
        assert str(market_data["rsi"]) in result

    def test_prompt_contains_sentiment(self, prompt_builder, market_data, sentiment_data):
        result = prompt_builder.build(market_data, sentiment_data)
        assert "POSITIVE" in result

    def test_overbought_hint_included(self, prompt_builder, sentiment_data):
        data = make_market_data(rsi=75.0)
        result = prompt_builder.build(data, sentiment_data)
        assert "overbought" in result

    def test_oversold_hint_included(self, prompt_builder, sentiment_data):
        data = make_market_data(rsi=25.0)
        result = prompt_builder.build(data, sentiment_data)
        assert "oversold" in result

    def test_bullish_hint_included(self, prompt_builder, sentiment_data):
        data = make_market_data(macd=1.0, signal=0.5)
        result = prompt_builder.build(data, sentiment_data)
        assert "bullish" in result

    def test_bearish_hint_included(self, prompt_builder, sentiment_data):
        data = make_market_data(macd=0.5, signal=1.0)
        result = prompt_builder.build(data, sentiment_data)
        assert "bearish" in result

    def test_missing_market_field_raises(self, prompt_builder, sentiment_data):
        bad_data = {"ticker": "AAPL", "close_price": 150.0}
        with pytest.raises(InvalidMarketDataError, match="missing required fields"):
            prompt_builder.build(bad_data, sentiment_data)

    def test_missing_sentiment_field_raises(self, prompt_builder, market_data):
        bad_data = {"overall": "positive"}
        with pytest.raises(InvalidSentimentDataError, match="missing required fields"):
            prompt_builder.build(market_data, bad_data)

    def test_rsi_out_of_range_raises(self, prompt_builder, sentiment_data):
        data = make_market_data(rsi=150.0)
        with pytest.raises(InvalidMarketDataError, match="out of range"):
            prompt_builder.build(data, sentiment_data)

    def test_invalid_sentiment_label_raises(self, prompt_builder, market_data):
        data = make_sentiment_data(overall="unknown")
        with pytest.raises(InvalidSentimentDataError, match="Invalid sentiment label"):
            prompt_builder.build(market_data, data)

    def test_non_numeric_rsi_raises(self, prompt_builder, sentiment_data):
        data = make_market_data()
        data["rsi"] = "high"
        with pytest.raises(InvalidMarketDataError, match="must be a number"):
            prompt_builder.build(data, sentiment_data)

class TestFundamentalsBranch:
    """Covers the optional fundamentals section (lines only hit when a block is passed)."""

    def test_build_includes_fundamentals_block(self, prompt_builder, market_data, sentiment_data):
        block = "FUNDAMENTALS\nSector: Tech\nRevenue trend: rising"
        result = prompt_builder.build(market_data, sentiment_data, fundamentals_block=block)
        assert "FUNDAMENTALS" in result
        assert "Sector: Tech" in result
        # extra handling rule only appears when fundamentals are present
        assert "inform your REASONING" in result

    def test_build_without_fundamentals_omits_block(self, prompt_builder, market_data, sentiment_data):
        result = prompt_builder.build(market_data, sentiment_data)
        assert "FUNDAMENTALS" not in result
