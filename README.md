# Agentic AI Stock Trading System

A research-based multi-agent AI system that simulates autonomous stock trading.
Specialized agents collaborate to analyze market data, process financial news,
generate trading strategies, and validate risk — entirely in simulation, with
**no real money and no real brokerage integration**.

Instead of one model making every decision, the system distributes responsibility
across specialized components, mirroring a real trading desk: a data analyst, a news
analyst, a strategist, and a risk manager working together.

> **Status:** CISC 699 Implementation Sprint I — engineering baseline tagged `release-2026-sprint1-v0.1.0`.
> The core pipeline (GRAD 695) is complete and tested (221 unit tests). This phase
> migrates the Strategy Agent's LLM from local Ollama to the Claude API and adds the
> Execution Simulator and Portfolio Agent.

---

## System Architecture

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
Strategy Agent (LLM)     → fuses signals → BUY / SELL / HOLD + reasoning
        │                   [CISC 699: Ollama/llama3.2 → Claude API]
        ▼
Risk Validator           → gates the decision (RSI extremes, position size, stop loss)
        │
        ▼
Execution Simulator      → records simulated trade + P&L   [planned, CISC 699]
```

The `core/scheduler.py` drives the loop across a watchlist; `pipeline.py` wires a single
ticker through the stages end-to-end.

---

## Repository Structure

```
Stock_Trading_Agentic_AI/
├── agents/
│   ├── risk_validator.py             # RSI / position-size / stop-loss gating
│   ├── signal_filter.py              # dynamic-threshold signal escalation
│   └── strategy_agent/               # LLM decision subpackage
│       ├── agent.py                  # decide(market, sentiment) -> decision
│       ├── llm_client.py             # Ollama client (← Claude migration target)
│       ├── prompt_builder.py
│       └── exceptions.py
├── services/
│   ├── data_ingestion/               # yfinance + indicators subpackage
│   │   ├── service.py · fetcher.py · indicators.py · cache.py
│   │   ├── validator.py · historical_analyzer.py · exceptions.py
│   └── sentiment_analysis/           # news + FinBERT subpackage
│       ├── service.py · fetcher.py · classifier.py
│       ├── aggregator.py · exceptions.py
├── core/
│   └── scheduler.py                  # watchlist polling loop
├── scripts/                          # standalone service runners
│   ├── run_data_ingestion.py · run_sentiment_analysis.py · run_strategy_agent.py
├── tests/                            # pytest suites, mirrored per component (221 tests)
│   ├── data_ingestion/ · sentiment_analysis/ · strategy_agent/
│   ├── signal_filter/ · scheduler/ · scripts/ · historical_analyzer/
│   └── smoke_test.py                 # minimal offline baseline check
├── docs/                             # engineering documentation
│   ├── ARCHITECTURE.md · CHANGELOG note · KNOWN_ISSUES.md
│   ├── RISK_LOG.md · SPRINT_REFLECTION.md · AI_USAGE_LOG.md
├── utils/
├── main.py                           # entry point — runs the Scheduler over a watchlist
├── pipeline.py                       # single-ticker end-to-end orchestrator
├── requirements.txt
├── .env.example
├── .gitignore
├── CHANGELOG.md
└── README.md
```

### Conventions
- **Modules/files:** `snake_case`; **classes:** `PascalCase`; **constants:** `UPPER_SNAKE`.
- **Agents reason; services compute.** Subpackages expose their public class via `__init__.py`
  (e.g. `from services.data_ingestion import DataIngestionService`).
- **Tests mirror source layout** under `tests/<component>/`.
- **Secrets** live in `.env` (gitignored); only `.env.example` is tracked. Runtime/cache
  artifacts are never committed.

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Always releasable; tagged baselines (`release-2026-sprint1-v0.1.0`, …) live here. |
| `feature/<name>` | One branch per unit of work (e.g. `feature/execution-simulator`, `feature/claude-llm-client`). |
| `fix/<name>` | Targeted bug fixes. |

Commit messages: imperative and scoped — `feat(exec): add P&L tracking`,
`docs(readme): refresh structure`, `test(signal): cover transition crossovers`.

---

## Setup

### Prerequisites
- Python **3.11+**, `git`
- **Ollama** with `llama3.2` pulled (current Strategy Agent backend)
- A **Brave Search API** key (financial news)

### Install
```bash
git clone https://github.com/chirag42/Stock_Trading_Agentic_AI.git
cd Stock_Trading_Agentic_AI

python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env                # then fill in BRAVE_API_KEY

# Strategy Agent LLM (local):
# install Ollama from ollama.com, then:
ollama pull llama3.2
```

### Required environment variables
| Variable | Purpose |
|----------|---------|
| `BRAVE_API_KEY` | Financial news retrieval for sentiment |
| `ANTHROPIC_API_KEY` | Claude API (CISC 699 migration — not yet required) |

---

## Running

```bash
# Run the full scheduler over a watchlist
python main.py

# Run a single ticker end-to-end
python -c "from pipeline import TradingPipeline; TradingPipeline().run('MSFT')"

# Run individual service runners
python scripts/run_data_ingestion.py
python scripts/run_sentiment_analysis.py
python scripts/run_strategy_agent.py

# Full test suite (221 tests)
pytest

# Minimal offline smoke test (no keys / Ollama / model load)
python tests/smoke_test.py
```

The smoke test imports every core module and exercises the real `SignalFilter` and
`RiskValidator` against synthetic inputs. A passing run ends with `BASELINE OK`.

---

## Current Status

| Component | State |
|-----------|-------|
| Data Ingestion (modular) | ✅ Complete + tested |
| Sentiment Analysis (modular, FinBERT) | ✅ Complete + tested |
| Signal Filter (dynamic thresholds) | ✅ Complete + tested |
| Strategy Agent (Ollama/llama3.2) | ✅ Complete + tested |
| Risk Validator | ✅ Complete + tested |
| Scheduler + Pipeline | ✅ Complete |
| **Unit tests** | ✅ **221 passing** |
| Claude API migration (`llm_client.py`) | 🔄 CISC 699 — planned |
| Execution Simulator | 📋 CISC 699 — planned |
| Portfolio Agent | 📋 CISC 699 — planned |

---

## Documentation
See [`docs/`](docs/): architecture notes, known-issues log, risk register, sprint
reflection, and AI usage log. Version history is in [`CHANGELOG.md`](CHANGELOG.md).

---

## Disclaimer
This system is a **research simulation only**. It does not connect to any brokerage,
executes no real trades, involves no real money, and is not financial advice.
