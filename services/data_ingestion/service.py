import logging
from .validator   import TickerValidator
from .cache       import DataCache
from .fetcher     import MarketDataFetcher
from .indicators  import IndicatorCalculator

logger = logging.getLogger("DataIngestionService")

class DataIngestionService:

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        cache_ttl: int = 300
    ):
        self.validator  = TickerValidator()
        self.cache      = DataCache(ttl_seconds=cache_ttl)
        self.fetcher    = MarketDataFetcher(max_retries, backoff_base)
        self.calculator = IndicatorCalculator()

    def get_latest_summary(
        self, ticker: str, period: str = "3mo"
    ) -> dict:
        ticker = self.validator.validate_ticker(ticker)
        self.validator.validate_period(period)

        df = self.cache.get(ticker, period)
        if df is None:
            df = self.fetcher.fetch(ticker, period)
            self.cache.set(ticker, period, df)

        df     = self.calculator.calculate(df)
        latest = df.iloc[-1]

        rsi  = float(latest["RSI"])
        macd = float(latest["MACD"])
        sig  = float(latest["Signal"])

        return {
            "ticker":      ticker,
            "close_price": round(float(latest["Close"]), 2),
            "volume":      int(latest["Volume"]),
            "rsi":         round(rsi, 2),
            "rsi_signal":  "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
            "macd":        round(macd, 4),
            "signal":      round(sig, 4),
            "macd_signal": "bullish" if macd > sig else "bearish",
            "data_rows":   len(df),
            "as_of":       str(df.index[-1].date())
        }