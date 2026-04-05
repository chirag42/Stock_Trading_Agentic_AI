import logging
from .fetcher     import NewsFetcher
from .classifier  import SentimentClassifier
from .aggregator  import SentimentAggregator

logger = logging.getLogger("SentimentAnalysisService")


class SentimentAnalysisService:

    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.fetcher    = NewsFetcher(max_retries=max_retries, backoff_base=backoff_base)
        self.classifier = SentimentClassifier()
        self.aggregator = SentimentAggregator()

    def get_aggregated_sentiment(self, ticker: str, count: int = 5) -> dict:
        """
        Main entry point.
        Fetches news, classifies each article, returns aggregated sentiment.
        """
        articles = self.fetcher.fetch(ticker, count)

        classified = []
        for article in articles:
            title       = article.get("title", "")
            description = article.get("description", "")
            text        = f"{title}. {description}".strip()

            if not text or text == ".":
                logger.warning(f"Skipping article with no text content.")
                continue

            result = self.classifier.classify(text)
            classified.append({
                "headline":   title,
                "sentiment":  result["label"],
                "confidence": result["score"]
            })

        return self.aggregator.aggregate(ticker, classified)