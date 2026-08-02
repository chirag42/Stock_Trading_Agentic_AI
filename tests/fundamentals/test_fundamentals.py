"""Tests for fundamentals — pure helpers plus fetch/_assemble with yfinance mocked."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

import pandas as pd

import services.data_ingestion.fundamentals as f
from services.data_ingestion.fundamentals import (
    FundamentalsFetcher, format_fundamentals_for_prompt,
    _first_row, _trend, _safe, _fmt_money, UNAVAILABLE,
)
from services.data_ingestion.exceptions import DataIngestionError


class TestFirstRow:
    def test_none_df_returns_none(self):
        assert _first_row(None, ["X"]) is None

    def test_empty_df_returns_none(self):
        assert _first_row(pd.DataFrame(), ["X"]) is None

    def test_matching_key_drops_nan(self):
        df = pd.DataFrame([[120, float("nan"), 100]], index=["Total Revenue"])
        assert _first_row(df, ["Total Revenue"]) == [120, 100]

    def test_no_matching_key(self):
        df = pd.DataFrame([[1, 2]], index=["Something Else"])
        assert _first_row(df, ["Total Revenue"]) is None


class TestTrend:
    def test_too_few_values(self):
        assert _trend([100]) == UNAVAILABLE
        assert _trend([]) == UNAVAILABLE

    def test_oldest_zero(self):
        assert _trend([100, 0]) == UNAVAILABLE

    def test_rising(self):
        assert _trend([120, 100]) == "rising"

    def test_declining(self):
        assert _trend([80, 100]) == "declining"

    def test_flat(self):
        assert _trend([101, 100]) == "roughly flat"


class TestSafe:
    def test_returns_value(self):
        assert _safe({"a": 5}, "a") == 5

    def test_missing_returns_none(self):
        assert _safe({}, "a") is None


class TestFmtMoney:
    def test_trillions(self):
        assert _fmt_money(2.5e12) == "$2.5T"

    def test_billions(self):
        assert _fmt_money(3e9) == "$3.0B"

    def test_millions(self):
        assert _fmt_money(4e6) == "$4.0M"

    def test_small_number(self):
        assert _fmt_money(1234) == "$1,234"

    def test_non_number(self):
        assert _fmt_money("unavailable") == "unavailable"


class TestFormatForPrompt:
    def test_empty_data(self):
        out = format_fundamentals_for_prompt({})
        assert "unavailable" in out.lower()

    def test_full_block_contains_fields(self):
        data = {
            "sector": "Technology", "revenue_trend": "rising",
            "net_income_trend": "rising", "net_margin_pct": 25.0,
            "debt_to_equity": 0.5, "cash_on_hand": 5e9,
            "trailing_pe": 30, "price_to_book": 8, "market_cap": 2e12,
            "analyst_target_mean": 220, "next_earnings_date": "2026-08-01",
            "days_to_earnings": 20,
        }
        out = format_fundamentals_for_prompt(data)
        assert "Technology" in out
        assert "rising" in out
        assert "$2.0T" in out

    def test_earnings_elevated_risk_note(self):
        data = {"days_to_earnings": 3, "sector": "X", "net_margin_pct": UNAVAILABLE}
        out = format_fundamentals_for_prompt(data)
        assert "elevated event risk" in out

    def test_earnings_recently_reported(self):
        data = {"days_to_earnings": -2, "sector": "X", "net_margin_pct": UNAVAILABLE}
        out = format_fundamentals_for_prompt(data)
        assert "recently reported" in out

    def test_net_margin_unavailable_branch(self):
        data = {"days_to_earnings": 20, "sector": "X", "net_margin_pct": UNAVAILABLE}
        out = format_fundamentals_for_prompt(data)
        assert "Net margin: unavailable" in out


class TestFetch:
    def test_empty_ticker_raises(self):
        with pytest.raises(DataIngestionError):
            FundamentalsFetcher().fetch("  ")

    def test_fetch_assembles_structured_dict(self):
        qf = pd.DataFrame([[120, 100], [30, 20]],
                          index=["Total Revenue", "Net Income"],
                          columns=["q1", "q0"])
        bs = pd.DataFrame([[50, 60], [200, 180]],
                          index=["Total Debt", "Stockholders Equity"],
                          columns=["q1", "q0"])
        fake_t = MagicMock()
        fake_t.info = {"sector": "Tech", "trailingPE": 30, "priceToBook": 8,
                       "marketCap": 2e12, "targetMeanPrice": 220}
        fake_t.quarterly_financials = qf
        fake_t.quarterly_balance_sheet = bs
        fake_t.calendar = {"Earnings Date": [datetime(2026, 8, 1, tzinfo=timezone.utc)]}

        with patch.object(f.yf, "Ticker", return_value=fake_t):
            data = FundamentalsFetcher().fetch("AAPL")

        assert data["ticker"] == "AAPL"
        assert data["sector"] == "Tech"
        assert data["revenue_trend"] == "rising"
        assert data["debt_to_equity"] == 0.25   # 50/200
        assert data["next_earnings_date"] == "2026-08-01"

    def test_fetch_retries_then_raises_on_total_failure(self):
        with patch.object(f.yf, "Ticker", side_effect=Exception("boom")):
            with patch.object(f.time, "sleep"):   # don't actually sleep
                with pytest.raises(DataIngestionError):
                    FundamentalsFetcher(max_retries=2, backoff_base=0.01).fetch("AAPL")


class TestEarningsTiming:
    def test_no_calendar_returns_none(self):
        fake_t = MagicMock()
        fake_t.calendar = {}
        result = FundamentalsFetcher()._earnings_timing(fake_t)
        assert result == (None, None)

    def test_datetime_calendar_returns_days(self):
        fake_t = MagicMock()
        future = datetime.now(timezone.utc) + timedelta(days=10)
        fake_t.calendar = {"Earnings Date": [future]}
        iso, days = FundamentalsFetcher()._earnings_timing(fake_t)
        assert iso is not None
        assert isinstance(days, int)
