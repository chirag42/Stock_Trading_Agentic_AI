import pytest
from unittest.mock import patch, MagicMock
from services.sentiment_analysis.fetcher import NewsFetcher
from services.sentiment_analysis.exceptions import (
    BraveAPIError,
    BraveAPIRateLimitError,
    NoArticlesFoundError,
    InvalidTickerError,
)
from tests.sentiment_analysis.conftest import make_mock_articles


class TestNewsFetcher:

    @pytest.fixture
    def fetcher(self):
        with patch.dict("os.environ", {"BRAVE_API_KEY": "test-key"}):
            return NewsFetcher(max_retries=2, backoff_base=0.01)

    def _mock_response(self, status_code: int, articles: list = None):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = {"results": articles or []}
        return mock

    def test_successful_fetch_returns_articles(self, fetcher):
        articles = make_mock_articles(5)
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(200, articles)
            result = fetcher.fetch("AAPL")
            assert isinstance(result, list)
            assert len(result) == 5

    def test_empty_ticker_raises(self, fetcher):
        with pytest.raises(InvalidTickerError):
            fetcher.fetch("")

    def test_whitespace_ticker_raises(self, fetcher):
        with pytest.raises(InvalidTickerError):
            fetcher.fetch("   ")

    def test_rate_limit_raises(self, fetcher):
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(429)
            with pytest.raises(BraveAPIRateLimitError):
                fetcher.fetch("AAPL")

    def test_invalid_api_key_raises(self, fetcher):
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(401)
            with pytest.raises(BraveAPIError, match="Invalid Brave API key"):
                fetcher.fetch("AAPL")

    def test_non_200_status_raises(self, fetcher):
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(500)
            with pytest.raises(BraveAPIError, match="status 500"):
                fetcher.fetch("AAPL")

    def test_empty_results_raises(self, fetcher):
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(200, [])
            with pytest.raises(NoArticlesFoundError):
                fetcher.fetch("AAPL")

    def test_retries_on_transient_error(self, fetcher):
        articles = make_mock_articles(3)
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.side_effect = [
                Exception("Connection reset"),
                self._mock_response(200, articles)
            ]
            result = fetcher.fetch("AAPL")
            assert len(result) == 3

    def test_all_retries_exhausted_raises(self, fetcher):
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.side_effect = Exception("Timeout")
            with pytest.raises(BraveAPIError, match="All .* attempts failed"):
                fetcher.fetch("AAPL")

    def test_rate_limit_not_retried(self, fetcher):
        """Rate limit is deterministic — should raise immediately, no retry."""
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(429)
            with pytest.raises(BraveAPIRateLimitError):
                fetcher.fetch("AAPL")
            assert mock_get.call_count == 1

    def test_missing_api_key_raises_on_init(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(BraveAPIError, match="BRAVE_API_KEY not found"):
                NewsFetcher()

    def test_ticker_normalised_to_uppercase(self, fetcher):
        articles = make_mock_articles(3)
        with patch("services.sentiment_analysis.fetcher.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(200, articles)
            fetcher.fetch("aapl")
            call_params = mock_get.call_args[1]["params"]
            assert "AAPL" in call_params["q"]