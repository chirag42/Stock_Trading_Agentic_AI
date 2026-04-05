import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from services.data_ingestion import DataIngestionService
from services.data_ingestion.cache import DataCache
from services.data_ingestion.fetcher import MarketDataFetcher
from services.data_ingestion.indicators import IndicatorCalculator
from services.data_ingestion.validator import TickerValidator


def make_mock_df(rows: int = 60, stale_days: int = 0) -> pd.DataFrame:
    end   = datetime.now() - timedelta(days=stale_days)
    dates = pd.date_range(end=end, periods=rows, freq="D")
    close = 150.0 + np.cumsum(np.random.randn(rows))
    return pd.DataFrame({
        "Open":   close * 0.99,
        "High":   close * 1.01,
        "Low":    close * 0.98,
        "Close":  close,
        "Volume": np.random.randint(1_000_000, 5_000_000, size=rows),
    }, index=dates)


@pytest.fixture
def valid_df():
    return make_mock_df(rows=60)

@pytest.fixture
def small_df():
    return make_mock_df(rows=10)

@pytest.fixture
def stale_df():
    return make_mock_df(rows=60, stale_days=10)

@pytest.fixture
def validator():
    return TickerValidator()

@pytest.fixture
def cache():
    return DataCache(ttl_seconds=300)

@pytest.fixture
def fetcher():
    return MarketDataFetcher(max_retries=2, backoff_base=0.01)

@pytest.fixture
def calculator():
    return IndicatorCalculator()

@pytest.fixture
def svc():
    return DataIngestionService(max_retries=2, backoff_base=0.01, cache_ttl=300)