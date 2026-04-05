import pytest
from services.sentiment_analysis.aggregator import SentimentAggregator
from services.sentiment_analysis.exceptions import NoArticlesFoundError
from tests.sentiment_analysis.conftest import make_classified_articles


class TestSentimentAggregator:

    def test_majority_positive_returns_positive(self, aggregator):
        articles = make_classified_articles(["positive", "positive", "negative"])
        result = aggregator.aggregate("AAPL", articles)
        assert result["overall"] == "positive"

    def test_majority_negative_returns_negative(self, aggregator):
        articles = make_classified_articles(["negative", "negative", "positive"])
        result = aggregator.aggregate("AAPL", articles)
        assert result["overall"] == "negative"

    def test_majority_neutral_returns_neutral(self, aggregator):
        articles = make_classified_articles(["neutral", "neutral", "positive"])
        result = aggregator.aggregate("AAPL", articles)
        assert result["overall"] == "neutral"

    def test_counts_are_correct(self, aggregator):
        articles = make_classified_articles(
            ["positive", "positive", "negative", "neutral"]
        )
        result = aggregator.aggregate("AAPL", articles)
        assert result["positive"] == 2
        assert result["negative"] == 1
        assert result["neutral"]  == 1

    def test_articles_analyzed_matches_input(self, aggregator):
        articles = make_classified_articles(["positive"] * 5)
        result = aggregator.aggregate("AAPL", articles)
        assert result["articles_analyzed"] == 5

    def test_weighted_score_all_positive(self, aggregator):
        articles = make_classified_articles(["positive"] * 4)
        result = aggregator.aggregate("AAPL", articles)
        assert result["weighted_score"] == 1.0

    def test_weighted_score_all_negative(self, aggregator):
        articles = make_classified_articles(["negative"] * 4)
        result = aggregator.aggregate("AAPL", articles)
        assert result["weighted_score"] == -1.0

    def test_weighted_score_mixed(self, aggregator):
        articles = make_classified_articles(
            ["positive", "positive", "negative", "neutral"]
        )
        result = aggregator.aggregate("AAPL", articles)
        # (2 positive - 1 negative) / 4 total = 0.25
        assert result["weighted_score"] == pytest.approx(0.25)

    def test_empty_articles_raises(self, aggregator):
        with pytest.raises(NoArticlesFoundError):
            aggregator.aggregate("AAPL", [])

    def test_ticker_preserved_in_result(self, aggregator):
        articles = make_classified_articles(["positive"])
        result = aggregator.aggregate("MSFT", articles)
        assert result["ticker"] == "MSFT"

    def test_breakdown_included_in_result(self, aggregator):
        articles = make_classified_articles(["positive", "negative"])
        result = aggregator.aggregate("AAPL", articles)
        assert "breakdown" in result
        assert len(result["breakdown"]) == 2

    def test_avg_confidence_calculated(self, aggregator):
        articles = make_classified_articles(["positive", "positive"])
        result = aggregator.aggregate("AAPL", articles)
        assert result["avg_confidence"] == pytest.approx(0.90)