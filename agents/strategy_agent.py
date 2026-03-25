import ollama
from services.data_ingestion import DataIngestionService
from services.sentiment_analysis import SentimentAnalysisService

class StrategyAgent:

    def __init__(self):
        self.data_service = DataIngestionService()
        self.sentiment_service = SentimentAnalysisService()
        self.model = "llama3.2"

    def build_prompt(self, market_data: dict, sentiment_data: dict) -> str:
        """
        Builds a structured prompt for the LLM combining
        technical indicators and sentiment analysis.
        """
        rsi = market_data["rsi"]
        macd = market_data["macd"]
        signal = market_data["signal"]
        price = market_data["close_price"]
        ticker = market_data["ticker"]

        overall_sentiment = sentiment_data["overall"]
        positive = sentiment_data["positive"]
        negative = sentiment_data["negative"]
        neutral = sentiment_data["neutral"]
        total = sentiment_data["articles_analyzed"]

        # RSI interpretation hint
        if rsi > 70:
            rsi_hint = "overbought — potential sell signal"
        elif rsi < 30:
            rsi_hint = "oversold — potential buy signal"
        else:
            rsi_hint = "neutral range"

        # MACD interpretation hint
        macd_hint = "bullish crossover" if macd > signal else "bearish crossover"

        prompt = f"""
        You are a financial analysis AI assistant. Analyze the following data for {ticker} stock and make a trading decision.

        --- TECHNICAL INDICATORS ---
        Current Price: ${price}
        RSI: {rsi} ({rsi_hint})
        MACD: {macd} ({macd_hint})
        Signal Line: {signal}

        --- MARKET SENTIMENT ---
        Overall Sentiment: {overall_sentiment.upper()}
        Positive Articles: {positive}/{total}
        Negative Articles: {negative}/{total}
        Neutral Articles: {neutral}/{total}

        --- YOUR TASK ---
        Based on the technical indicators and market sentiment above:
        1. Give a clear decision: BUY, SELL, or HOLD
        2. Give 2-3 short reasons for your decision
        3. Mention any risks

        Keep your response concise and structured. Start with the decision on the first line.
        """
        return prompt

    def decide(self, ticker: str) -> dict:
        """
        Main method — fetches all data, builds prompt,
        queries Ollama, and returns the trading decision.
        """
        print(f"\nRunning Strategy Agent for {ticker}...")

        # Step 1 — Get market data
        print("Step 1: Fetching market data...")
        market_data = self.data_service.get_latest_summary(ticker)
        if not market_data:
            return {"error": f"Could not fetch market data for {ticker}"}

        # Step 2 — Get sentiment data
        print("Step 2: Analyzing sentiment...")
        sentiment_data = self.sentiment_service.get_aggregated_sentiment(ticker)
        if not sentiment_data:
            return {"error": f"Could not fetch sentiment data for {ticker}"}

        # Step 3 — Build prompt
        print("Step 3: Building prompt...")
        prompt = self.build_prompt(market_data, sentiment_data)

        # Step 4 — Query local LLM
        print("Step 4: Querying Ollama (llama3.2)...")
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analysis assistant. Be concise, structured, and data-driven."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        llm_response = response["message"]["content"]

        # Step 5 — Package result
        result = {
            "ticker": ticker,
            "market_data": market_data,
            "sentiment": {
                "overall": sentiment_data["overall"],
                "positive": sentiment_data["positive"],
                "negative": sentiment_data["negative"],
                "neutral": sentiment_data["neutral"],
            },
            "llm_decision": llm_response
        }

        return result


# --- Quick test ---
if __name__ == "__main__":
    agent = StrategyAgent()
    result = agent.decide("MSFT")

    print("\n" + "="*50)
    print("STRATEGY AGENT DECISION")
    print("="*50)
    print(f"Ticker: {result['ticker']}")
    print(f"Price: ${result['market_data']['close_price']}")
    print(f"RSI: {result['market_data']['rsi']}")
    print(f"Sentiment: {result['sentiment']['overall'].upper()}")
    print("\n--- LLM Reasoning ---")
    print(result["llm_decision"])