import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sentiment_analysis import (
    SentimentAnalysisService,
    BraveAPIError,
    BraveAPIRateLimitError,
    NoArticlesFoundError,
)


def run(ticker: str = "AAPL", count: int = 5):
    svc = SentimentAnalysisService()

    try:
        print(f"\n--- Sentiment Analysis Service ---")
        print(f"Ticker  : {ticker}")
        print(f"Articles: {count}")
        print("-" * 35)

        result = svc.get_aggregated_sentiment(ticker, count)

        print(f"Overall     : {result['overall'].upper()}")
        print(f"Positive    : {result['positive']}/{result['articles_analyzed']}")
        print(f"Negative    : {result['negative']}/{result['articles_analyzed']}")
        print(f"Neutral     : {result['neutral']}/{result['articles_analyzed']}")
        print(f"Weighted    : {result['weighted_score']}")
        print(f"Confidence  : {result['avg_confidence']}")
        print(f"\nBreakdown:")
        for article in result["breakdown"]:
            print(
                f"  [{article['sentiment'].upper()}] "
                f"({article['confidence']}) "
                f"{article['headline']}"
            )
        return result

    except BraveAPIRateLimitError as e:
        print(f"Rate limit hit: {e}")
    except BraveAPIError as e:
        print(f"Brave API error: {e}")
    except NoArticlesFoundError as e:
        print(f"No articles found: {e}")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    count  = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run(ticker, count)