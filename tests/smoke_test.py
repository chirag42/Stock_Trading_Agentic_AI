"""
tests/smoke_test.py — Baseline smoke test for the Agentic AI Stock Trading System.

Purpose (CISC 699 Implementation Sprint I):
    Prove the engineering baseline is REAL and RUNNABLE. This test:
      1. Imports every core module in the project (verifies the package wiring).
      2. Exercises the two network-free decision components — SignalFilter and
         RiskValidator — against synthetic inputs, so it runs fully OFFLINE
         (no API keys, no Ollama, no FinBERT model load required).

    It deliberately does NOT call yfinance, Brave Search, or the LLM, so any peer
    can run it immediately after `pip install -r requirements.txt`.

Run from the repository root:
    python tests/smoke_test.py

A successful run ends with:  BASELINE OK
"""

import importlib
import os
import sys
from contextlib import redirect_stdout
from datetime import datetime

# Make the repo root importable when run as `python tests/smoke_test.py`
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# (module_path, symbol) pairs that make up the core pipeline.
CORE_MODULES = [
    ("services.data_ingestion", "DataIngestionService"),
    ("services.data_ingestion", "HistoricalAnalyzer"),
    ("services.sentiment_analysis", "SentimentAnalysisService"),
    ("agents.strategy_agent", "StrategyAgent"),
    ("agents.signal_filter", "SignalFilter"),
    ("agents.risk_validator", "RiskValidator"),
    ("core.scheduler", "Scheduler"),
    ("pipeline", "TradingPipeline"),
]


def phase_imports() -> bool:
    print("\n[1/2] Import check — verifying every core module loads")
    all_ok = True
    for module_path, symbol in CORE_MODULES:
        try:
            mod = importlib.import_module(module_path)
            getattr(mod, symbol)
            print(f"      [PASS] {module_path}.{symbol}")
        except Exception as exc:  # noqa: BLE001
            all_ok = False
            print(f"      [FAIL] {module_path}.{symbol}  ->  "
                  f"{type(exc).__name__}: {exc}")
    return all_ok


def phase_logic() -> bool:
    print("\n[2/2] Offline logic check — real SignalFilter + RiskValidator")
    from agents.signal_filter import SignalFilter
    from agents.risk_validator import RiskValidator

    ok = True
    devnull = open(os.devnull, "w")

    # --- SignalFilter: oversold + bullish MACD should trigger a BUY signal ---
    try:
        sf = SignalFilter()
        market_data = {"ticker": "MSFT", "rsi": 28.0, "macd": 1.2, "signal": 0.8}
        with redirect_stdout(devnull):
            signal = sf.check(market_data)
        assert {"triggered", "signal_type", "reason"}.issubset(signal)
        print(f"      [PASS] SignalFilter.check -> "
              f"triggered={signal['triggered']}, type={signal['signal_type']}")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"      [FAIL] SignalFilter.check -> {type(exc).__name__}: {exc}")

    # --- RiskValidator: a healthy BUY approves; an overbought BUY rejects ---
    try:
        rv = RiskValidator()
        with redirect_stdout(devnull):
            approved = rv.validate_trade("BUY", "MSFT", 372.74, 10000, 54.2)
            rejected = rv.validate_trade("BUY", "AAPL", 210.0, 10000, 82.0)
        assert approved["approved"] is True
        assert rejected["approved"] is False
        print(f"      [PASS] RiskValidator.validate_trade -> "
              f"healthy={approved['status']}, overbought={rejected['status']}")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"      [FAIL] RiskValidator.validate_trade -> "
              f"{type(exc).__name__}: {exc}")

    devnull.close()
    return ok


def main() -> int:
    print("=" * 60)
    print(" AGENTIC AI STOCK TRADING SYSTEM — BASELINE SMOKE TEST")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print("=" * 60)

    imports_ok = phase_imports()
    logic_ok = phase_logic()

    print("\n" + "-" * 60)
    if imports_ok and logic_ok:
        print("BASELINE OK — all core modules import and decision logic runs.")
        print("=" * 60)
        return 0
    print("BASELINE INCOMPLETE — see [FAIL] lines above.")
    print("(If imports fail, run `pip install -r requirements.txt` first.)")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    sys.exit(main())
