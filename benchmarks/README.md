# Benchmarks — Midpoint Technical Evidence (Hard Stop 4)

Controlled experiments examining the central technical question:

> **Is the local LLM (Ollama / llama3.2) decision layer reliable enough to trust, and
> does the evidence justify migrating to a hosted model (Claude)?**

All experiments record run metadata (timestamp, model, parameters, environment) and
write machine-readable results to `benchmarks/results/*.json` for auditability.

## Prerequisites
```bash
pip install -r requirements.txt
ollama serve            # Ollama running with llama3.2 pulled (ollama pull llama3.2)
```

## Experiments

| # | Script | Question | External dep |
|---|--------|----------|--------------|
| 1 | `exp1_decision_consistency.py` | Same input, N times — how consistent is the decision, and how slow? | Ollama |
| 2 | `exp2_llm_vs_rules.py` | Does the LLM follow its own stated rules vs a deterministic oracle? | Ollama |
| 3 | `exp3_stage_latency.py` | Which pipeline stage is the bottleneck? | Ollama + FinBERT |
| 4 | `exp4_failure_probes.py` | Does the system fail safely with typed exceptions? | None (P6 needs Ollama stopped) |

## How to run
```bash
python benchmarks/exp1_decision_consistency.py --runs 20
python benchmarks/exp2_llm_vs_rules.py --repeats 1
python benchmarks/exp3_stage_latency.py --iters 5
python benchmarks/exp4_failure_probes.py
```

## Method notes (for reproducibility)
- **Fixed inputs.** Experiments 1–3 use hard-coded market/sentiment inputs and seeded
  synthetic price series, so results depend only on the model, not on live data.
- **Deterministic baseline.** `rule_oracle.py` encodes the prompt's exact decision rules
  (BUY if RSI<35 and bullish MACD; SELL if RSI>65 and bearish MACD; else HOLD). Experiment 2
  measures LLM agreement against this baseline.
- **Latency scope.** Experiment 3 times computational stages (indicators, FinBERT, LLM) on
  fixed inputs; network-bound data-fetch latency is excluded as variable and discussed
  separately.
- **Failure injection.** Experiment 4 asserts the correct typed exception for each fault;
  probe P6 (Ollama unavailable) is a true pass only when Ollama is stopped.

## Interpreting results
- **Consistency (Exp 1):** agreement < 100% quantifies non-determinism in the decision layer.
- **Rule-fidelity (Exp 2):** lower agreement means the LLM deviates from its instructions.
- **Bottleneck (Exp 3):** expected to be dominated by the LLM query.
- **Robustness (Exp 4):** all probes passing shows disciplined, typed error handling.

Together these inform whether the Ollama decision layer is trustworthy as-is or whether the
Claude migration should be prioritized next.
