"""
benchmarks/exp2_llm_vs_rules.py — Experiment 2 (Hard Stop 4).

LLM decision vs deterministic rule oracle across an 18-scenario matrix.
Backend selectable: --backend ollama (default) or --backend claude.

USAGE
    python benchmarks/exp2_llm_vs_rules.py --repeats 1
    python benchmarks/exp2_llm_vs_rules.py --repeats 1 --backend claude

Results are written to benchmarks/results/exp2_llm_vs_rules_<backend>.json
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agents.strategy_agent import StrategyAgent, LLMConnectionError
from benchmarks.rule_oracle import rule_decision

RSI_LEVELS = {"oversold": 27.0, "neutral": 50.0, "overbought": 73.0}
MACD_DIRS = {"bullish": (0.9, 0.4), "bearish": (0.4, 0.9)}   # (macd, signal)
SENTIMENTS = {
    "positive": {"overall": "positive", "positive": 7, "negative": 1, "neutral": 2, "articles_analyzed": 10},
    "negative": {"overall": "negative", "positive": 1, "negative": 7, "neutral": 2, "articles_analyzed": 10},
    "neutral":  {"overall": "neutral",  "positive": 3, "negative": 3, "neutral": 4, "articles_analyzed": 10},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=1, help="LLM queries per scenario")
    ap.add_argument("--backend", default="ollama", choices=["ollama", "claude"])
    args = ap.parse_args()

    agent = StrategyAgent(backend=args.backend)

    print("=" * 72)
    print(" EXPERIMENT 2 — LLM vs DETERMINISTIC RULE ORACLE")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(f" Backend: {args.backend}   Model: {agent.model_name}   Repeats/scenario: {args.repeats}")
    print(f" Env: Python {platform.python_version()} on {platform.system()} {platform.machine()}")
    print("=" * 72)
    print(f" {'RSI':<11}{'MACD':<9}{'Sentiment':<11}{'Oracle':<8}{'LLM':<8}{'Match'}")
    print(" " + "-" * 62)

    rows, matches, total = [], 0, 0
    for rsi_name, rsi in RSI_LEVELS.items():
        for macd_name, (macd, signal) in MACD_DIRS.items():
            for sent_name, sentiment in SENTIMENTS.items():
                market = {"ticker": "BENCH", "close_price": 100.0, "rsi": rsi, "macd": macd, "signal": signal}
                oracle = rule_decision(rsi, macd, signal)
                for _ in range(args.repeats):
                    try:
                        llm = agent.decide(market, sentiment)["decision"]
                    except LLMConnectionError as exc:
                        print(f"\n[FAIL] {exc}")
                        return 1
                    match = (llm == oracle)
                    matches += int(match); total += 1
                    print(f" {rsi_name:<11}{macd_name:<9}{sent_name:<11}{oracle:<8}{llm:<8}{'YES' if match else 'no'}")
                    rows.append({"rsi": rsi_name, "macd": macd_name, "sentiment": sent_name,
                                 "oracle": oracle, "llm": llm, "match": match})

    rate = 100.0 * matches / total if total else 0.0
    print(" " + "-" * 62)
    print(f" Overall agreement with rule oracle: {matches}/{total} = {rate:.1f}%")
    print("=" * 72)

    os.makedirs(os.path.join(REPO_ROOT, "benchmarks", "results"), exist_ok=True)
    out = os.path.join(REPO_ROOT, "benchmarks", "results", f"exp2_llm_vs_rules_{args.backend}.json")
    with open(out, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(timespec="seconds"),
                   "backend": args.backend, "model": agent.model_name,
                   "repeats_per_scenario": args.repeats, "agreement_pct": round(rate, 1),
                   "matches": matches, "total": total, "rows": rows}, f, indent=2)
    print(f" Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
