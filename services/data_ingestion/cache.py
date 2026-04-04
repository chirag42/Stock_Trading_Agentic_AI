import hashlib
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger("Cache")

class DataCache:

    def __init__(self, ttl_seconds: int = 300):
        self._store: dict = {}
        self._ttl = ttl_seconds

    def _key(self, ticker: str, period: str) -> str:
        return hashlib.md5(f"{ticker}:{period}".encode()).hexdigest()

    def get(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        key = self._key(ticker, period)
        if key not in self._store:
            return None
        df, expires_at = self._store[key]
        if datetime.now() > expires_at:
            del self._store[key]
            return None
        logger.info(f"Cache hit for {ticker} ({period})")
        return df.copy()

    def set(self, ticker: str, period: str, df: pd.DataFrame) -> None:
        key = self._key(ticker, period)
        expires_at = datetime.now() + timedelta(seconds=self._ttl)
        self._store[key] = (df.copy(), expires_at)

    def invalidate(self, ticker: str, period: str) -> None:
        self._store.pop(self._key(ticker, period), None)

    def clear(self) -> None:
        self._store.clear()