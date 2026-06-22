"""
tests/validate_pipeline.py — Early data & logic validation (Hard Stop 3).

Exercises the REAL data-transformation and decision logic across multiple scenarios,
fully offline (no network, no API keys, no Ollama, no FinBERT load). This validates the
core computational path on controlled, synthetic inputs so the evidence is exact and
reproducible from a clean restart.

Validated:
    A. Input validation   — TickerValidator (services.data_ingestion)
    B. Indicator math     — IndicatorCalculator: RSI/MACD on synthetic prices + edge cases
    C. Signal escalation  — SignalFilter across oversold / overbought / neutral regimes
    D. Risk gating        — RiskValidator approve / reject / emergency-halt scenarios

Run from the repository root:
    python tests/validate_pipeline.py
"""

import os
import sys
from contextlib import redirect_stdout
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import pandas as pd

passes = fails = 0
_devnull = open(os.devnull, "w")


def check(name, condition, detail=""):
    global passes, fails
    if condition:
        passes += 1
        print(f"  [PASS] {name}" + (f"  ->  {detail}" if detail else ""))
    else:
        fails += 1
        print(f"  [FAIL] {name}" + (f"  ->  {detail}" if detail else ""))


def synthetic_prices(trend, n=60, start=100.0, seed=7):
    """Build a deterministic OHLCV frame with a known directional bias and
    realistic day-to-day pullbacks (so RSI lands in a believable range)."""
    rng = np.random.default_rng(seed)
    if trend == "up":
        steps = rng.normal(0.6, 1.2, n)      # net up, with occasional down days
    elif trend == "down":
        steps = rng.normal(-0.6, 1.2, n)     # net down, with occasional up days
    else:
        steps = rng.normal(0.0, 0.4, n)      # flat-ish
    closes = start + np.cumsum(steps)
    return pd.DataFrame({"Close": closes})


# --------------------------------------------------------------------------- #
def phase_a_input_validation():
    print("\n[A] Input validation — TickerValidator")
    from services.data_ingestion.validator import TickerValidator
    from services.data_ingestion.exceptions import InvalidTickerError

    tv = TickerValidator()
    check("normalizes ' msft ' -> 'MSFT'", tv.validate_ticker(" msft ") == "MSFT")

    def rejects(value):
        try:
            tv.validate_ticker(value)
            return False
        except (InvalidTickerError, Exception):
            return True

    check("rejects empty string", rejects(""))
    check("rejects >10 chars", rejects("ABCDEFGHIJK"))
    check("rejects invalid chars", rejects("MS@FT"))
    check("accepts valid period '1mo'", tv.validate_period("1mo") is None)
    try:
        tv.validate_period("7d"); bad = False
    except Exception:
        bad = True
    check("rejects invalid period '7d'", bad)


# --------------------------------------------------------------------------- #
def phase_b_indicators():
    print("\n[B] Indicator math — IndicatorCalculator (RSI / MACD)")
    from services.data_ingestion.indicators import IndicatorCalculator
    from services.data_ingestion.exceptions import InsufficientDataError

    calc = IndicatorCalculator()

    up = calc.calculate(synthetic_prices("up"))
    rsi = up["RSI"].dropna()
    check("RSI bounded within [0, 100]", bool((rsi >= 0).all() and (rsi <= 100).all()),
          f"min={rsi.min():.1f}, max={rsi.max():.1f}")
    check("uptrend RSI skews high (>50)", rsi.iloc[-1] > 50, f"latest RSI={rsi.iloc[-1]:.1f}")
    check("MACD and Signal columns produced", {"MACD", "Signal"}.issubset(up.columns))

    # Edge case: monotonic rises -> RSI must clamp at 100
    rising = pd.DataFrame({"Close": np.arange(100, 160, 1.0)})
    r_rise = calc.calculate(rising)["RSI"].dropna()
    check("all-gains edge case -> RSI = 100", bool((r_rise.tail(5) == 100.0).all()),
          f"tail RSI={r_rise.iloc[-1]:.1f}")

    # Edge case: monotonic falls -> RSI must clamp at 0
    falling = pd.DataFrame({"Close": np.arange(160, 100, -1.0)})
    r_fall = calc.calculate(falling)["RSI"].dropna()
    check("all-losses edge case -> RSI = 0", bool((r_fall.tail(5) == 0.0).all()),
          f"tail RSI={r_fall.iloc[-1]:.1f}")

    # Guard: too few rows must raise
    try:
        calc.calculate(pd.DataFrame({"Close": np.arange(10)})); raised = False
    except InsufficientDataError:
        raised = True
    check("insufficient data raises InsufficientDataError", raised)


# --------------------------------------------------------------------------- #
def phase_c_signal_filter():
    print("\n[C] Signal escalation — SignalFilter")
    from agents.signal_filter import SignalFilter
    sf = SignalFilter()

    with redirect_stdout(_devnull):
        oversold = sf.check({"ticker": "T", "rsi": 25.0, "macd": 1.2, "signal": 0.6})
        overbought = sf.check({"ticker": "T", "rsi": 78.0, "macd": -0.8, "signal": -0.2})
        neutral = sf.check({"ticker": "T", "rsi": 50.0, "macd": 0.1, "signal": 0.1})

    check("oversold + bullish MACD triggers", oversold["triggered"] is True,
          f"type={oversold['signal_type']}")
    check("overbought + bearish MACD triggers", overbought["triggered"] is True,
          f"type={overbought['signal_type']}")
    check("neutral regime does not trigger", neutral["triggered"] is False)


# --------------------------------------------------------------------------- #
def phase_d_risk_validator():
    print("\n[D] Risk gating — RiskValidator")
    from agents.risk_validator import RiskValidator
    rv = RiskValidator()

    with redirect_stdout(_devnull):
        healthy = rv.validate_trade("BUY", "MSFT", 372.74, 10000, 54.2)
        overbought = rv.validate_trade("BUY", "AAPL", 210.0, 10000, 82.0)

    check("healthy BUY approved", healthy["approved"] is True, f"status={healthy['status']}")
    check("overbought BUY rejected", overbought["approved"] is False, f"status={overbought['status']}")

    # Emergency halt overrides everything
    with redirect_stdout(_devnull):
        rv.trigger_emergency_halt()
        halted = rv.validate_trade("BUY", "MSFT", 372.74, 10000, 54.2)
        rv.lift_emergency_halt()
        resumed = rv.validate_trade("BUY", "MSFT", 372.74, 10000, 54.2)
    check("emergency halt blocks all trades", halted["approved"] is False, f"status={halted['status']}")
    check("lifting halt resumes trading", resumed["approved"] is True, f"status={resumed['status']}")


# --------------------------------------------------------------------------- #
def main():
    print("=" * 64)
    print(" PIPELINE DATA & LOGIC VALIDATION — Hard Stop 3")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(" Mode:   offline (synthetic inputs, real module code)")
    print("=" * 64)

    try:
        phase_a_input_validation()
        phase_b_indicators()
        phase_c_signal_filter()
        phase_d_risk_validator()
    finally:
        _devnull.close()

    print("\n" + "-" * 64)
    print(f" SUMMARY: {passes} pass, {fails} fail")
    verdict = "VALIDATION OK" if fails == 0 else "VALIDATION FAILED"
    print(f" {verdict} — core data + decision logic validated on sample input.")
    print("=" * 64)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
