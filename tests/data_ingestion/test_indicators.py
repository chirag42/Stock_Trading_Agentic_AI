import pytest
import numpy as np
from services.data_ingestion.indicators import IndicatorCalculator
from services.data_ingestion.exceptions import InsufficientDataError
from tests.data_ingestion.conftest import make_mock_df


class TestIndicatorCalculator:

    def test_rsi_column_added(self, calculator, valid_df):
        result = calculator.calculate(valid_df)
        assert "RSI" in result.columns

    def test_macd_column_added(self, calculator, valid_df):
        result = calculator.calculate(valid_df)
        assert "MACD" in result.columns

    def test_signal_column_added(self, calculator, valid_df):
        result = calculator.calculate(valid_df)
        assert "Signal" in result.columns

    def test_rsi_within_valid_range(self, calculator, valid_df):
        result = calculator.calculate(valid_df)
        rsi = result["RSI"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    def test_original_df_not_mutated(self, calculator, valid_df):
        original_cols = list(valid_df.columns)
        calculator.calculate(valid_df)
        assert list(valid_df.columns) == original_cols

    def test_insufficient_rows_raises(self, calculator, small_df):
        with pytest.raises(InsufficientDataError):
            calculator.calculate(small_df)

    def test_rsi_100_on_all_gains(self, calculator):
        df = make_mock_df(rows=60)
        df["Close"] = range(100, 160)
        result = calculator.calculate(df)
        assert result["RSI"].dropna().iloc[-1] == pytest.approx(100.0, abs=1.0)

    def test_macd_positive_on_strong_uptrend(self, calculator):
        df = make_mock_df(rows=60)
        df["Close"] = [100 + i * 2 for i in range(60)]
        result = calculator.calculate(df)
        assert result["MACD"].iloc[-1] > 0

    def test_macd_negative_on_strong_downtrend(self, calculator):
        df = make_mock_df(rows=60)
        df["Close"] = [200 - i * 2 for i in range(60)]
        result = calculator.calculate(df)
        assert result["MACD"].iloc[-1] < 0