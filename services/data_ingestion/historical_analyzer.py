import logging
import pandas as pd
import numpy as np
from .fetcher    import MarketDataFetcher
from .indicators import IndicatorCalculator
from .exceptions import DataIngestionError

logger = logging.getLogger("HistoricalAnalyzer")


class HistoricalAnalyzer:

    # How many std deviations from mean defines oversold/overbought
    STD_MULTIPLIER = 1.5

    # Minimum RSI history needed for meaningful stats
    MIN_RSI_PERIODS = 50

    def __init__(self):
        self.fetcher    = MarketDataFetcher()
        self.calculator = IndicatorCalculator()

    def analyze(self, ticker: str) -> dict:
        """
        Loads 1 year of daily data for a ticker, computes RSI
        and MACD across the full history, and returns dynamic
        thresholds and context for the signal filter.
        """
        logger.info(f"[{ticker}] Running historical analysis...")

        # ── Step 1 — Fetch 1 year of data ─────────────────────
        df = self.fetcher.fetch(ticker, period="1y")
        df = self.calculator.calculate(df)

        # ── Step 2 — RSI statistics ────────────────────────────
        rsi_series = df["RSI"].dropna()

        if len(rsi_series) < self.MIN_RSI_PERIODS:
            raise DataIngestionError(
                f"Not enough RSI data for {ticker} — "
                f"got {len(rsi_series)}, need {self.MIN_RSI_PERIODS}"
            )

        rsi_mean = float(rsi_series.mean())
        rsi_std  = float(rsi_series.std())

        # Dynamic thresholds — statistically meaningful for this stock
        dynamic_oversold   = round(rsi_mean - (self.STD_MULTIPLIER * rsi_std), 2)
        dynamic_overbought = round(rsi_mean + (self.STD_MULTIPLIER * rsi_std), 2)

        # Clamp to valid RSI range
        dynamic_oversold   = max(10.0, dynamic_oversold)
        dynamic_overbought = min(90.0, dynamic_overbought)

        # ── Step 3 — MACD crossover history ───────────────────
        crossovers = self._find_crossovers(df)

        # ── Step 4 — Recent trend context ─────────────────────
        last_30_days   = df.tail(30)
        recent_rsi_avg = round(float(last_30_days["RSI"].dropna().mean()), 2)
        price_30d_ago  = float(last_30_days["Close"].iloc[0])
        price_now      = float(last_30_days["Close"].iloc[-1])
        trend_pct      = round(((price_now - price_30d_ago) / price_30d_ago) * 100, 2)

        if trend_pct > 3:
            trend = "uptrend"
        elif trend_pct < -3:
            trend = "downtrend"
        else:
            trend = "sideways"

        # ── Step 5 — Current RSI position ─────────────────────
        current_rsi = round(float(df["RSI"].iloc[-1]), 2)

        if current_rsi < dynamic_oversold:
            rsi_position = "oversold"
        elif current_rsi > dynamic_overbought:
            rsi_position = "overbought"
        else:
            rsi_position = "neutral"

        result = {
            "ticker":               ticker,
            "period_analyzed":      "1 year",
            "from_date":            str(df.index[0].date()),
            "to_date":              str(df.index[-1].date()),
            "rsi_mean":             round(rsi_mean, 2),
            "rsi_std":              round(rsi_std, 2),
            "dynamic_oversold":     dynamic_oversold,
            "dynamic_overbought":   dynamic_overbought,
            "current_rsi":          current_rsi,
            "rsi_position":         rsi_position,
            "recent_rsi_avg":       recent_rsi_avg,
            "trend":                trend,
            "trend_pct_30d":        trend_pct,
            "crossovers_last_year": len(crossovers),
            "last_crossover":       crossovers[-1] if crossovers else None,
            "data_points":          len(rsi_series),
        }
        
        logger.info(
            f"[{ticker}] Analysis complete — "
            f"oversold < {dynamic_oversold}, "
            f"overbought > {dynamic_overbought}, "
            f"trend: {trend}, "
            f"current RSI position: {rsi_position}"
        )

        return result

    def _find_crossovers(self, df: pd.DataFrame) -> list:
        """
        Finds all MACD crossover events in the history.
        A crossover is where MACD crosses the signal line.
        Returns list of dicts with date and crossover type.
        """
        crossovers = []
        macd   = df["MACD"].values
        signal = df["Signal"].values
        dates  = df.index

        for i in range(1, len(df)):
            prev_diff = macd[i-1] - signal[i-1]
            curr_diff = macd[i]   - signal[i]

            # Bullish crossover — MACD crossed above signal
            if prev_diff <= 0 and curr_diff > 0:
                crossovers.append({
                    "date": str(dates[i].date()),
                    "type": "bullish",
                    "rsi_at_crossover": round(float(df["RSI"].iloc[i]), 2)
                })

            # Bearish crossover — MACD crossed below signal
            elif prev_diff >= 0 and curr_diff < 0:
                crossovers.append({
                    "date": str(dates[i].date()),
                    "type": "bearish",
                    "rsi_at_crossover": round(float(df["RSI"].iloc[i]), 2)
                })

        return crossovers


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    analyzer = HistoricalAnalyzer()
    result   = analyzer.analyze("AAPL")

    # Show date range being analyzed
    print(f"\n--- Historical Analysis ---")
    print(f"  period analyzed : 1 year")
    print(f"  from            : {pd.Timestamp.now() - pd.DateOffset(years=1):%Y-%m-%d}")
    print(f"  to              : {pd.Timestamp.now():%Y-%m-%d}")

    for k, v in result.items():
        if k != "last_crossover":
            print(f"  {k}: {v}")

    if result["last_crossover"]:
        print(f"\n  Last crossover:")
        for k, v in result["last_crossover"].items():
            print(f"    {k}: {v}")