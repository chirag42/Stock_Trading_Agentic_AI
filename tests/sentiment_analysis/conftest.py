import pytest
from unittest.mock import MagicMock
from services.sentiment_analysis import SentimentAnalysisService
from services.sentiment_analysis.fetcher import NewsFetcher
from services.sentiment_analysis.classifier import SentimentClassifier
from services.sentiment_analysis.aggregator import SentimentAggregator


def make_mock_articles(count: int = 5) -> list[dict]:
    """Builds realistic mock Brave API article responses."""
    return [
        {
            "title":       f"Stock news headline {i+1}",
            "description": f"Description of financial news article {i+1}."
        }
        for i in range(count)
    ]


def make_classified_articles(sentiments: list[str]) -> list[dict]:
    """Builds pre-classified article dicts for aggregator tests."""
    return [
        {
            "headline":   f"Headline {i+1}",
            "sentiment":  sentiment,
            "confidence": 0.90
        }
        for i, sentiment in enumerate(sentiments)
    ]


@pytest.fixture
def mock_articles():
    return make_mock_articles(5)


@pytest.fixture
def aggregator():
    return SentimentAggregator()


@pytest.fixture
def mock_classifier():
    """Returns a mocked SentimentClassifier — no FinBERT download needed."""
    classifier = MagicMock(spec=SentimentClassifier)
    classifier.classify.return_value = {"label": "positive", "score": 0.92}
    return classifier


@pytest.fixture
def mock_fetcher(mock_articles):
    """Returns a mocked NewsFetcher — no real API calls."""
    fetcher = MagicMock(spec=NewsFetcher)
    fetcher.fetch.return_value = mock_articles
    return fetcher


@pytest.fixture
def svc(mock_fetcher, mock_classifier):
    """
    Returns a SentimentAnalysisService with fetcher and
    classifier both mocked — safe for unit tests.
    """
    service = SentimentAnalysisService.__new__(SentimentAnalysisService)
    service.fetcher    = mock_fetcher
    service.classifier = mock_classifier
    service.aggregator = SentimentAggregator()
    return service