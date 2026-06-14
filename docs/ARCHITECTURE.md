# Architecture Notes

How the repository maps onto the system design, and where CISC 699 extends it.

## 1. Principles
1. **Single responsibility per component.** Each agent/service owns one pipeline stage.
2. **Agents reason; services compute.** Services fetch/calculate/record; agents decide.
3. **External dependencies behind thin wrappers.** yfinance, Brave Search, and the LLM
   are reached through dedicated modules, so swapping the LLM (Ollama → Claude) is a
   localized change inside `agents/strategy_agent/llm_client.py`.
4. **Hard simulation boundary.** No module places a real order.

## 2. Component → Module Map
| Design Component | Module(s) | State |
|------------------|-----------|-------|
| Data Ingestion | `services/data_ingestion/` (service, fetcher, indicators, cache, validator, historical_analyzer) | ✅ Complete + tested |
| Signal Filter | `agents/signal_filter.py` (dynamic thresholds via HistoricalAnalyzer) | ✅ Complete + tested |
| Sentiment Analysis | `services/sentiment_analysis/` (service, fetcher, classifier=FinBERT, aggregator) | ✅ Complete + tested |
| Strategy Agent | `agents/strategy_agent/` (agent, prompt_builder, llm_client) | ✅ Complete + tested |
| LLM backend | `agents/strategy_agent/llm_client.py` (Ollama/llama3.2) | 🔄 Claude migration target |
| Risk Validator | `agents/risk_validator.py` (RSI extremes, position size, stop loss, emergency halt) | ✅ Complete + tested |
| Scheduler | `core/scheduler.py` (watchlist polling loop) | ✅ Complete |
| Pipeline | `pipeline.py` (single-ticker end-to-end) | ✅ Complete |
| Service runners | `scripts/run_*.py` | ✅ Complete |
| Execution Simulator | (planned) | 📋 CISC 699 |
| Portfolio Agent | (planned) | 📋 CISC 699 |

## 3. Data Flow
1. `main.py` starts the `Scheduler` over a watchlist (`pipeline.py` handles one ticker).
2. **Data Ingestion** → `get_latest_summary(ticker)` returns price, RSI, MACD, signal line.
3. **Signal Filter** → `check(market_data)` escalates only on strong signals (saves LLM calls).
4. **Sentiment Analysis** → `get_aggregated_sentiment(ticker)` returns an aggregated score.
5. **Strategy Agent** → `decide(market_data, sentiment_data)` returns decision + reasoning.
6. **Risk Validator** → `validate_trade(...)` approves / warns / rejects.
7. **Execution Simulator** (planned) records the simulated trade and P&L.

## 4. CISC 699 Extension Strategy
- **Claude migration:** add a Claude-backed client behind the same interface as the
  current Ollama client in `agents/strategy_agent/llm_client.py`; keep Ollama runnable
  until parity is verified on shared fixtures.
- **Execution Simulator:** new module recording entry/exit + P&L, feeding back to Strategy.
- **Portfolio Agent:** sits above the pipeline; converts a user profile into a watchlist
  and supplies dynamic thresholds that replace the Risk Validator's static 5%/20% defaults.
- **Sequencing:** Execution Simulator → Claude client → Portfolio Agent, keeping the
  pipeline runnable at each step.

## 5. Cross-Cutting
- **Config/secrets:** `.env` (gitignored), template in `.env.example`.
- **Testing:** per-component suites under `tests/` (221 tests) + offline `smoke_test.py`.
- **Reproducibility:** pinned `requirements.txt`; deterministic logic unit-tested without network.
