import logging
from services.data_ingestion import HistoricalAnalyzer

logger = logging.getLogger("SignalFilter")


class SignalFilter:

    def __init__(self):
        self.analyzer = HistoricalAnalyzer()
        # key: ticker → historical analysis result
        self._baselines:      dict = {}
        # key: ticker → last market_data dict
        self._previous_state: dict = {}

    def initialize(self, tickers: list) -> None:
        """
        Must be called once on startup before polling begins.
        Runs historical analysis for every ticker in the watchlist
        and stores dynamic thresholds as baselines.
        """
        print("\n--- Initializing Signal Filter ---")
        for ticker in tickers:
            try:
                print(f"  Analyzing {ticker} history...")
                baseline = self.analyzer.analyze(ticker)
                self._baselines[ticker] = baseline
                print(
                    f"  [{ticker}] oversold < {baseline['dynamic_oversold']} | "
                    f"overbought > {baseline['dynamic_overbought']} | "
                    f"trend: {baseline['trend']}"
                )
            except Exception as exc:
                logger.error(f"[{ticker}] Historical analysis failed: {exc}")
                # Fall back to default thresholds if analysis fails
                self._baselines[ticker] = {
                    "dynamic_oversold":   35.0,
                    "dynamic_overbought": 65.0,
                    "trend":              "unknown"
                }
        print("--- Initialization complete ---\n")

    def check(self, market_data: dict) -> dict:
        """
        Evaluates whether market conditions are strong enough
        to escalate to the LLM for a decision.
        Uses dynamic thresholds from historical analysis.
        """
        ticker      = market_data["ticker"]
        rsi         = market_data["rsi"]
        macd        = market_data["macd"]
        signal_line = market_data["signal"]

        # Get dynamic thresholds for this ticker
        baseline         = self._baselines.get(ticker, {})
        oversold_thresh  = baseline.get("dynamic_oversold",   35.0)
        overbought_thresh= baseline.get("dynamic_overbought", 65.0)

        # ── First poll for this ticker ─────────────────────────
        if ticker not in self._previous_state:
            logger.info(f"[{ticker}] First live poll — taking state snapshot")
            result = self._check_initial_entry(
                ticker, rsi, macd, signal_line,
                oversold_thresh, overbought_thresh
            )
            self._previous_state[ticker] = market_data
            return result

        # ── Subsequent polls — detect transitions ──────────────
        prev         = self._previous_state[ticker]
        prev_rsi     = prev["rsi"]
        prev_macd    = prev["macd"]
        prev_signal  = prev["signal"]

        result = self._check_transition(
            ticker,
            rsi,       macd,      signal_line,
            prev_rsi,  prev_macd, prev_signal,
            oversold_thresh, overbought_thresh
        )

        self._previous_state[ticker] = market_data
        return result

    def _check_initial_entry(
        self,
        ticker:            str,
        rsi:               float,
        macd:              float,
        signal_line:       float,
        oversold_thresh:   float,
        overbought_thresh: float,
    ) -> dict:
        """
        First-poll logic — uses tighter thresholds (10% inside
        the dynamic boundary) since we have no transition context.
        """
        # Tighter thresholds for initial entry
        # Stock must be more extreme than normal oversold/overbought
        tight_oversold   = oversold_thresh   - (oversold_thresh   * 0.10)
        tight_overbought = overbought_thresh + (overbought_thresh * 0.10)

        if rsi < tight_oversold and macd > signal_line:
            reason = (
                f"Initial entry: RSI {rsi} deeply oversold "
                f"(< {tight_oversold:.1f}, dynamic threshold) "
                f"with bullish MACD"
            )
            logger.info(f"[{ticker}] Initial BUY signal — {reason}")
            return {"triggered": True, "signal_type": "BUY", "reason": reason}

        if rsi > tight_overbought and macd < signal_line:
            reason = (
                f"Initial entry: RSI {rsi} deeply overbought "
                f"(> {tight_overbought:.1f}, dynamic threshold) "
                f"with bearish MACD"
            )
            logger.info(f"[{ticker}] Initial SELL signal — {reason}")
            return {"triggered": True, "signal_type": "SELL", "reason": reason}

        reason = (
            f"First poll baseline set. RSI {rsi} not extreme enough "
            f"for initial entry (need < {tight_oversold:.1f} or "
            f"> {tight_overbought:.1f}) — watching for transitions"
        )
        return {"triggered": False, "signal_type": "NONE", "reason": reason}

    def _check_transition(
        self,
        ticker:            str,
        rsi:               float, macd:        float, signal_line:  float,
        prev_rsi:          float, prev_macd:   float, prev_signal:  float,
        oversold_thresh:   float,
        overbought_thresh: float,
    ) -> dict:
        """
        Transition detection — compares current vs previous state
        using dynamic thresholds.
        """

        # RSI crossed into oversold
        rsi_crossed_oversold = (
            prev_rsi >= oversold_thresh and
            rsi < oversold_thresh
        )

        # RSI crossed into overbought
        rsi_crossed_overbought = (
            prev_rsi <= overbought_thresh and
            rsi > overbought_thresh
        )

        # MACD bullish crossover
        macd_crossed_bullish = (
            prev_macd <= prev_signal and
            macd > signal_line
        )

        # MACD bearish crossover
        macd_crossed_bearish = (
            prev_macd >= prev_signal and
            macd < signal_line
        )

        # BUY — RSI in oversold zone AND MACD bullish
        buy_signal = (
            (rsi_crossed_oversold or rsi < oversold_thresh) and
            (macd_crossed_bullish or macd > signal_line)
        )

        # SELL — RSI in overbought zone AND MACD bearish
        sell_signal = (
            (rsi_crossed_overbought or rsi > overbought_thresh) and
            (macd_crossed_bearish or macd < signal_line)
        )

        if buy_signal:
            reason = (
                f"RSI {prev_rsi:.1f} → {rsi:.1f} "
                f"({'crossed oversold' if rsi_crossed_oversold else 'in oversold zone'} "
                f"threshold {oversold_thresh}), "
                f"MACD {'crossed bullish' if macd_crossed_bullish else 'bullish'}"
            )
            logger.info(f"[{ticker}] BUY transition — {reason}")
            return {"triggered": True, "signal_type": "BUY", "reason": reason}

        if sell_signal:
            reason = (
                f"RSI {prev_rsi:.1f} → {rsi:.1f} "
                f"({'crossed overbought' if rsi_crossed_overbought else 'in overbought zone'} "
                f"threshold {overbought_thresh}), "
                f"MACD {'crossed bearish' if macd_crossed_bearish else 'bearish'}"
            )
            logger.info(f"[{ticker}] SELL transition — {reason}")
            return {"triggered": True, "signal_type": "SELL", "reason": reason}

        reason = (
            f"RSI {rsi:.1f} (oversold < {oversold_thresh}, "
            f"overbought > {overbought_thresh}), "
            f"MACD {macd:.4f} vs Signal {signal_line:.4f} "
            f"— no transition detected"
        )
        return {"triggered": False, "signal_type": "NONE", "reason": reason}

    def reset(self, ticker: str = None) -> None:
        if ticker:
            self._previous_state.pop(ticker, None)
            self._baselines.pop(ticker, None)
            logger.info(f"[{ticker}] State and baseline reset")
        else:
            self._previous_state.clear()
            self._baselines.clear()
            logger.info("All states and baselines reset")