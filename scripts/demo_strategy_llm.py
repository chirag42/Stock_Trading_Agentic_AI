"""
scripts/demo_strategy_llm.py — Strategy Agent LLM-path validation (Hard Stop 3).

Exercises the REAL decision path end-to-end: prompt construction -> Ollama (llama3.2)
query -> decision parsing. It uses representative indicator and sentiment inputs (an
oversold + bullish-MACD setup with positive news, which the decision rules map to BUY),
because current live-market data does not satisfy the Signal Filter's escalation
criteria. This is a component-level validation of the LLM integration, distinct from the
live end-to-end pipeline run.

Prerequisite: Ollama must be running with llama3.2 pulled.
    ollama list          # confirm llama3.2 is present
    ollama serve         # if not already running

Run from the repository root:
    python scripts/demo_strategy_llm.py
"""

import os
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agents.strategy_agent import StrategyAgent
from agents.strategy_agent.exceptions import LLMConnectionError

# Representative inputs: oversold RSI + bullish MACD crossover + positive sentiment.
# Per the prompt's decision rules this maps to BUY (oversold < 35 AND bullish MACD).
MARKET_DATA = {
    "ticker":      "DEMO",
    "close_price": 182.40,
    "rsi":         27.8,      # oversold
    "macd":        0.85,      # above signal -> bullish crossover
    "signal":      0.40,
}
SENTIMENT_DATA = {
    "overall":           "positive",
    "positive":          7,
    "negative":          1,
    "neutral":           2,
    "articles_analyzed": 10,
}


def main():
    print("=" * 60)
    print(" STRATEGY AGENT LLM-PATH VALIDATION — Hard Stop 3")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(" Inputs: oversold RSI 27.8 + bullish MACD + positive sentiment")
    print("=" * 60)

    agent = StrategyAgent()  # defaults to llama3.2 via Ollama
    try:
        result = agent.decide(MARKET_DATA, SENTIMENT_DATA)
    except LLMConnectionError as exc:
        print(f"\n[FAIL] {exc}")
        print("Start Ollama (ollama serve) and ensure llama3.2 is pulled, then retry.")
        return 1

    print(f"\n  Decision : {result['decision']}")
    print("  LLM reasoning:")
    for line in result["llm_reasoning"].splitlines():
        print(f"      {line}")
    print("\n" + "-" * 60)
    print(f" LLM PATH OK — Ollama returned and parsed a '{result['decision']}' decision.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
