"""
benchmarks/exp1_decision_consistency.py — Experiment 1 (Hard Stop 4).

Same fixed input sent N times; measures decision agreement and latency.
Backend selectable: --backend ollama (default) or --backend claude.

USAGE
    python benchmarks/exp1_decision_consistency.py --runs 20                  # Ollama
    python benchmarks/exp1_decision_consistency.py --runs 20 --backend claude # Claude

Results are written to benchmarks/results/exp1_consistency_<backend>.json
"""

import argparse
import json
import os
import platform
import statistics
import sys
import time
from collections import Counter
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agents.strategy_agent import StrategyAgent, LLMConnectionError

MARKET_DATA = {"ticker": "BENCH", "close_price": 182.40, "rsi": 27.8, "macd": 0.85, "signal": 0.40}
SENTIMENT_DATA = {"overall": "positive", "positive": 7, "negative": 1, "neutral": 2, "articles_analyzed": 10}


def percentile(values, pct):
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100.0)
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=20, help="number of repeated LLM calls")
    ap.add_argument("--backend", default="ollama", choices=["ollama", "claude"])
    args = ap.parse_args()

    agent = StrategyAgent(backend=args.backend)

    print("=" * 64)
    print(" EXPERIMENT 1 — DECISION CONSISTENCY & LATENCY")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(f" Backend: {args.backend}   Model: {agent.model_name}   Runs: {args.runs}")
    print(f" Env: Python {platform.python_version()} on {platform.system()} {platform.machine()}")
    print(" Fixed input: RSI 27.8 (oversold), MACD 0.85 > Signal 0.40 (bullish), sentiment positive")
    print("=" * 64)

    decisions, latencies = [], []
    for i in range(1, args.runs + 1):
        t0 = time.perf_counter()
        try:
            result = agent.decide(MARKET_DATA, SENTIMENT_DATA)
        except LLMConnectionError as exc:
            print(f"\n[FAIL] {exc}")
            return 1
        dt = time.perf_counter() - t0
        decisions.append(result["decision"])
        latencies.append(dt)
        print(f"  run {i:>2}: {result['decision']:<5}  {dt:6.2f}s")

    dist = Counter(decisions)
    modal, modal_n = dist.most_common(1)[0]
    agreement = 100.0 * modal_n / len(decisions)

    print("\n" + "-" * 64)
    print(" Decision distribution:", dict(dist))
    print(f" Modal decision: {modal}  ({modal_n}/{len(decisions)} = {agreement:.1f}% agreement)")
    print(f" Latency (s): mean={statistics.mean(latencies):.2f}  "
          f"median={statistics.median(latencies):.2f}  "
          f"p95={percentile(latencies, 95):.2f}  "
          f"min={min(latencies):.2f}  max={max(latencies):.2f}")
    print("=" * 64)

    os.makedirs(os.path.join(REPO_ROOT, "benchmarks", "results"), exist_ok=True)
    out = os.path.join(REPO_ROOT, "benchmarks", "results", f"exp1_consistency_{args.backend}.json")
    with open(out, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "backend": args.backend, "model": agent.model_name, "runs": args.runs,
            "input": {"market": MARKET_DATA, "sentiment": SENTIMENT_DATA},
            "decisions": decisions, "distribution": dict(dist),
            "modal_decision": modal, "agreement_pct": round(agreement, 1),
            "latency_s": {
                "mean": round(statistics.mean(latencies), 3),
                "median": round(statistics.median(latencies), 3),
                "p95": round(percentile(latencies, 95), 3),
                "min": round(min(latencies), 3), "max": round(max(latencies), 3),
            },
        }, f, indent=2)
    print(f" Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
