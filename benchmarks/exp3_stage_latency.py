"""
benchmarks/exp3_stage_latency.py — Experiment 3 (Hard Stop 4).

Per-stage latency: indicators, FinBERT, and the LLM query, on fixed inputs.
LLM backend selectable: --backend ollama (default) or --backend claude.

USAGE
    python benchmarks/exp3_stage_latency.py --iters 5
    python benchmarks/exp3_stage_latency.py --iters 5 --backend claude

Results are written to benchmarks/results/exp3_stage_latency_<backend>.json
"""

import argparse
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import pandas as pd


def time_stage(fn, iters):
    ts = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return ts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=5, help="iterations per stage")
    ap.add_argument("--backend", default="ollama", choices=["ollama", "claude"])
    args = ap.parse_args()

    print("=" * 64)
    print(" EXPERIMENT 3 — PER-STAGE LATENCY PROFILE")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(f" LLM backend: {args.backend}   Iterations/stage: {args.iters}")
    print(f" Env: Python {platform.python_version()} on {platform.system()} {platform.machine()}")
    print("=" * 64)

    results = {}
    model_name = args.backend

    # Stage 1: indicator computation (offline)
    from services.data_ingestion.indicators import IndicatorCalculator
    calc = IndicatorCalculator()
    prices = pd.DataFrame({"Close": 100 + np.cumsum(np.random.default_rng(1).normal(0.3, 1.0, 120))})
    results["indicators"] = time_stage(lambda: calc.calculate(prices.copy()), args.iters)

    # Stage 2: FinBERT sentiment classification (offline model inference)
    try:
        from services.sentiment_analysis.classifier import SentimentClassifier
        clf = SentimentClassifier()
        headline = "Company beats earnings expectations and raises full-year guidance."
        results["finbert_classify"] = time_stage(lambda: clf.classify(headline), args.iters)
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] FinBERT stage skipped: {type(exc).__name__}: {exc}")

    # Stage 3: LLM query (Ollama or Claude)
    try:
        from agents.strategy_agent import StrategyAgent, LLMConnectionError
        agent = StrategyAgent(backend=args.backend)
        model_name = agent.model_name
        market = {"ticker": "BENCH", "close_price": 182.4, "rsi": 27.8, "macd": 0.85, "signal": 0.40}
        sentiment = {"overall": "positive", "positive": 7, "negative": 1, "neutral": 2, "articles_analyzed": 10}
        results["llm_query"] = time_stage(lambda: agent.decide(market, sentiment), args.iters)
    except LLMConnectionError as exc:
        print(f"  [WARN] LLM stage skipped: {exc}")

    print(f"\n {'Stage':<20}{'mean (s)':>12}{'median (s)':>14}")
    print(" " + "-" * 44)
    summary = {}
    for stage, ts in results.items():
        mean, med = statistics.mean(ts), statistics.median(ts)
        summary[stage] = {"mean_s": round(mean, 4), "median_s": round(med, 4), "n": len(ts)}
        print(f" {stage:<20}{mean:>12.4f}{med:>14.4f}")
    print("=" * 64)

    if "llm_query" in summary and "indicators" in summary:
        ratio = summary["llm_query"]["mean_s"] / max(summary["indicators"]["mean_s"], 1e-9)
        print(f" LLM query is ~{ratio:,.0f}x slower than indicator computation.")

    os.makedirs(os.path.join(REPO_ROOT, "benchmarks", "results"), exist_ok=True)
    out = os.path.join(REPO_ROOT, "benchmarks", "results", f"exp3_stage_latency_{args.backend}.json")
    with open(out, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(timespec="seconds"),
                   "backend": args.backend, "llm_model": model_name,
                   "iters": args.iters, "stages": summary}, f, indent=2)
    print(f" Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
