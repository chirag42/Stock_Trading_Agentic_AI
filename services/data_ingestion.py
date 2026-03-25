import yfinance as yf
import pandas as pd

class DataIngestionService:
    
    def fetch_market_data(self, ticker: str, period: str = "3mo"):
        """
        Fetches historical OHLCV data for a given stock ticker.
        period options: 1d, 5d, 1mo, 3mo, 6mo, 1y
        """
        print(f"Fetching market data for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return None
        
        print(f"Got {len(df)} days of data for {ticker}")
        return df

    def calculate_indicators(self, df: pd.DataFrame):
        """
        Calculates RSI and MACD on top of raw OHLCV data.
        """
        # --- RSI (Relative Strength Index) ---
        # Measures if a stock is overbought (>70) or oversold (<30)
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # --- MACD (Moving Average Convergence Divergence) ---
        # Measures trend momentum
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        return df

    def get_latest_summary(self, ticker: str):
        """
        Main method — fetches data, calculates indicators,
        and returns the most recent values as a clean dictionary.
        """
        df = self.fetch_market_data(ticker)
        if df is None:
            return None
        
        df = self.calculate_indicators(df)
        latest = df.iloc[-1]  # most recent row

        summary = {
            "ticker": ticker,
            "close_price": round(latest["Close"], 2),
            "volume": int(latest["Volume"]),
            "rsi": round(latest["RSI"], 2),
            "macd": round(latest["MACD"], 4),
            "signal": round(latest["Signal"], 4),
        }

        return summary


# --- Quick test ---
if __name__ == "__main__":
    service = DataIngestionService()
    result = service.get_latest_summary("MSFT")
    print("\n--- Latest Summary ---")
    for key, value in result.items():
        print(f"{key}: {value}")