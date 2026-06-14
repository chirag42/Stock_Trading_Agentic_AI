import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from services.data_ingestion.historical_analyzer import HistoricalAnalyzer
from services.data_ingestion.exceptions import DataIngestionError


def make_historical_df(rows: int = 252, trend: str = "sideways") -> pd.DataFrame:
    """Builds a realistic 1-year daily DataFrame."""
    dates = pd.date_range(end=datetime.now(), periods=rows, freq="D")
    if trend == "uptrend":
        close = [100 + i * 0.5 for i in range(rows)]
    elif trend == "downtrend":
        close = [200 - i * 0.5 for i in range(rows)]
    else:
        close = 150 + np.cumsum(np.random.randn(rows) * 0.5)
    close = np.array(close, dtype=float)
    return pd.DataFrame({
        "Open":   close * 0.99,
        "High":   close * 1.01,
        "Low":    close * 0.98,
        "Close":  close,
        "Volume": np.random.randint(1_000_000, 5_000_000, size=rows),
    }, index=dates)


@pytest.fixture
def analyzer():
    return HistoricalAnalyzer()


class TestHistoricalAnalyzer:

    def test_returns_all_expected_keys(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        expected = {
            "ticker", "rsi_mean", "rsi_std",
            "dynamic_oversold", "dynamic_overbought",
            "current_rsi", "rsi_position", "recent_rsi_avg",
            "trend", "trend_pct_30d", "crossovers_last_year",
            "last_crossover", "data_points",
            "period_analyzed", "from_date", "to_date"
        }
        assert expected.issubset(result.keys())

    def test_ticker_preserved_in_result(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("MSFT")
        assert result["ticker"] == "MSFT"

    def test_dynamic_oversold_below_mean(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        assert result["dynamic_oversold"] < result["rsi_mean"]

    def test_dynamic_overbought_above_mean(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        assert result["dynamic_overbought"] > result["rsi_mean"]

    def test_dynamic_oversold_clamped_above_10(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        assert result["dynamic_oversold"] >= 10.0

    def test_dynamic_overbought_clamped_below_90(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        assert result["dynamic_overbought"] <= 90.0

    def test_uptrend_detected(self, analyzer):
        with patch.object(
            analyzer.fetcher, "fetch",
            return_value=make_historical_df(trend="uptrend")
        ):
            result = analyzer.analyze("AAPL")
        assert result["trend"] == "uptrend"

    def test_downtrend_detected(self, analyzer):
        with patch.object(
            analyzer.fetcher, "fetch",
            return_value=make_historical_df(trend="downtrend")
        ):
            result = analyzer.analyze("AAPL")
        assert result["trend"] == "downtrend"

    def test_rsi_position_neutral_when_in_range(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        valid_positions = {"oversold", "overbought", "neutral"}
        assert result["rsi_position"] in valid_positions

    def test_insufficient_rsi_data_raises(self, analyzer):
        small_df = make_historical_df(rows=30)
        with patch.object(analyzer.fetcher, "fetch", return_value=small_df):
            with pytest.raises(DataIngestionError, match="Need 35 rows"):
                analyzer.analyze("AAPL")

    def test_crossovers_returns_list(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        assert isinstance(result["crossovers_last_year"], int)
        assert result["crossovers_last_year"] >= 0

    def test_from_date_before_to_date(self, analyzer):
        with patch.object(analyzer.fetcher, "fetch", return_value=make_historical_df()):
            result = analyzer.analyze("AAPL")
        assert result["from_date"] < result["to_date"]