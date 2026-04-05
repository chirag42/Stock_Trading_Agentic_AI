import pytest
from services.data_ingestion.cache import DataCache
from tests.data_ingestion.conftest import make_mock_df


class TestDataCache:

    def test_miss_returns_none(self, cache):
        assert cache.get("AAPL", "3mo") is None

    def test_set_then_get_returns_data(self, cache, valid_df):
        cache.set("AAPL", "3mo", valid_df)
        result = cache.get("AAPL", "3mo")
        assert result is not None
        assert len(result) == len(valid_df)

    def test_returns_copy_not_reference(self, cache, valid_df):
        cache.set("AAPL", "3mo", valid_df)
        result = cache.get("AAPL", "3mo")
        result["Close"] = 0
        original = cache.get("AAPL", "3mo")
        assert not (original["Close"] == 0).all()

    def test_expired_entry_returns_none(self):
        cache = DataCache(ttl_seconds=0)
        cache.set("AAPL", "3mo", make_mock_df())
        assert cache.get("AAPL", "3mo") is None

    def test_invalidate_removes_entry(self, cache, valid_df):
        cache.set("AAPL", "3mo", valid_df)
        cache.invalidate("AAPL", "3mo")
        assert cache.get("AAPL", "3mo") is None

    def test_clear_removes_all_entries(self, cache):
        cache.set("AAPL", "3mo", make_mock_df())
        cache.set("MSFT", "1mo", make_mock_df())
        cache.clear()
        assert cache.get("AAPL", "3mo") is None
        assert cache.get("MSFT", "1mo") is None

    def test_different_tickers_dont_collide(self, cache):
        df1 = make_mock_df(rows=40)
        df2 = make_mock_df(rows=50)
        cache.set("AAPL", "3mo", df1)
        cache.set("MSFT", "3mo", df2)
        assert len(cache.get("AAPL", "3mo")) == len(df1)
        assert len(cache.get("MSFT", "3mo")) == len(df2)

    def test_different_periods_dont_collide(self, cache):
        df1 = make_mock_df(rows=40)
        df2 = make_mock_df(rows=50)
        cache.set("AAPL", "1mo", df1)
        cache.set("AAPL", "3mo", df2)
        assert len(cache.get("AAPL", "1mo")) == len(df1)
        assert len(cache.get("AAPL", "3mo")) == len(df2)