import logging
import pandas as pd
from .exceptions import InsufficientDataError

logger = logging.getLogger("Indicators")

class IndicatorCalculator:

    MIN_ROWS_RSI  = 20
    MIN_ROWS_MACD = 35

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < self.MIN_ROWS_MACD:
            raise InsufficientDataError(
                f"Need {self.MIN_ROWS_MACD} rows for indicators. Got {len(df)}."
            )
        df = df.copy()
        df = self._add_rsi(df)
        df = self._add_macd(df)
        return df

    def _add_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df["Close"].diff()
        gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs    = gain / loss.replace(0, float("nan"))
        rsi   = 100 - (100 / (1 + rs))
        # Handle edge cases: all gains → RSI=100, all losses → RSI=0
        rsi[(loss == 0) & (gain > 0)] = 100.0
        rsi[(gain == 0) & (loss > 0)] = 0.0
        df["RSI"] = rsi
        return df
    

    def _add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        ema12        = df["Close"].ewm(span=12, adjust=False).mean()
        ema26        = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"]   = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        return df