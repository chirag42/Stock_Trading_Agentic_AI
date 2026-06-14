import sys
import os

# Ensures project root is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_ingestion import (
    DataIngestionService,
    InvalidTickerError,
    InsufficientDataError,
    StaleDataError,
    DataIngestionError,
)


def run(ticker: str = "AAPL", period: str = "3mo"):
    svc = DataIngestionService()

    try:
        print(f"\n--- Data Ingestion Service ---")
        print(f"Ticker : {ticker}")
        print(f"Period : {period}")
        print("-" * 35)

        result = svc.get_latest_summary(ticker, period)

        print(f"Price      : ${result['close_price']}")
        print(f"Volume     : {result['volume']:,}")
        print(f"RSI        : {result['rsi']} ({result['rsi_signal']})")
        print(f"MACD       : {result['macd']}")
        print(f"Signal     : {result['signal']} ({result['macd_signal']})")
        print(f"Data rows  : {result['data_rows']}")
        print(f"As of      : {result['as_of']}")
        return result

    except InvalidTickerError as e:
        print(f"Invalid ticker: {e}")
    except InsufficientDataError as e:
        print(f"Not enough data: {e}")
    except StaleDataError as e:
        print(f"Stale data: {e}")
    except DataIngestionError as e:
        print(f"Data ingestion error: {e}")


if __name__ == "__main__":
    # Default ticker is AAPL
    # Pass a ticker as argument: python scripts/run_data_ingestion.py MSFT
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    period = sys.argv[2] if len(sys.argv) > 2 else "3mo"
    run(ticker, period)