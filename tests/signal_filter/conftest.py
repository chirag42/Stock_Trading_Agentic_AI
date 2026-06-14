import pytest
from unittest.mock import MagicMock
from agents.signal_filter import SignalFilter
from services.data_ingestion import HistoricalAnalyzer


def make_market_data(
    ticker="AAPL", rsi=50.0, macd=0.5, signal=0.3, price=150.0
) -> dict:
    return {
        "ticker":      ticker,
        "close_price": price,
        "rsi":         rsi,
        "macd":        macd,
        "signal":      signal,
        "rsi_signal":  "neutral",
        "macd_signal": "bullish" if macd > signal else "bearish",
    }


def make_baseline(
    oversold=35.0, overbought=65.0, trend="sideways"
) -> dict:
    return {
        "dynamic_oversold":   oversold,
        "dynamic_overbought": overbought,
        "trend":              trend,
    }


@pytest.fixture
def mock_analyzer():
    """Mocked HistoricalAnalyzer — no real API calls."""
    analyzer = MagicMock(spec=HistoricalAnalyzer)
    analyzer.analyze.return_value = make_baseline()
    return analyzer


@pytest.fixture
def signal_filter(mock_analyzer):
    """
    SignalFilter with mocked analyzer and pre-loaded
    AAPL baseline so tests don't need to call initialize().
    """
    sf = SignalFilter()
    sf.analyzer = mock_analyzer
    sf._baselines["AAPL"] = make_baseline()
    return sf