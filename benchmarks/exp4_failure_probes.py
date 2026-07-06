"""
benchmarks/exp4_failure_probes.py — Experiment 4 (Hard Stop 4).

TECHNICAL QUESTION
    Does the system fail safely? When inputs are malformed, the LLM output is unusable, or
    the LLM runtime is unavailable, does the code raise the correct, typed exceptions rather
    than crashing or returning silent garbage?

METHOD
    Inject controlled failures and assert the expected exception type is raised:
      P1  malformed market data (missing field)   -> InvalidMarketDataError
      P2  out-of-range RSI (>100)                  -> InvalidMarketDataError
      P3  malformed sentiment (bad label)          -> InvalidSentimentDataError
      P4  empty prompt to the LLM client           -> LLMResponseError
      P5  unparseable LLM response text            -> DecisionParsingError
      P6  Ollama runtime unavailable               -> LLMConnectionError

    P1-P5 are fully offline. P6 requires Ollama to be STOPPED to observe the real
    connection error (or it is reported as INFO if Ollama happens to be running).

USAGE
    python benchmarks/exp4_failure_probes.py

Results are written to benchmarks/results/exp4_failure_probes.json
"""

import json
import os
import platform
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agents.strategy_agent import (
    StrategyAgent, LLMConnectionError, LLMResponseError,
    InvalidMarketDataError, InvalidSentimentDataError, DecisionParsingError,
)
from agents.strategy_agent.prompt_builder import PromptBuilder
from agents.strategy_agent.llm_client import LLMClient

GOOD_MARKET = {"ticker": "T", "close_price": 100.0, "rsi": 28.0, "macd": 0.9, "signal": 0.4}
GOOD_SENT = {"overall": "positive", "positive": 7, "negative": 1, "neutral": 2, "articles_analyzed": 10}

results = []


def probe(pid, desc, expected_exc, fn):
    try:
        fn()
        results.append({"id": pid, "desc": desc, "expected": expected_exc.__name__,
                        "observed": "no exception", "pass": False})
        print(f"  [FAIL] {pid}: expected {expected_exc.__name__}, none raised — {desc}")
    except expected_exc as exc:
        results.append({"id": pid, "desc": desc, "expected": expected_exc.__name__,
                        "observed": type(exc).__name__, "pass": True})
        print(f"  [PASS] {pid}: {expected_exc.__name__} raised — {desc}")
    except Exception as exc:  # noqa: BLE001
        results.append({"id": pid, "desc": desc, "expected": expected_exc.__name__,
                        "observed": type(exc).__name__, "pass": False})
        print(f"  [FAIL] {pid}: expected {expected_exc.__name__}, got {type(exc).__name__} — {desc}")


def main():
    print("=" * 64)
    print(" EXPERIMENT 4 — FAILURE-CASE PROBES (error handling)")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(f" Env: Python {platform.python_version()} on {platform.system()} {platform.machine()}")
    print("=" * 64)

    pb = PromptBuilder()
    agent = StrategyAgent()

    # P1: missing market field
    probe("P1", "market data missing 'macd'", InvalidMarketDataError,
          lambda: pb.validate_market_data({k: v for k, v in GOOD_MARKET.items() if k != "macd"}))
    # P2: RSI out of range
    probe("P2", "RSI = 142 (out of range)", InvalidMarketDataError,
          lambda: pb.validate_market_data({**GOOD_MARKET, "rsi": 142}))
    # P3: bad sentiment label
    probe("P3", "sentiment label 'euphoric'", InvalidSentimentDataError,
          lambda: pb.validate_sentiment_data({**GOOD_SENT, "overall": "euphoric"}))
    # P4: empty prompt
    probe("P4", "empty prompt to LLM client", LLMResponseError,
          lambda: LLMClient().query("   "))
    # P5: unparseable decision text
    probe("P5", "unparseable LLM response", DecisionParsingError,
          lambda: agent._parse_decision("The market is quite uncertain today."))

    # P6: Ollama unavailable — only a true PASS if Ollama is actually stopped
    print("\n  P6 (Ollama-down) — stop Ollama to observe LLMConnectionError:")
    try:
        LLMClient().query("Say BUY.")
        results.append({"id": "P6", "desc": "Ollama unavailable", "expected": "LLMConnectionError",
                        "observed": "Ollama is running", "pass": None})
        print("  [INFO] P6: Ollama is running — connection succeeded; stop Ollama to test this path")
    except LLMConnectionError:
        results.append({"id": "P6", "desc": "Ollama unavailable", "expected": "LLMConnectionError",
                        "observed": "LLMConnectionError", "pass": True})
        print("  [PASS] P6: LLMConnectionError raised — Ollama unavailable handled cleanly")

    scored = [r for r in results if r["pass"] is not None]
    passed = sum(1 for r in scored if r["pass"])
    print("\n" + "-" * 64)
    print(f" SUMMARY: {passed}/{len(scored)} probes passed"
          + ("" if len(scored) == len(results) else "  (P6 informational unless Ollama stopped)"))
    print("=" * 64)

    os.makedirs(os.path.join(REPO_ROOT, "benchmarks", "results"), exist_ok=True)
    out = os.path.join(REPO_ROOT, "benchmarks", "results", "exp4_failure_probes.json")
    with open(out, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(timespec="seconds"),
                   "passed": passed, "scored": len(scored), "probes": results}, f, indent=2)
    print(f" Wrote {out}")
    return 0 if passed == len(scored) else 1


if __name__ == "__main__":
    sys.exit(main())
