import pytest
import pandas as pd
from unittest.mock import patch
from services.data_ingestion.fetcher import MarketDataFetcher
from services.data_ingestion.exceptions import (
    InvalidTickerError, InsufficientDataError,
    StaleDataError, DataIngestionError
)
from tests.data_ingestion.conftest import make_mock_df


class TestMarketDataFetcher:

    def test_successful_fetch_returns_dataframe(self, fetcher, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = fetcher.fetch("AAPL", "3mo")
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(valid_df)  # use actual length

    def test_empty_response_raises_invalid_ticker(self, fetcher):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = pd.DataFrame()
            with pytest.raises(InvalidTickerError):
                fetcher.fetch("FAKE", "3mo")

    def test_none_response_raises_invalid_ticker(self, fetcher):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = None
            with pytest.raises(InvalidTickerError):
                fetcher.fetch("FAKE", "3mo")

    def test_insufficient_rows_raises(self, fetcher, small_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = small_df
            with pytest.raises(InsufficientDataError):
                fetcher.fetch("AAPL", "3mo")

    def test_stale_data_raises(self, fetcher, stale_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = stale_df
            with pytest.raises(StaleDataError):
                fetcher.fetch("AAPL", "3mo")

    def test_missing_columns_raises(self, fetcher, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df.drop(columns=["Volume"])
            with pytest.raises(DataIngestionError, match="missing columns"):
                fetcher.fetch("AAPL", "3mo")

    def test_nan_close_rows_dropped(self, fetcher, valid_df):
        valid_df.iloc[5, valid_df.columns.get_loc("Close")] = float("nan")
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = fetcher.fetch("AAPL", "3mo")
            assert result["Close"].isna().sum() == 0

    def test_retries_on_transient_error(self, fetcher, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.side_effect = [
                Exception("Timeout"),  # only 1 failure — fetcher has max_retries=2
                valid_df
            ]
            result = fetcher.fetch("AAPL", "3mo")
            assert result is not None

    def test_all_retries_exhausted_raises(self, fetcher):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.side_effect = Exception("Connection refused")
            with pytest.raises(DataIngestionError, match="All .* attempts failed"):
                fetcher.fetch("AAPL", "3mo")

    def test_deterministic_error_not_retried(self, fetcher):
        """InvalidTickerError should raise immediately — no retry."""
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = pd.DataFrame()
            with pytest.raises(InvalidTickerError):
                fetcher.fetch("FAKE", "3mo")
            assert mock.return_value.history.call_count == 1