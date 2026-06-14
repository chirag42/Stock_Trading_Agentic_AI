import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_ingestion     import DataIngestionService, DataIngestionError
from services.sentiment_analysis import SentimentAnalysisService, SentimentAnalysisError
from agents.strategy_agent       import (
    StrategyAgent,
    LLMConnectionError,
    LLMResponseError,
    DecisionParsingError,
)


def run(ticker: str = "AAPL"):
    try:
        print(f"\n--- Strategy Agent ---")
        print(f"Ticker: {ticker}")
        print("-" * 35)

        # Step 1 — market data
        print("Fetching market data...")
        market_data = DataIngestionService().get_latest_summary(ticker)
        print(
            f"  RSI: {market_data['rsi']} ({market_data['rsi_signal']}) | "
            f"MACD: {market_data['macd_signal']}"
        )

        # Step 2 — sentiment
        print("Fetching sentiment...")
        sentiment_data = SentimentAnalysisService().get_aggregated_sentiment(ticker)
        print(f"  Sentiment: {sentiment_data['overall'].upper()}")

        # Step 3 — LLM decision
        print("Querying LLM...")
        agent  = StrategyAgent()
        result = agent.decide(market_data, sentiment_data)

        print(f"\n{'='*40}")
        print(f"  DECISION : *** {result['decision']} ***")
        print(f"{'='*40}")
        print(f"\nReasoning:\n{result['llm_reasoning']}")
        return result

    except LLMConnectionError as e:
        print(f"LLM connection error: {e}")
        print("Make sure Ollama is running: ollama serve")
    except LLMResponseError as e:
        print(f"LLM response error: {e}")
    except DecisionParsingError as e:
        print(f"Could not parse decision: {e}")
    except DataIngestionError as e:
        print(f"Market data error: {e}")
    except SentimentAnalysisError as e:
        print(f"Sentiment error: {e}")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    run(ticker)