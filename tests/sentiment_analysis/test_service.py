import pytest
from services.sentiment_analysis import SentimentAnalysisService
from services.sentiment_analysis.exceptions import (
    NoArticlesFoundError,
    BraveAPIError,
)
from tests.sentiment_analysis.conftest import make_mock_articles


class TestSentimentAnalysisService:

    def test_returns_all_expected_keys(self, svc):
        result = svc.get_aggregated_sentiment("AAPL")
        expected = {
            "ticker", "articles_analyzed", "positive",
            "negative", "neutral", "overall",
            "weighted_score", "avg_confidence", "breakdown"
        }
        assert expected.issubset(result.keys())

    def test_ticker_passed_to_fetcher(self, svc):
        svc.get_aggregated_sentiment("MSFT")
        svc.fetcher.fetch.assert_called_once_with("MSFT", 5)

    def test_classifier_called_per_article(self, svc, mock_articles):
        svc.get_aggregated_sentiment("AAPL")
        assert svc.classifier.classify.call_count == len(mock_articles)

    def test_articles_analyzed_matches_fetched(self, svc, mock_articles):
        result = svc.get_aggregated_sentiment("AAPL")
        assert result["articles_analyzed"] == len(mock_articles)

    def test_all_positive_gives_positive_overall(self, svc):
        svc.classifier.classify.return_value = {"label": "positive", "score": 0.95}
        result = svc.get_aggregated_sentiment("AAPL")
        assert result["overall"] == "positive"

    def test_all_negative_gives_negative_overall(self, svc):
        svc.classifier.classify.return_value = {"label": "negative", "score": 0.88}
        result = svc.get_aggregated_sentiment("AAPL")
        assert result["overall"] == "negative"

    def test_articles_with_no_text_skipped(self, svc):
        svc.fetcher.fetch.return_value = [
            {"title": "",  "description": ""},
            {"title": "Real headline", "description": "Real description."}
        ]
        result = svc.get_aggregated_sentiment("AAPL")
        assert result["articles_analyzed"] == 1

    def test_fetcher_error_propagates(self, svc):
        svc.fetcher.fetch.side_effect = BraveAPIError("API down")
        with pytest.raises(BraveAPIError):
            svc.get_aggregated_sentiment("AAPL")

    def test_no_articles_after_filtering_raises(self, svc):
        svc.fetcher.fetch.return_value = [
            {"title": "", "description": ""},
            {"title": "", "description": ""},
        ]
        with pytest.raises(NoArticlesFoundError):
            svc.get_aggregated_sentiment("AAPL")

    def test_weighted_score_in_result(self, svc):
        result = svc.get_aggregated_sentiment("AAPL")
        assert "weighted_score" in result
        assert -1.0 <= result["weighted_score"] <= 1.0