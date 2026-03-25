import requests
import os
from dotenv import load_dotenv
from transformers import pipeline

load_dotenv()  # loads your .env file

class SentimentAnalysisService:

    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        print("Loading FinBERT model... (first time takes a minute)")
        self.classifier = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            top_k=1
        )
        print("FinBERT ready!")

    def fetch_news(self, ticker: str, count: int = 5):
        """
        Calls Brave Search API to get recent news about a stock ticker.
        """
        print(f"Fetching news for {ticker}...")
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": f"{ticker} stock news",
            "count": count,
            "search_lang": "en"
        }
        response = requests.get(
            "https://api.search.brave.com/res/v1/news/search",
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            print(f"Brave API error: {response.status_code}")
            return []

        data = response.json()
        articles = data.get("results", [])
        print(f"Found {len(articles)} news articles")
        return articles

    def analyze_sentiment(self, text: str):
        """
        Runs FinBERT on a piece of text.
        Returns: positive / negative / neutral + confidence score
        """
        result = self.classifier(text[:512])[0][0]  # limit to 512 chars
        return {
            "label": result["label"],
            "score": round(result["score"], 4)
        }

    def get_aggregated_sentiment(self, ticker: str):
        """
        Main method — fetches news, runs FinBERT on each headline,
        and returns an overall sentiment summary.
        """
        articles = self.fetch_news(ticker)
        if not articles:
            return None

        results = []
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title}. {description}"

            sentiment = self.analyze_sentiment(text)
            results.append({
                "headline": title,
                "sentiment": sentiment["label"],
                "confidence": sentiment["score"]
            })

        # Count positives, negatives, neutrals
        labels = [r["sentiment"] for r in results]
        summary = {
            "ticker": ticker,
            "articles_analyzed": len(results),
            "positive": labels.count("positive"),
            "negative": labels.count("negative"),
            "neutral": labels.count("neutral"),
            "overall": max(set(labels), key=labels.count),  # majority vote
            "breakdown": results
        }

        return summary


# --- Quick test ---
if __name__ == "__main__":
    service = SentimentAnalysisService()
    result = service.get_aggregated_sentiment("MSFT")

    print("\n--- Sentiment Summary ---")
    print(f"Ticker: {result['ticker']}")
    print(f"Articles Analyzed: {result['articles_analyzed']}")
    print(f"Positive: {result['positive']}")
    print(f"Negative: {result['negative']}")
    print(f"Neutral: {result['neutral']}")
    print(f"Overall Sentiment: {result['overall'].upper()}")
    print("\n--- Breakdown ---")
    for item in result["breakdown"]:
        print(f"[{item['sentiment'].upper()}] {item['headline']}")