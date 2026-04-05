import logging
from .exceptions import NoArticlesFoundError

logger = logging.getLogger("SentimentAggregator")


class SentimentAggregator:

    def aggregate(self, ticker: str, classified_articles: list[dict]) -> dict:
        """
        Takes a list of classified articles and produces
        an aggregated sentiment summary for the ticker.
        """
        if not classified_articles:
            raise NoArticlesFoundError(
                f"No classified articles to aggregate for '{ticker}'."
            )

        labels = [a["sentiment"] for a in classified_articles]

        positive = labels.count("positive")
        negative = labels.count("negative")
        neutral  = labels.count("neutral")
        total    = len(labels)

        # Weighted score: positive = +1, negative = -1, neutral = 0
        weighted_score = round((positive - negative) / total, 4)

        # Overall = majority vote
        overall = max(["positive", "negative", "neutral"], key=labels.count)

        # Confidence = average score of articles matching overall label
        matching = [
            a["confidence"] for a in classified_articles
            if a["sentiment"] == overall
        ]
        avg_confidence = round(sum(matching) / len(matching), 4) if matching else 0.0

        return {
            "ticker":          ticker,
            "articles_analyzed": total,
            "positive":        positive,
            "negative":        negative,
            "neutral":         neutral,
            "overall":         overall,
            "weighted_score":  weighted_score,
            "avg_confidence":  avg_confidence,
            "breakdown":       classified_articles
        }