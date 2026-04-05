import pytest
from unittest.mock import patch
from services.data_ingestion import DataIngestionService, InvalidTickerError
from tests.data_ingestion.conftest import make_mock_df


class TestDataIngestionService:

    def test_returns_all_expected_keys(self, svc, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = svc.get_latest_summary("AAPL")
        expected = {
            "ticker", "close_price", "volume", "rsi",
            "rsi_signal", "macd", "signal", "macd_signal",
            "data_rows", "as_of"
        }
        assert expected.issubset(result.keys())

    def test_ticker_always_uppercase(self, svc, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = svc.get_latest_summary("aapl")
        assert result["ticker"] == "AAPL"

    def test_close_price_is_float(self, svc, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = svc.get_latest_summary("AAPL")
        assert isinstance(result["close_price"], float)

    def test_volume_is_int(self, svc, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = svc.get_latest_summary("AAPL")
        assert isinstance(result["volume"], int)

    def test_second_call_uses_cache(self, svc, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            svc.get_latest_summary("AAPL")
            svc.get_latest_summary("AAPL")
            assert mock.return_value.history.call_count == 1

    def test_rsi_signal_overbought(self, svc):
        df = make_mock_df(rows=60)
        n = len(df)
        df["Close"] = [100 + i * 3 for i in range(n)]
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = df
            result = svc.get_latest_summary("AAPL")
        assert result["rsi_signal"] == "overbought"

    def test_rsi_signal_oversold(self, svc):
        df = make_mock_df(rows=60)
        n = len(df)
        df["Close"] = [200 - i * 3 for i in range(n)]
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = df
            result = svc.get_latest_summary("AAPL")
        assert result["rsi_signal"] == "oversold"

    def test_invalid_ticker_raises(self, svc):
        with pytest.raises(InvalidTickerError):
            svc.get_latest_summary("IN$VALID")
        
    def test_data_rows_matches_df_length(self, svc, valid_df):
        with patch("services.data_ingestion.fetcher.yf.Ticker") as mock:
            mock.return_value.history.return_value = valid_df
            result = svc.get_latest_summary("AAPL")
        assert result["data_rows"] == len(valid_df)  # use actual length

    