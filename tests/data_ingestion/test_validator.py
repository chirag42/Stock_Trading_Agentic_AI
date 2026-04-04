import pytest
from services.data_ingestion.exceptions import InvalidTickerError
from services.data_ingestion.validator import TickerValidator


class TestTickerValidation:

    def test_empty_string_raises(self, validator):
        with pytest.raises(InvalidTickerError, match="cannot be empty"):
            validator.validate_ticker("")

    def test_whitespace_only_raises(self, validator):
        with pytest.raises(InvalidTickerError, match="cannot be empty"):
            validator.validate_ticker("   ")

    def test_too_long_raises(self, validator):
        with pytest.raises(InvalidTickerError, match="too long"):
            validator.validate_ticker("TOOLONGTICKER")

    def test_special_characters_raises(self, validator):
        with pytest.raises(InvalidTickerError, match="invalid characters"):
            validator.validate_ticker("IN$VALID")

    def test_non_string_raises(self, validator):
        with pytest.raises(InvalidTickerError):
            validator.validate_ticker(12345)

    def test_lowercase_normalised_to_uppercase(self, validator):
        assert validator.validate_ticker("aapl") == "AAPL"

    def test_whitespace_stripped(self, validator):
        assert validator.validate_ticker("  MSFT  ") == "MSFT"

    def test_valid_ticker_passes(self, validator):
        assert validator.validate_ticker("AAPL") == "AAPL"

    def test_ticker_with_dot_passes(self, validator):
        # e.g. BRK.B
        assert validator.validate_ticker("BRK.B") == "BRK.B"

    def test_ticker_with_dash_passes(self, validator):
        assert validator.validate_ticker("BF-B") == "BF-B"


class TestPeriodValidation:

    def test_invalid_period_raises(self, validator):
        with pytest.raises(ValueError, match="Invalid period"):
            validator.validate_period("10y")

    def test_all_valid_periods_pass(self, validator):
        for p in ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]:
            validator.validate_period(p)  # should not raise

    def test_empty_period_raises(self, validator):
        with pytest.raises(ValueError):
            validator.validate_period("")