import pytest
from unittest.mock import patch, MagicMock
from scripts.run_sentiment_analysis import run
from services.sentiment_analysis.exceptions import (
    BraveAPIError,
    BraveAPIRateLimitError,
    NoArticlesFoundError,
)


def make_sentiment_result(overall="positive"):
    return {
        "ticker":              "AAPL",
        "overall":             overall,
        "positive":            3,
        "negative":            1,
        "neutral":             1,
        "articles_analyzed":   5,
        "weighted_score":      0.4,
        "avg_confidence":      0.91,
        "breakdown": [
            {"headline": "Stock rises", "sentiment": "positive", "confidence": 0.95},
            {"headline": "Market falls", "sentiment": "negative", "confidence": 0.88},
        ]
    }


@pytest.fixture
def mock_svc():
    with patch("scripts.run_sentiment_analysis.SentimentAnalysisService") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        instance.get_aggregated_sentiment.return_value = make_sentiment_result()
        yield instance


class TestRunSentimentAnalysis:

    def test_returns_result_on_success(self, mock_svc):
        result = run("AAPL")
        assert result is not None
        assert result["overall"] == "positive"

    def test_calls_service_with_ticker_and_count(self, mock_svc):
        run("MSFT", 7)
        mock_svc.get_aggregated_sentiment.assert_called_once_with("MSFT", 7)

    def test_default_ticker_is_aapl(self, mock_svc):
        run()
        mock_svc.get_aggregated_sentiment.assert_called_once_with("AAPL", 5)

    def test_returns_none_on_rate_limit(self, mock_svc, capsys):
        mock_svc.get_aggregated_sentiment.side_effect = BraveAPIRateLimitError("Rate limit")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Rate limit" in captured.out

    def test_returns_none_on_api_error(self, mock_svc, capsys):
        mock_svc.get_aggregated_sentiment.side_effect = BraveAPIError("API down")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "Brave API error" in captured.out

    def test_returns_none_on_no_articles(self, mock_svc, capsys):
        mock_svc.get_aggregated_sentiment.side_effect = NoArticlesFoundError("No news")
        result = run("AAPL")
        assert result is None
        captured = capsys.readouterr()
        assert "No articles found" in captured.out

    def test_output_contains_overall_sentiment(self, mock_svc, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "POSITIVE" in captured.out

    def test_output_contains_breakdown(self, mock_svc, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "Stock rises" in captured.out

    def test_output_contains_weighted_score(self, mock_svc, capsys):
        run("AAPL")
        captured = capsys.readouterr()
        assert "0.4" in captured.out

    def test_negative_sentiment_output(self, mock_svc, capsys):
        mock_svc.get_aggregated_sentiment.return_value = make_sentiment_result("negative")
        run("AAPL")
        captured = capsys.readouterr()
        assert "NEGATIVE" in captured.out