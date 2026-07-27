# Agentic AI Stock Trading System

A research-based multi-agent AI system that simulates autonomous stock trading.
Specialized agents collaborate to analyze market data, process financial news,
weigh company fundamentals, generate trading strategies, and validate risk —
entirely in simulation, with **no real money and no real brokerage integration**.

Instead of one model making every decision, the system distributes responsibility
across specialized components, mirroring a real trading desk: a data analyst, a news
analyst, a strategist, and a risk manager working together.

> **Status — CISC 699.** The core pipeline (GRAD 695) is complete and tested (221 unit
> tests). CISC 699 has since added **company fundamentals** as decision context and a
> **configurable LLM backend** so the Strategy Agent runs on either the **Claude API**
> (default) or **local Ollama/llama3.2**. Evidence for the Claude vs. Ollama comparison
> lives in [`benchmarks/`](benchmarks/) (tagged `release-2026-hardstop4-v0.3.0`).

---

## 1. Purpose

This repository is the **decision engine** of the project. Given a stock ticker, it
gathers market indicators, news sentiment, and fundamentals, and produces an auditable
**BUY / SELL / HOLD** decision with plain-language reasoning. It is consumed directly
(via `main.py` / `pipeline.py`) and also serves as an importable dependency for the
companion **backend API** and **frontend** projects.

---

## 2. System Architecture

```
User Input (Stock Ticker)
        │
        ▼
Data Ingestion Service   → yfinance OHLCV + RSI / MACD (+ historical analyzer)
        │
        ▼
Signal Filter            → escalates to the LLM only on strong, dynamic-threshold signals
        │
        ▼
Sentiment Analysis       → Brave Search news → FinBERT classification → aggregated score
        │
        ▼
Fundamentals (context)   → yfinance quarterly financials, balance sheet, valuation,
        │                   earnings timing — degrades gracefully to "unavailable"
        ▼
Strategy Agent (LLM)     → fuses signals → BUY / SELL / HOLD + reasoning
        │                   backend = claude (default) | ollama  (configurable)
        ▼
Risk Validator           → gates the decision (RSI extremes, position size, stop loss)
```

`core/scheduler.py` drives the loop across a watchlist; `pipeline.py` wires a single
ticker through the stages end-to-end.

---

## 3. Prerequisites

| Requirement | Version used in development | Notes |
|-------------|-----------------------------|-------|
| Python | **3.12.4** (3.11+ supported) | `python --version` |
| pip | bundled with Python | |
| git | any recent | |
| Ollama | 0.30.10 | **only if** using the local backend; pull `llama3.2` |
| Anthropic API key | — | required for the default Claude backend |
| Brave Search API key | — | required for news sentiment |

**Hardware assumptions.** Runs on a standard laptop (developed on macOS, Apple Silicon,
16 GB RAM). No GPU is required. FinBERT runs on CPU (first load downloads ~440 MB of
model weights). The local Ollama backend is CPU-bound and noticeably slower than the
Claude API; the Claude backend needs only network access.

---

## 4. Setup

```bash
git clone https://github.com/chirag42/Stock_Trading_Agentic_AI.git
cd Stock_Trading_Agentic_AI

python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env                # then fill in the keys (see section 6)
```

If you plan to use the **local** backend, also install Ollama from https://ollama.com and:
```bash
ollama pull llama3.2
```

---

## 5. Running & expected outputs

```bash
# Full scheduler over a watchlist (Claude backend by default)
python main.py --backend claude
python main.py --backend ollama       # local alternative (Ollama must be running)

# Single ticker end-to-end
python -c "from pipeline import TradingPipeline; TradingPipeline().run('MSFT')"

# Standalone service runners
python scripts/run_data_ingestion.py
python scripts/run_sentiment_analysis.py
python scripts/run_strategy_agent.py

# Full test suite (offline; no keys or model calls needed)
pytest -q

# Minimal offline smoke test
python tests/smoke_test.py
```

**Expected output — single ticker run:** the pipeline prints each stage in order
(market data → signal filter → sentiment → fundamentals → decision). A typical ending:

```
============================================================
  DECISION for MSFT: *** HOLD ***
============================================================
  LLM REASONING:
  HOLD
  Reasons:
  1. RSI is in a neutral range ...
  ...
```

If the signal filter judges the setup too weak, the run ends early with
`Signal too weak — skipping LLM` — this is expected behavior, not an error.

**Expected output — tests:** `pytest -q` ends with `221 passed`.

**Expected output — benchmarks:** each experiment writes a JSON file to
`benchmarks/results/` and prints a summary (e.g. Exp 1 consistency, Exp 2 rule
agreement). See section 8.

---

## 6. Configuration & API keys

Secrets are read from the **environment** (never hard-coded, never committed). Copy
`.env.example` to `.env` and fill in the values, **or** export them in your shell.

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `ANTHROPIC_API_KEY` | for Claude backend | Claude API (default Strategy Agent LLM) |
| `BRAVE_API_KEY` | yes | Brave Search — financial news for sentiment |

**Credential handling.** `.env` is gitignored; only `.env.example` (blank template) is
tracked. In CI, keys are provided as GitHub Actions **Secrets** and injected via `env:`.

**Rate limits.** The Brave free tier is rate-limited; rapid repeated runs may return
fewer or no articles. The Claude API is billed per call and has request-rate limits.
Both paths degrade gracefully — a missing news response yields neutral sentiment rather
than a crash.

**No key? Use the fully offline path:** `pytest -q` and `python tests/smoke_test.py`
require no keys, no network, and no Ollama — they run on synthetic, seeded inputs.

---

## 7. Data handling

- **Market data** comes from **Yahoo Finance via the `yfinance` library** — an
  unofficial API. Data is fetched live at runtime and cached briefly in memory; **no
  market data is stored in or committed to the repository.**
- **News** comes from the **Brave Search API**, fetched live per request.
- **What cannot be redistributed:** raw Yahoo/Brave responses are not redistributed —
  the repo contains only code and synthetic/seeded fixtures used by the tests and
  benchmarks. Anyone reproducing the project supplies their own API keys and fetches
  their own live data.
- **Determinism:** benchmarks use fixed inputs and a seeded synthetic price series so
  results depend only on the model, not on live-market variability.

---

## 8. Reproducibility — benchmarks & evidence

The `benchmarks/` folder contains the controlled experiments behind the Claude-vs-Ollama
comparison. Each harness takes a `--backend` flag and writes machine-readable JSON to
`benchmarks/results/`.

```bash
# Offline / deterministic — no keys needed
python benchmarks/exp4_failure_probes.py

# Backend comparison (needs the relevant key / Ollama)
python benchmarks/exp1_decision_consistency.py --runs 20 --backend claude
python benchmarks/exp2_llm_vs_rules.py --repeats 1 --backend claude
python benchmarks/exp3_stage_latency.py --iters 5 --backend claude
```

Evidence assets are versioned in the repo and snapshotted at tag
`release-2026-hardstop4-v0.3.0`.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ANTHROPIC_API_KEY not found` / `BRAVE_API_KEY` empty | env not loaded in this shell | `source ~/.zshrc` (or re-`export`), then re-run in the same terminal |
| Logs show `Querying llama3.2 via Ollama` after setting Claude | `main.py` takes the backend from `--backend`, not the env var | run `python main.py --backend claude` |
| `LLMConnectionError` on the Ollama backend | Ollama not running / model not pulled | start Ollama; `ollama pull llama3.2`; verify `ollama list` |
| Sentiment returns few/no articles | Brave free-tier rate limit | wait and retry; runs still complete with neutral sentiment |
| Fundamentals show `unavailable` for a ticker | yfinance has no data for that field/ticker | expected — the system reasons on what is present |
| `ModuleNotFoundError` running a script | venv not activated | `source venv/bin/activate` |
| Mixed `(base)` conda + `(venv)` in prompt | conda base auto-activates | run inside the project `venv`; `conda deactivate` if needed |

---

## 10. Repository structure

```
Stock_Trading_Agentic_AI/
├── agents/
│   ├── risk_validator.py             # RSI / position-size / stop-loss gating
│   ├── signal_filter.py              # dynamic-threshold signal escalation
│   └── strategy_agent/               # LLM decision subpackage
│       ├── agent.py                  # decide(market, sentiment, fundamentals) -> decision
│       ├── llm_client.py             # Ollama client
│       ├── claude_client.py          # Claude API client (mirrors llm_client)
│       ├── prompt_builder.py         # builds the prompt (optional fundamentals block)
│       └── exceptions.py
├── services/
│   ├── data_ingestion/               # yfinance + indicators + fundamentals subpackage
│   │   ├── service.py · fetcher.py · indicators.py · cache.py
│   │   ├── validator.py · historical_analyzer.py · fundamentals.py · exceptions.py
│   └── sentiment_analysis/           # news + FinBERT subpackage
│       ├── service.py · fetcher.py · classifier.py · aggregator.py · exceptions.py
├── core/scheduler.py                 # watchlist polling loop (backend-configurable)
├── benchmarks/                       # exp1–exp4 harnesses + results/ (evidence)
├── scripts/                          # standalone service runners
├── tests/                            # pytest suites mirrored per component (221 tests)
├── docs/                             # architecture, known issues, risk log, AI usage log
├── utils/
├── main.py                           # entry point — Scheduler over a watchlist
├── pipeline.py                       # single-ticker end-to-end orchestrator
├── requirements.txt · .env.example · .gitignore · CHANGELOG.md · README.md
```

**Conventions:** modules `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`;
agents reason, services compute; tests mirror source layout; secrets in `.env` only.

---

## 11. Documentation

See [`docs/`](docs/) for architecture notes, the known-issues log, risk register,
sprint reflection, and AI usage log. Version history is in [`CHANGELOG.md`](CHANGELOG.md).

---

## 12. Disclaimer

This system is a **research simulation only**. It does not connect to any brokerage,
executes no real trades, involves no real money, and is **not financial advice**.
