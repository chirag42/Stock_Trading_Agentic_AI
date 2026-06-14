import pytest
from unittest.mock import patch, MagicMock
from scripts.run_data_ingestion import run
from services.data_ingestion.exceptions import (
    InvalidTickerError,
    InsufficientDataError,
    StaleDataError,
    DataIngestionError,
)


def make_market_result(ticker="AAPL"):
    return {
        "ticker":      ticker,
        "close_price": 182.50,
        "volume":      54000000,
        "rsi":         55.2,
        "rsi_signal":  "neutral",
        "macd":        0.8432,
        "signal":      0.6210,
        "macd_signal": "bullish",
        "data_rows":   60,
        "as_of":       "2026-04-10"
    }


@pytest.fixture
def mock_svc():
    with patch("scripts.run_data_ingestion.DataIngestionService") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        instance.get_latest_summary.return_value = make_market_result()
        yield instance


class TestRunDataIngestion:

    def test_returns_result_on_success(self, mock_svc):
        result = run("AAPL")
        assert result is not None
        assert result["ticker"] == "AAPL"

    def test_calls_service_with_ticker(self, mock_svc):
        run("MSFT")
        mock_svc.get_latest_summary.assert_called_once_with("MSFT", "3mo")

    def test_calls_service_with_custom_period(self, mock_svc):
        run("AAPL", "6mo")
        mock_svc.get_latest_summary.assert_called_once_with("AAPL", "6mo")

    def test_returns_none_on_invalid_ticker(self, mock_svc, capsys):
        mock_svc.get_latest_summary.side_effect = InvalidTickerError("Bad ticker")
        result = run("INVALID$$")
        assert result is None
        captured = capsys.readouterr()
        assert "Invalid ticker" in captured.out

    def test_returns_none_on_insufficient_data(self, mock_svc, capsys):
        mock_svc.get_latest_summary.side_effect = InsufficientDataError("Not enough")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Not enough data" in captured.out

    def test_returns_none_on_stale_data(self, mock_svc, capsys):
        mock_svc.get_latest_summary.side_effect = StaleDataError("Too old")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Stale data" in captured.out

    def test_returns_none_on_generic_error(self, mock_svc, capsys):
        mock_svc.get_latest_summary.side_effect = DataIngestionError("Something wrong")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Data ingestion error" in captured.out

    def test_default_ticker_is_aapl(self, mock_svc):
        run()
        mock_svc.get_latest_summary.assert_called_once_with("AAPL", "3mo")

    def test_output_contains_price(self, mock_svc, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "182.5" in captured.out

    def test_output_contains_rsi(self, mock_svc, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "55.2" in captured.out

    def test_output_contains_ticker(self, mock_svc, capsys):
        run("MSFT")
        captured = capsys.readouterr()
        assert "MSFT" in captured.out