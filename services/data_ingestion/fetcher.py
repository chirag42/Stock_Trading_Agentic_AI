import time
import logging
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

from .exceptions import (
    InvalidTickerError, InsufficientDataError,
    StaleDataError, DataIngestionError
)

logger = logging.getLogger("Fetcher")

class MarketDataFetcher:

    REQUIRED_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}
    MIN_ROWS         = 35
    MAX_STALE_DAYS   = 5

    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.max_retries  = max_retries
        self.backoff_base = backoff_base

    def fetch(self, ticker: str, period: str) -> pd.DataFrame:
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Fetching {ticker} ({period}) — "
                    f"attempt {attempt}/{self.max_retries}"
                )
                df = yf.Ticker(ticker).history(period=period, timeout=10)

                if df is None or df.empty:
                    raise InvalidTickerError(
                        f"No data for '{ticker}'. Check the ticker symbol."
                    )

                missing = self.REQUIRED_COLUMNS - set(df.columns)
                if missing:
                    raise DataIngestionError(
                        f"API response missing columns: {missing}"
                    )

                df = df.dropna(subset=["Close"])

                if len(df) < self.MIN_ROWS:
                    raise InsufficientDataError(
                        f"Only {len(df)} rows for '{ticker}'. "
                        f"Need {self.MIN_ROWS}. Try a longer period."
                    )

                last_date = df.index[-1]
                if hasattr(last_date, "tzinfo") and last_date.tzinfo:
                    last_date = last_date.tz_localize(None)
                age = (datetime.now() - last_date).days
                if age > self.MAX_STALE_DAYS:
                    raise StaleDataError(
                        f"Data for '{ticker}' is {age} days old."
                    )

                return df

            except (InvalidTickerError, InsufficientDataError,
                    StaleDataError, ValueError):
                raise  # Don't retry deterministic errors

            except Exception as exc:
                last_exc = exc
                wait = self.backoff_base ** attempt
                logger.warning(
                    f"Attempt {attempt} failed: {exc}. Retrying in {wait:.1f}s"
                )
                time.sleep(wait)

        raise DataIngestionError(
            f"All {self.max_retries} attempts failed for '{ticker}'. "
            f"Last error: {last_exc}"
        )