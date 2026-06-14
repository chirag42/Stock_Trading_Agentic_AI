import os
import time
import logging
import requests
import yfinance as yf

from .exceptions import (
    BraveAPIError,
    BraveAPIRateLimitError,
    NoArticlesFoundError,
    InvalidTickerError,
)

logger = logging.getLogger("SentimentFetcher")


class NewsFetcher:

    BRAVE_API_URL = "https://api.search.brave.com/res/v1/news/search"

    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.api_key     = os.getenv("BRAVE_API_KEY")
        self.max_retries = max_retries
        self.backoff_base = backoff_base

        if not self.api_key:
            raise BraveAPIError(
                "BRAVE_API_KEY not found in environment. "
                "Add it to your .env file."
            )

    def fetch(self, ticker: str, count: int = 5) -> list[dict]:
        """
        Fetches news articles for a given ticker from Brave Search API.
        Returns a list of article dicts with title and description.
        Raises BraveAPIError subclasses on failure.
        """
        ticker = ticker.strip().upper()
        if not ticker:
            raise InvalidTickerError("Ticker cannot be empty.")
        
        # Validate ticker is a real stock before calling Brave API
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).history(period="5d")
            if info.empty:
                raise InvalidTickerError(
                    f"'{ticker}' does not appear to be a valid stock ticker."
                )
        except Exception:
            raise InvalidTickerError(
                f"'{ticker}' is not a recognised stock ticker."
            )
        headers = {
            "Accept":              "application/json",
            "Accept-Encoding":     "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q":           f"{ticker} stock news",
            "count":       count,
            "search_lang": "en"
        }

        last_exc = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Fetching news for {ticker} — "
                    f"attempt {attempt}/{self.max_retries}"
                )
                response = requests.get(
                    self.BRAVE_API_URL,
                    headers=headers,
                    params=params,
                    timeout=10
                )

                if response.status_code == 429:
                    raise BraveAPIRateLimitError(
                        "Brave Search API rate limit hit. Try again later."
                    )

                if response.status_code == 401:
                    raise BraveAPIError(
                        "Invalid Brave API key. Check your .env file."
                    )

                if response.status_code != 200:
                    raise BraveAPIError(
                        f"Brave API returned status {response.status_code}"
                    )

                articles = response.json().get("results", [])

                if not articles:
                    raise NoArticlesFoundError(
                        f"No news articles found for '{ticker}'."
                    )

                logger.info(f"Found {len(articles)} articles for {ticker}")
                return articles

            except (BraveAPIRateLimitError, BraveAPIError,
                    NoArticlesFoundError, InvalidTickerError):
                raise  # deterministic — don't retry

            except Exception as exc:
                last_exc = exc
                wait = self.backoff_base ** attempt
                logger.warning(
                    f"Attempt {attempt} failed: {exc}. Retrying in {wait:.1f}s"
                )
                time.sleep(wait)

        raise BraveAPIError(
            f"All {self.max_retries} attempts failed for '{ticker}'. "
            f"Last error: {last_exc}"
        )