"""Tests for TradingPipeline.run() — services mocked, no network or model loads."""
import pytest
from unittest.mock import patch, MagicMock
import pipeline as pipeline_mod
from pipeline import TradingPipeline

MARKET = {"close_price": 180.0, "rsi": 28.0, "rsi_signal": "oversold",
          "macd": 0.9, "macd_signal": "bullish"}
SENTIMENT = {"overall": "positive", "positive": 7, "negative": 1,
             "articles_analyzed": 10, "avg_confidence": 0.8}


def _pipe():
    p = TradingPipeline.__new__(TradingPipeline)
    p.data_svc = MagicMock()
    p.sentiment_svc = MagicMock()
    p.fundamentals_fetcher = MagicMock()
    p.agent = MagicMock()
    p.signal_filter = MagicMock()
    p.data_svc.get_latest_summary.return_value = MARKET
    p.sentiment_svc.get_aggregated_sentiment.return_value = SENTIMENT
    return p


class TestRun:
    def test_skip_when_signal_weak(self):
        p = _pipe()
        p.signal_filter.check.return_value = {"triggered": False, "reason": "flat"}
        result = p.run("aapl")
        assert result["decision"] == "SKIP"
        assert result["ticker"] == "AAPL"
        p.agent.decide.assert_not_called()   # LLM never called on skip

    def test_full_path_success(self):
        p = _pipe()
        p.signal_filter.check.return_value = {"triggered": True, "signal_type": "BUY", "reason": "strong"}
        p.fundamentals_fetcher.fetch.return_value = {"sector": "Tech", "revenue_trend": "rising"}
        p.agent.decide.return_value = {"ticker": "AAPL", "decision": "BUY", "llm_reasoning": "Good entry."}
        result = p.run("AAPL")
        assert result["decision"] == "BUY"
        p.agent.decide.assert_called_once()
        # fundamentals block was passed as 3rd arg
        args = p.agent.decide.call_args[0]
        assert "FUNDAMENTALS" in args[2]

    def test_fundamentals_failure_falls_back(self):
        p = _pipe()
        p.signal_filter.check.return_value = {"triggered": True, "signal_type": "BUY", "reason": "strong"}
        p.fundamentals_fetcher.fetch.side_effect = Exception("yf down")
        p.agent.decide.return_value = {"ticker": "AAPL", "decision": "HOLD", "llm_reasoning": "Neutral."}
        result = p.run("AAPL")
        assert result["decision"] == "HOLD"
        # still called the agent with a fallback fundamentals block
        args = p.agent.decide.call_args[0]
        assert "unavailable" in args[2].lower()


class TestInit:
    def test_init_builds_components(self):
        with patch.object(pipeline_mod, "DataIngestionService") as D, \
             patch.object(pipeline_mod, "SentimentAnalysisService") as S, \
             patch.object(pipeline_mod, "FundamentalsFetcher") as F, \
             patch.object(pipeline_mod, "StrategyAgent") as A, \
             patch.object(pipeline_mod, "SignalFilter") as SF:
            p = TradingPipeline(backend="claude")
            assert p.data_svc is D.return_value
            assert p.agent is A.return_value
            SF.assert_called_once()   # created its own signal filter

    def test_init_uses_provided_signal_filter(self):
        provided = MagicMock()
        with patch.object(pipeline_mod, "DataIngestionService"), \
             patch.object(pipeline_mod, "SentimentAnalysisService"), \
             patch.object(pipeline_mod, "FundamentalsFetcher"), \
             patch.object(pipeline_mod, "StrategyAgent"), \
             patch.object(pipeline_mod, "SignalFilter") as SF:
            p = TradingPipeline(signal_filter=provided)
            assert p.signal_filter is provided
            SF.assert_not_called()
