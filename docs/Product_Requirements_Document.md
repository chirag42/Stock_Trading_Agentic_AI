# Product Requirements Document

---

## Cover Page

| Field | Value |
|-------|-------|
| **Project Name** | Agentic AI Stock Trading System |
| **Student(s)** | Chirag Nagpal |
| **Course** | GRAD 695 / CISC 699 |
| **Semester** | Spring 2026 |
| **Repository URL** | https://github.com/chirag42/Stock_Trading_Agentic_AI.git |
| **Current Branch** | feature-sprint-5-changes |
| **Current Commit SHA** | fe49dacad2bf8bf546527f8eb096de3f443c20b9 |
| **Current Release Version** | release-2026-hardstop4-v0.3.0 |
| **Document Version** | 1.0.0 |
| **Last Updated** | 2026-07-21 |

---

## Revision History

| Version | Date | Git Commit | Description | Author |
|---------|------|------------|-------------|--------|
| 1.0.0 | 2026-07-21 | fe49dacad2 | Initial PRD creation from repository analysis | Chirag Nagpal |

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [Product Scope](#2-product-scope)
3. [Software Capabilities](#3-software-capabilities)
4. [Undesirable Events](#4-undesirable-events)
5. [Risk Analysis](#5-risk-analysis)
6. [Risk Prioritization](#6-risk-prioritization)
7. [Risk Mitigation](#7-risk-mitigation)
8. [Functional Requirements](#8-functional-requirements)
9. [Quality Requirements](#9-quality-requirements)
10. [Performance Requirements](#10-performance-requirements)
11. [Assumptions](#11-assumptions)
12. [Constraints](#12-constraints)
13. [External Interfaces](#13-external-interfaces)
14. [Requirements Traceability Matrix](#14-requirements-traceability-matrix)
15. [Future Versions](#15-future-versions)
16. [Open Issues](#16-open-issues)
17. [Glossary](#17-glossary)

---

## 1. Product Vision

### 1.1 Problem Statement

Individual traders and researchers lack access to institutional-grade autonomous trading decision systems. Existing solutions either require significant capital for professional tools or rely on simplistic rule-based approaches that cannot adapt to complex market conditions. There is a need for a research-oriented multi-agent AI system that demonstrates how specialized agents can collaborate to analyze market data, process financial news, generate trading strategies, and validate risk.

### 1.2 Intended Users

- **Researchers**: Academic researchers studying multi-agent AI systems and their application to financial decision-making
- **Students**: Graduate students learning about agentic AI architectures and financial technology
- **Developers**: Software engineers exploring LLM integration patterns in domain-specific applications

### 1.3 Stakeholders

- **Academic Supervisors**: Course instructors evaluating the project for GRAD 695/CISC 699
- **Research Community**: Peers interested in reproducing or extending the system
- **Student Developer**: Primary maintainer responsible for implementation and documentation

### 1.4 Product Goals

1. Demonstrate a functional multi-agent architecture where specialized components collaborate on trading decisions
2. Integrate market data analysis, sentiment analysis, and LLM-based reasoning in a coherent pipeline
3. Implement robust risk validation to gate trading decisions
4. Provide a reproducible research baseline with comprehensive testing (221+ unit tests)
5. Enable comparison between local LLM (Ollama/llama3.2) and hosted LLM (Claude) backends

### 1.5 Major Features

Based on repository evidence:

| Feature | Status | Module |
|---------|--------|--------|
| Data Ingestion (yfinance + indicators) | ✅ Complete | `services/data_ingestion/` |
| Historical Analysis (dynamic thresholds) | ✅ Complete | `services/data_ingestion/historical_analyzer.py` |
| Fundamentals Fetching | ✅ Complete | `services/data_ingestion/fundamentals.py` |
| Sentiment Analysis (FinBERT) | ✅ Complete | `services/sentiment_analysis/` |
| Signal Filtering (dynamic thresholds) | ✅ Complete | `agents/signal_filter.py` |
| Strategy Agent (LLM decisions) | ✅ Complete | `agents/strategy_agent/` |
| Risk Validation | ✅ Complete | `agents/risk_validator.py` |
| Pipeline Orchestration | ✅ Complete | `pipeline.py` |
| Scheduler (watchlist polling) | ✅ Complete | `core/scheduler.py` |
| Benchmark Suite | ✅ Complete | `benchmarks/` |
| Claude API Integration | ✅ Complete | `agents/strategy_agent/claude_client.py` |
| Execution Simulator | 📋 Planned | — |
| Portfolio Agent | 📋 Planned | — |

### 1.6 Planned Software Versions

| Version | Description | Status |
|---------|-------------|--------|
| 0.1.0 | Engineering baseline (GRAD 695 core complete) | ✅ Released |
| 0.3.0 | Hard Stop 4 — Benchmark suite and Claude integration | ✅ Current |
| 1.0.0 | Execution Simulator and Portfolio Agent | 📋 Planned |

---

## 2. Product Scope

### 2.1 Included Functionality

- **Market Data Ingestion**: Fetch OHLCV data via yfinance with RSI and MACD indicator calculation
- **Historical Analysis**: Compute per-ticker dynamic thresholds from 1-year price history
- **Fundamentals Retrieval**: Extract quarterly results, balance sheet health, valuation metrics (best-effort)
- **News Sentiment Analysis**: Fetch financial news via Brave Search API, classify with FinBERT model
- **Signal Filtering**: Escalate only strong signals to LLM using dynamic thresholds and transition detection
- **Strategy Generation**: LLM-based trading decision (BUY/SELL/HOLD) with reasoning via Ollama or Claude
- **Risk Validation**: Gate decisions based on RSI extremes, position size limits, stop-loss checks, emergency halt
- **Watchlist Scheduling**: Poll multiple tickers at configurable intervals with cooldown management
- **Benchmark Experiments**: Decision consistency, rule fidelity, stage latency, failure probe testing

### 2.2 Excluded Functionality

- **Real Trade Execution**: No connection to any brokerage; all trades are simulated
- **Real Money**: No financial transactions; research simulation only
- **Portfolio Tracking**: Actual portfolio positions and P&L tracking not yet implemented
- **User Authentication**: No user accounts or multi-user support
- **Web Interface**: Command-line only; no GUI or web dashboard

### 2.3 Future Enhancements

- Execution Simulator for recording simulated trades and computing P&L
- Portfolio Agent for user profile to watchlist/threshold conversion
- Automated CI/CD pipeline (GitHub Actions)
- Web-based dashboard for monitoring

---

## 3. Software Capabilities

### 3.1 Level-1 Capabilities

| ID | Capability | Description |
|----|------------|-------------|
| C1 | Ingest Market Data | Fetch and process real-time and historical market data with technical indicators |
| C2 | Analyze Sentiment | Retrieve financial news and classify sentiment using NLP models |
| C3 | Filter Trading Signals | Evaluate market conditions and escalate significant signals for LLM processing |
| C4 | Generate Trading Decisions | Use LLM reasoning to produce BUY/SELL/HOLD decisions with justification |
| C5 | Validate Trade Risk | Gate trading decisions through risk management rules and limits |
| C6 | Schedule Pipeline Execution | Manage watchlist polling, market hours, and cooldown periods |
| C7 | Benchmark Agent Performance | Run controlled experiments to measure decision quality and system reliability |

### 3.2 Level-2 Capabilities

#### C1. Ingest Market Data

| ID | Capability |
|----|------------|
| 1.1 | Fetch OHLCV Data — Retrieve Open/High/Low/Close/Volume from yfinance |
| 1.2 | Calculate Technical Indicators — Compute RSI (14-period) and MACD (12/26/9) |
| 1.3 | Validate Ticker Symbols — Ensure ticker format compliance before API calls |
| 1.4 | Cache Market Data — Store fetched data with configurable TTL to reduce API calls |
| 1.5 | Analyze Historical Patterns — Compute 1-year statistics for dynamic threshold generation |
| 1.6 | Fetch Fundamental Data — Retrieve quarterly financials, valuation ratios, earnings info |

#### C2. Analyze Sentiment

| ID | Capability |
|----|------------|
| 2.1 | Fetch Financial News — Query Brave Search API for ticker-related headlines |
| 2.2 | Classify Sentiment — Apply FinBERT model to each article for positive/negative/neutral |
| 2.3 | Aggregate Sentiment Score — Combine individual classifications into overall sentiment |

#### C3. Filter Trading Signals

| ID | Capability |
|----|------------|
| 3.1 | Initialize Dynamic Thresholds — Run historical analysis on watchlist at startup |
| 3.2 | Detect Initial Entry Signals — Apply tighter thresholds for first-poll decisions |
| 3.3 | Detect Transition Signals — Identify RSI zone crossings and MACD crossovers |

#### C4. Generate Trading Decisions

| ID | Capability |
|----|------------|
| 4.1 | Build Decision Prompt — Assemble market, sentiment, and fundamentals into LLM prompt |
| 4.2 | Query LLM Backend — Send prompt to Ollama (local) or Claude (hosted) |
| 4.3 | Parse Decision Response — Extract BUY/SELL/HOLD from LLM output with fallback parsing |

#### C5. Validate Trade Risk

| ID | Capability |
|----|------------|
| 5.1 | Check RSI Extremes — Reject BUY when RSI > 80, reject SELL when RSI < 20 |
| 5.2 | Enforce Position Size Limits — Block trades exceeding max portfolio percentage (default 20%) |
| 5.3 | Calculate Stop-Loss Impact — Warn if potential loss exceeds portfolio threshold |
| 5.4 | Manage Emergency Halt — Freeze/resume all trading on system command |

#### C6. Schedule Pipeline Execution

| ID | Capability |
|----|------------|
| 6.1 | Manage Watchlist — Track multiple tickers for periodic polling |
| 6.2 | Enforce Market Hours — Optionally restrict polling to US market hours (9:30 AM – 4:00 PM ET) |
| 6.3 | Apply Decision Cooldown — Prevent re-evaluation of ticker for configurable period after decision |
| 6.4 | Execute Pipeline Iteration — Run full pipeline (data → signal → sentiment → LLM → risk) per ticker |

#### C7. Benchmark Agent Performance

| ID | Capability |
|----|------------|
| 7.1 | Measure Decision Consistency — Run identical inputs N times, compute agreement percentage |
| 7.2 | Evaluate Rule Fidelity — Compare LLM decisions against deterministic rule oracle |
| 7.3 | Profile Stage Latency — Time each pipeline stage to identify bottlenecks |
| 7.4 | Test Failure Handling — Inject faults and verify typed exception responses |

---

## 4. Undesirable Events

| UE ID | Level-2 Capability | Undesirable Event |
|-------|-------------------|-------------------|
| UE-1.1-01 | 1.1 Fetch OHLCV Data | yfinance API returns empty or malformed data |
| UE-1.1-02 | 1.1 Fetch OHLCV Data | yfinance rate limiting or outage prevents data retrieval |
| UE-1.2-01 | 1.2 Calculate Technical Indicators | Insufficient data points for indicator calculation |
| UE-1.3-01 | 1.3 Validate Ticker Symbols | Invalid ticker symbol submitted |
| UE-1.4-01 | 1.4 Cache Market Data | Stale cached data used for decision after TTL expiry failure |
| UE-1.5-01 | 1.5 Analyze Historical Patterns | Insufficient RSI periods (< 50) for threshold calculation |
| UE-1.6-01 | 1.6 Fetch Fundamental Data | Fundamental data unavailable or incomplete for ticker |
| UE-2.1-01 | 2.1 Fetch Financial News | Brave Search API rate limiting under rapid calls |
| UE-2.1-02 | 2.1 Fetch Financial News | No news articles found for ticker |
| UE-2.2-01 | 2.2 Classify Sentiment | FinBERT model fails to load due to memory constraints |
| UE-2.2-02 | 2.2 Classify Sentiment | Empty or invalid text submitted for classification |
| UE-2.3-01 | 2.3 Aggregate Sentiment Score | All articles filtered out, no sentiment to aggregate |
| UE-3.1-01 | 3.1 Initialize Dynamic Thresholds | Historical analysis fails for ticker in watchlist |
| UE-3.2-01 | 3.2 Detect Initial Entry Signals | False positive signal on first poll due to extreme market conditions |
| UE-3.3-01 | 3.3 Detect Transition Signals | Missed transition due to polling interval gap |
| UE-4.1-01 | 4.1 Build Decision Prompt | Prompt exceeds LLM context window limit |
| UE-4.2-01 | 4.2 Query LLM Backend | Ollama service not running (LLMConnectionError) |
| UE-4.2-02 | 4.2 Query LLM Backend | Claude API quota exceeded or authentication failure |
| UE-4.2-03 | 4.2 Query LLM Backend | LLM response timeout |
| UE-4.3-01 | 4.3 Parse Decision Response | LLM returns response without valid BUY/SELL/HOLD |
| UE-5.1-01 | 5.1 Check RSI Extremes | Valid trade rejected due to RSI threshold being too conservative |
| UE-5.2-01 | 5.2 Enforce Position Size Limits | Legitimate trade blocked by static position limits |
| UE-5.3-01 | 5.3 Calculate Stop-Loss Impact | Warning fatigue from frequent stop-loss alerts |
| UE-5.4-01 | 5.4 Manage Emergency Halt | Emergency halt not lifted, blocking all subsequent trades |
| UE-6.1-01 | 6.1 Manage Watchlist | Empty watchlist causes scheduler to idle indefinitely |
| UE-6.2-01 | 6.2 Enforce Market Hours | Timezone misconfiguration blocks valid trading windows |
| UE-6.3-01 | 6.3 Apply Decision Cooldown | Cooldown too long, missing profitable re-entry opportunities |
| UE-6.4-01 | 6.4 Execute Pipeline Iteration | Unhandled exception crashes pipeline mid-iteration |
| UE-7.1-01 | 7.1 Measure Decision Consistency | Benchmark produces misleading results due to uncontrolled inputs |
| UE-7.2-01 | 7.2 Evaluate Rule Fidelity | Rule oracle logic diverges from actual prompt instructions |
| UE-7.3-01 | 7.3 Profile Stage Latency | Network variability skews latency measurements |
| UE-7.4-01 | 7.4 Test Failure Handling | Failure probe passes incorrectly when dependency is available |

---

## 5. Risk Analysis

| UE ID | Risk Statement | Likelihood | Impact | Risk Score |
|-------|----------------|------------|--------|------------|
| UE-1.1-01 | yfinance returns malformed data, causing indicator calculation to fail | 2 | 3 | 6 |
| UE-1.1-02 | yfinance outage prevents data retrieval, halting pipeline | 2 | 4 | 8 |
| UE-1.2-01 | Insufficient data points causes InsufficientDataError, blocking decision | 2 | 3 | 6 |
| UE-1.3-01 | Invalid ticker bypasses validation, causing downstream API errors | 2 | 2 | 4 |
| UE-1.4-01 | Stale cache data leads to decision on outdated market conditions | 2 | 3 | 6 |
| UE-1.5-01 | Insufficient RSI history prevents dynamic threshold calculation | 2 | 2 | 4 |
| UE-1.6-01 | Missing fundamentals degrades LLM decision quality | 3 | 2 | 6 |
| UE-2.1-01 | Brave Search rate limiting thins headline set, reducing sentiment accuracy | 3 | 3 | 9 |
| UE-2.1-02 | No news found returns empty sentiment, affecting LLM input | 3 | 2 | 6 |
| UE-2.2-01 | FinBERT memory exhaustion crashes sentiment service | 2 | 4 | 8 |
| UE-2.2-02 | Empty text classification raises ClassifierError | 2 | 2 | 4 |
| UE-2.3-01 | No valid articles leaves sentiment undefined | 2 | 2 | 4 |
| UE-3.1-01 | Failed historical analysis forces fallback to static thresholds | 2 | 2 | 4 |
| UE-3.2-01 | False positive initial signal triggers unnecessary LLM call | 3 | 2 | 6 |
| UE-3.3-01 | Polling gap misses valid transition signal | 3 | 3 | 9 |
| UE-4.1-01 | Oversized prompt rejected by LLM, blocking decision | 1 | 3 | 3 |
| UE-4.2-01 | Ollama not running causes LLMConnectionError, halting strategy agent | 3 | 4 | 12 |
| UE-4.2-02 | Claude API failure blocks hosted LLM path | 2 | 3 | 6 |
| UE-4.2-03 | LLM timeout delays decision beyond market window | 2 | 3 | 6 |
| UE-4.3-01 | Unparseable LLM response raises DecisionParsingError | 2 | 3 | 6 |
| UE-5.1-01 | Overly conservative RSI check rejects valid trades | 2 | 2 | 4 |
| UE-5.2-01 | Static position limits block legitimate diversified trades | 2 | 2 | 4 |
| UE-5.3-01 | Frequent warnings reduce operator attention | 2 | 2 | 4 |
| UE-5.4-01 | Unreleased emergency halt blocks all trading indefinitely | 1 | 4 | 4 |
| UE-6.1-01 | Empty watchlist causes scheduler to run without purpose | 1 | 1 | 1 |
| UE-6.2-01 | Timezone error blocks valid trading sessions | 1 | 3 | 3 |
| UE-6.3-01 | Extended cooldown misses re-entry opportunities | 2 | 2 | 4 |
| UE-6.4-01 | Unhandled exception crashes pipeline, requiring manual restart | 2 | 4 | 8 |
| UE-7.1-01 | Uncontrolled benchmark inputs produce unreliable metrics | 2 | 2 | 4 |
| UE-7.2-01 | Oracle divergence invalidates rule fidelity measurements | 2 | 2 | 4 |
| UE-7.3-01 | Network variability skews latency benchmarks | 3 | 2 | 6 |
| UE-7.4-01 | False pass on failure probe masks error handling defects | 2 | 3 | 6 |

---

## 6. Risk Prioritization

| Priority | UE ID | Risk Score | Description |
|----------|-------|------------|-------------|
| 1 | UE-4.2-01 | 12 | Ollama not running causes LLMConnectionError |
| 2 | UE-2.1-01 | 9 | Brave Search rate limiting |
| 3 | UE-3.3-01 | 9 | Polling gap misses transition signal |
| 4 | UE-1.1-02 | 8 | yfinance outage halts pipeline |
| 5 | UE-2.2-01 | 8 | FinBERT memory exhaustion |
| 6 | UE-6.4-01 | 8 | Unhandled exception crashes pipeline |
| 7 | UE-1.1-01 | 6 | yfinance returns malformed data |
| 8 | UE-1.2-01 | 6 | Insufficient data for indicators |
| 9 | UE-1.4-01 | 6 | Stale cache data |
| 10 | UE-1.6-01 | 6 | Missing fundamentals |
| 11 | UE-2.1-02 | 6 | No news found |
| 12 | UE-3.2-01 | 6 | False positive initial signal |
| 13 | UE-4.2-02 | 6 | Claude API failure |
| 14 | UE-4.2-03 | 6 | LLM timeout |
| 15 | UE-4.3-01 | 6 | Unparseable LLM response |
| 16 | UE-7.3-01 | 6 | Network variability skews benchmarks |
| 17 | UE-7.4-01 | 6 | False pass on failure probe |

---

## 7. Risk Mitigation

| UE ID | Risk Mitigation | Classification |
|-------|-----------------|----------------|
| UE-4.2-01 | Provide Claude backend as alternative; document Ollama setup in README; smoke test validates import without Ollama | Pure Software |
| UE-2.1-01 | Cache recent results; implement backoff on BraveAPIRateLimitError; limit concurrent requests | Pure Software |
| UE-3.3-01 | Reduce polling interval for high-priority tickers; implement transition probability estimation | Pure Software |
| UE-1.1-02 | Wrap yfinance behind service layer; cache last-good payloads; offline smoke test validates logic | Pure Software |
| UE-2.2-01 | Run services sequentially when memory-constrained; Claude migration removes local FinBERT load | Pure Software |
| UE-6.4-01 | Per-ticker try/catch in scheduler; log errors without crashing loop; alert on repeated failures | Pure Software |
| UE-1.1-01 | Validate response structure in fetcher; raise typed DataIngestionError | Pure Software |
| UE-1.2-01 | Check data length before calculation; raise InsufficientDataError with clear message | Pure Software |
| UE-1.4-01 | Configurable cache TTL; invalidate cache on error; prefer fresh data for decisions | Pure Software |
| UE-1.6-01 | Graceful degradation — proceed with technicals + sentiment if fundamentals unavailable | Pure Software |
| UE-2.1-02 | Return neutral sentiment when no articles found; document limitation | Pure Software |
| UE-3.2-01 | Apply 10% tighter thresholds for initial entry; require stronger confirmation | Pure Software |
| UE-4.2-02 | Fall back to Ollama if Claude fails; monitor Claude console for quota | Pure Software |
| UE-4.2-03 | Configurable timeout; retry with exponential backoff; log slow queries | Pure Software |
| UE-4.3-01 | Fallback parsing scans full response; raise DecisionParsingError with context | Pure Software |
| UE-7.3-01 | Use fixed synthetic inputs for latency benchmarks; exclude network-bound stages | Pure Software |
| UE-7.4-01 | Document which probes require external dependencies stopped; manual verification step | Pure Software |

---

## 8. Functional Requirements

| Requirement ID | Level-2 Capability | Functional Requirement |
|----------------|-------------------|------------------------|
| FR-1.1.1 | 1.1 Fetch OHLCV Data | The Data Ingestion Service shall fetch OHLCV data for a validated ticker from yfinance within 10 seconds |
| FR-1.1.2 | 1.1 Fetch OHLCV Data | The Data Ingestion Service shall retry failed fetches up to 3 times with exponential backoff |
| FR-1.2.1 | 1.2 Calculate Technical Indicators | The Indicator Calculator shall compute 14-period RSI for the fetched price series |
| FR-1.2.2 | 1.2 Calculate Technical Indicators | The Indicator Calculator shall compute MACD (12/26/9) with signal line for the fetched price series |
| FR-1.3.1 | 1.3 Validate Ticker Symbols | The Ticker Validator shall reject empty, null, or malformed ticker symbols with a ValidationError |
| FR-1.4.1 | 1.4 Cache Market Data | The Data Cache shall store fetched data with a configurable TTL (default 300 seconds) |
| FR-1.4.2 | 1.4 Cache Market Data | The Data Cache shall return cached data when TTL has not expired |
| FR-1.5.1 | 1.5 Analyze Historical Patterns | The Historical Analyzer shall compute dynamic oversold/overbought thresholds from 1-year RSI statistics |
| FR-1.5.2 | 1.5 Analyze Historical Patterns | The Historical Analyzer shall require minimum 50 RSI periods for threshold calculation |
| FR-1.6.1 | 1.6 Fetch Fundamental Data | The Fundamentals Fetcher shall retrieve quarterly revenue, net income, and balance sheet metrics when available |
| FR-1.6.2 | 1.6 Fetch Fundamental Data | The Fundamentals Fetcher shall return "unavailable" for missing fields without raising exceptions |
| FR-2.1.1 | 2.1 Fetch Financial News | The News Fetcher shall query Brave Search API for ticker-related headlines |
| FR-2.1.2 | 2.1 Fetch Financial News | The News Fetcher shall return up to the requested count of articles (default 5) |
| FR-2.2.1 | 2.2 Classify Sentiment | The Sentiment Classifier shall apply FinBERT model to classify text as positive, negative, or neutral |
| FR-2.2.2 | 2.2 Classify Sentiment | The Sentiment Classifier shall truncate input text to 512 characters maximum |
| FR-2.3.1 | 2.3 Aggregate Sentiment Score | The Sentiment Aggregator shall compute overall sentiment from individual article classifications |
| FR-3.1.1 | 3.1 Initialize Dynamic Thresholds | The Signal Filter shall run historical analysis for all watchlist tickers at startup |
| FR-3.1.2 | 3.1 Initialize Dynamic Thresholds | The Signal Filter shall fall back to static thresholds (35/65) when analysis fails |
| FR-3.2.1 | 3.2 Detect Initial Entry Signals | The Signal Filter shall apply 10% tighter thresholds for first-poll entry decisions |
| FR-3.3.1 | 3.3 Detect Transition Signals | The Signal Filter shall detect RSI zone crossings compared to previous poll |
| FR-3.3.2 | 3.3 Detect Transition Signals | The Signal Filter shall detect MACD/signal line crossovers |
| FR-4.1.1 | 4.1 Build Decision Prompt | The Prompt Builder shall assemble market data, sentiment, and fundamentals into a structured prompt |
| FR-4.2.1 | 4.2 Query LLM Backend | The Strategy Agent shall support Ollama (local) and Claude (hosted) backends via configuration |
| FR-4.2.2 | 4.2 Query LLM Backend | The LLM Client shall query the configured backend and return the response text |
| FR-4.3.1 | 4.3 Parse Decision Response | The Strategy Agent shall extract BUY, SELL, or HOLD from the LLM response |
| FR-4.3.2 | 4.3 Parse Decision Response | The Strategy Agent shall raise DecisionParsingError when no valid decision is found |
| FR-5.1.1 | 5.1 Check RSI Extremes | The Risk Validator shall reject BUY decisions when RSI exceeds 80 |
| FR-5.1.2 | 5.1 Check RSI Extremes | The Risk Validator shall reject SELL decisions when RSI falls below 20 |
| FR-5.2.1 | 5.2 Enforce Position Size Limits | The Risk Validator shall reject trades where single share price exceeds max portfolio percentage (default 20%) |
| FR-5.3.1 | 5.3 Calculate Stop-Loss Impact | The Risk Validator shall warn when 5% stop-loss exceeds 2% of portfolio value |
| FR-5.4.1 | 5.4 Manage Emergency Halt | The Risk Validator shall block all trades when emergency halt is triggered |
| FR-5.4.2 | 5.4 Manage Emergency Halt | The Risk Validator shall resume trading when emergency halt is lifted |
| FR-6.1.1 | 6.1 Manage Watchlist | The Scheduler shall accept a configurable list of ticker symbols to monitor |
| FR-6.2.1 | 6.2 Enforce Market Hours | The Scheduler shall optionally restrict polling to US market hours (9:30 AM – 4:00 PM ET) |
| FR-6.3.1 | 6.3 Apply Decision Cooldown | The Scheduler shall prevent re-evaluation of a ticker for the cooldown period (default 4 hours) after a decision |
| FR-6.4.1 | 6.4 Execute Pipeline Iteration | The Trading Pipeline shall execute data ingestion, signal filtering, sentiment analysis, strategy generation, and risk validation in sequence |
| FR-7.1.1 | 7.1 Measure Decision Consistency | The consistency benchmark shall run identical inputs N times and report agreement percentage |
| FR-7.2.1 | 7.2 Evaluate Rule Fidelity | The rule fidelity benchmark shall compare LLM decisions against a deterministic rule oracle |
| FR-7.3.1 | 7.3 Profile Stage Latency | The latency benchmark shall time each pipeline stage independently |
| FR-7.4.1 | 7.4 Test Failure Handling | The failure probe benchmark shall verify typed exceptions for each fault scenario |

---

## 9. Quality Requirements

### 9.1 Performance

| ID | Requirement |
|----|-------------|
| QR-PERF-01 | The system shall complete a single-ticker pipeline iteration within 30 seconds under normal conditions |
| QR-PERF-02 | The LLM query (Ollama) shall return a decision within 20 seconds for typical prompts |
| QR-PERF-03 | The Claude API query shall return a decision within 10 seconds under normal load |

### 9.2 Reliability

| ID | Requirement |
|----|-------------|
| QR-REL-01 | The system shall handle external API failures gracefully without crashing |
| QR-REL-02 | The scheduler shall continue processing remaining tickers when one ticker fails |
| QR-REL-03 | The system shall maintain 221+ passing unit tests as a regression baseline |

### 9.3 Maintainability

| ID | Requirement |
|----|-------------|
| QR-MAIN-01 | The codebase shall follow single-responsibility principle (agents reason, services compute) |
| QR-MAIN-02 | External dependencies shall be wrapped behind thin abstraction layers |
| QR-MAIN-03 | Test suites shall mirror source layout under `tests/<component>/` |

### 9.4 Testability

| ID | Requirement |
|----|-------------|
| QR-TEST-01 | The system shall support offline smoke testing without external API keys or LLM runtime |
| QR-TEST-02 | Each component shall have dedicated unit tests with mocked dependencies |
| QR-TEST-03 | Benchmark experiments shall use fixed synthetic inputs for reproducibility |

### 9.5 Security

| ID | Requirement |
|----|-------------|
| QR-SEC-01 | API keys shall be stored in `.env` file (gitignored), not in source code |
| QR-SEC-02 | Only `.env.example` template shall be tracked in version control |
| QR-SEC-03 | No real financial transactions shall be executed by the system |

### 9.6 AI Explainability

| ID | Requirement |
|----|-------------|
| QR-AI-01 | The Strategy Agent shall return LLM reasoning alongside the decision |
| QR-AI-02 | The Risk Validator shall provide rejection/approval reasons for each decision |
| QR-AI-03 | The Signal Filter shall explain why a signal was or was not triggered |

### 9.7 AI Safety

| ID | Requirement |
|----|-------------|
| QR-AIS-01 | The system shall operate in simulation mode only; no real trades permitted |
| QR-AIS-02 | The Risk Validator shall gate all LLM decisions before simulated execution |
| QR-AIS-03 | Emergency halt capability shall immediately freeze all trading activity |

---

## 10. Performance Requirements

| ID | Metric | Target | Evidence |
|----|--------|--------|----------|
| PR-01 | Single-ticker pipeline latency | < 30 seconds | Stage latency benchmarks (`exp3_stage_latency.py`) |
| PR-02 | Ollama LLM response time | < 20 seconds | Benchmark results show mean ~4-8 seconds |
| PR-03 | Claude LLM response time | < 10 seconds | `exp1_consistency_claude.json`: mean 4.776s |
| PR-04 | FinBERT classification time | < 5 seconds per article | Benchmark coverage in exp3 |
| PR-05 | Data cache hit ratio | > 80% within TTL | Configurable 300s TTL in DataCache |
| PR-06 | Decision consistency (Claude) | 100% agreement on identical inputs | `exp1_consistency_claude.json`: 100% |
| PR-07 | Memory footprint (FinBERT + Ollama) | > **To Be Completed** | Known issue KI-08: memory-heavy on dev machine |

---

## 11. Assumptions

| ID | Assumption |
|----|------------|
| A-01 | Users have Python 3.11+ installed on their system |
| A-02 | Users can install and run Ollama locally (for local LLM backend) |
| A-03 | Users have access to Brave Search API key for sentiment analysis |
| A-04 | Internet connectivity is available for yfinance and Brave Search API calls |
| A-05 | The system operates in research/simulation context, not production trading |
| A-06 | US equity market hours (9:30 AM – 4:00 PM ET) are the relevant trading window |
| A-07 | yfinance provides reliable OHLCV data for major US equities |

---

## 12. Constraints

| ID | Constraint | Category |
|----|------------|----------|
| C-01 | Python 3.11+ required | Runtime |
| C-02 | Ollama required for local LLM backend (llama3.2 model) | Runtime |
| C-03 | Brave Search API key required for sentiment analysis | External Service |
| C-04 | Claude API key required for hosted LLM backend | External Service |
| C-05 | yfinance library for market data (no alternative data sources) | Library |
| C-06 | FinBERT model (ProsusAI/finbert) for sentiment classification | AI Model |
| C-07 | PyTorch and Transformers dependencies for FinBERT | Library |
| C-08 | Simulation only — no real brokerage integration | Design |
| C-09 | Command-line interface only — no web GUI | Interface |

---

## 13. External Interfaces

### 13.1 User Interfaces

| Interface | Description |
|-----------|-------------|
| Command Line | Primary interaction via `python main.py` and script runners |
| Console Output | Real-time logging of pipeline stages, decisions, and reasoning |

### 13.2 Software Interfaces

| Interface | Protocol | Purpose |
|-----------|----------|---------|
| yfinance API | HTTPS/REST | Fetch OHLCV and fundamental data |
| Brave Search API | HTTPS/REST | Fetch financial news headlines |
| Ollama API | HTTP (localhost:11434) | Local LLM query (llama3.2) |
| Claude API (Anthropic) | HTTPS/REST | Hosted LLM query (claude-sonnet-4-6) |
| Hugging Face Hub | HTTPS | Download FinBERT model weights |

### 13.3 External Services

| Service | Provider | Credentials |
|---------|----------|-------------|
| Market Data | Yahoo Finance (via yfinance) | None (public API) |
| Financial News | Brave Search | `BRAVE_API_KEY` |
| Local LLM | Ollama | None (local runtime) |
| Hosted LLM | Anthropic | `ANTHROPIC_API_KEY` |
| Sentiment Model | Hugging Face | None (public model) |

---

## 14. Requirements Traceability Matrix

| Requirement ID | Level-2 Capability | Requirement Description |
|----------------|-------------------|------------------------|
| FR-1.1.1 | 1.1 | Fetch OHLCV data within 10 seconds |
| FR-1.1.2 | 1.1 | Retry failed fetches up to 3 times |
| FR-1.2.1 | 1.2 | Compute 14-period RSI |
| FR-1.2.2 | 1.2 | Compute MACD (12/26/9) |
| FR-1.3.1 | 1.3 | Reject invalid ticker symbols |
| FR-1.4.1 | 1.4 | Store data with configurable TTL |
| FR-1.4.2 | 1.4 | Return cached data when valid |
| FR-1.5.1 | 1.5 | Compute dynamic thresholds from 1-year history |
| FR-1.5.2 | 1.5 | Require minimum 50 RSI periods |
| FR-1.6.1 | 1.6 | Retrieve quarterly financials |
| FR-1.6.2 | 1.6 | Graceful handling of missing fields |
| FR-2.1.1 | 2.1 | Query Brave Search API |
| FR-2.1.2 | 2.1 | Return up to N articles |
| FR-2.2.1 | 2.2 | Apply FinBERT classification |
| FR-2.2.2 | 2.2 | Truncate text to 512 characters |
| FR-2.3.1 | 2.3 | Compute overall sentiment |
| FR-3.1.1 | 3.1 | Run historical analysis at startup |
| FR-3.1.2 | 3.1 | Fall back to static thresholds |
| FR-3.2.1 | 3.2 | Apply tighter thresholds for first poll |
| FR-3.3.1 | 3.3 | Detect RSI zone crossings |
| FR-3.3.2 | 3.3 | Detect MACD crossovers |
| FR-4.1.1 | 4.1 | Assemble structured prompt |
| FR-4.2.1 | 4.2 | Support Ollama and Claude backends |
| FR-4.2.2 | 4.2 | Query backend and return response |
| FR-4.3.1 | 4.3 | Extract BUY/SELL/HOLD decision |
| FR-4.3.2 | 4.3 | Raise DecisionParsingError on failure |
| FR-5.1.1 | 5.1 | Reject BUY when RSI > 80 |
| FR-5.1.2 | 5.1 | Reject SELL when RSI < 20 |
| FR-5.2.1 | 5.2 | Enforce max portfolio percentage |
| FR-5.3.1 | 5.3 | Warn on excessive stop-loss impact |
| FR-5.4.1 | 5.4 | Block trades during emergency halt |
| FR-5.4.2 | 5.4 | Resume trading when halt lifted |
| FR-6.1.1 | 6.1 | Accept configurable watchlist |
| FR-6.2.1 | 6.2 | Optionally enforce market hours |
| FR-6.3.1 | 6.3 | Apply decision cooldown |
| FR-6.4.1 | 6.4 | Execute full pipeline sequence |
| FR-7.1.1 | 7.1 | Report decision agreement percentage |
| FR-7.2.1 | 7.2 | Compare against rule oracle |
| FR-7.3.1 | 7.3 | Time each pipeline stage |
| FR-7.4.1 | 7.4 | Verify typed exceptions |

---

## 15. Future Versions

### Version 1.0.0 (Planned — CISC 699)

- **Execution Simulator**: Record simulated trade entry/exit with P&L calculation
- **Portfolio Agent**: Convert user risk profile to watchlist and dynamic thresholds
- **CI/CD Pipeline**: GitHub Actions workflow for automated testing on push

### Version 2.0.0 (Future)

- **Web Dashboard**: Browser-based monitoring interface
- **Multi-user Support**: User authentication and profile management
- **Paper Trading Mode**: Integration with paper trading APIs (e.g., Alpaca sandbox)

### Version 3.0.0 (Future)

- **Backtesting Framework**: Historical strategy performance evaluation
- **Custom Indicator Support**: User-defined technical indicators
- **Alert System**: Email/SMS notifications for significant signals

---

## 16. Open Issues

| ID | Issue | Status |
|----|-------|--------|
| OI-01 | Execution Simulator not yet implemented (KI-06) | Open |
| OI-02 | Portfolio Agent not yet implemented (KI-07) | Open |
| OI-03 | Risk thresholds hardcoded (5%/20%) — should be profile-driven (KI-04) | Open |
| OI-04 | No automated CI — tests run locally only (KI-09) | Open |
| OI-05 | FinBERT memory footprint alongside Ollama on dev machine (KI-08) | Open |
| OI-06 | Specific performance baselines for PR-07 | > **To Be Completed** |
| OI-07 | Integration test coverage metrics | > **To Be Completed** |

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **Agent** | A specialized component that reasons about data and makes decisions (e.g., Strategy Agent, Risk Validator) |
| **CISC 699** | Graduate course continuation covering advanced implementation phases |
| **Claude** | Anthropic's hosted LLM service used as alternative backend to Ollama |
| **Cooldown** | Time period after a decision during which a ticker is not re-evaluated |
| **FinBERT** | Financial domain BERT model for sentiment classification (ProsusAI/finbert) |
| **GRAD 695** | Graduate course where core pipeline was developed |
| **HOLD** | Trading decision to maintain current position without action |
| **LLM** | Large Language Model — AI model for natural language reasoning |
| **MACD** | Moving Average Convergence Divergence — momentum indicator |
| **OHLCV** | Open, High, Low, Close, Volume — standard price data format |
| **Ollama** | Local LLM runtime for running models like llama3.2 |
| **Pipeline** | Sequence of stages (data → signal → sentiment → LLM → risk) for a single ticker |
| **RSI** | Relative Strength Index — momentum oscillator (0-100 scale) |
| **Scheduler** | Component managing watchlist polling and market hour enforcement |
| **Service** | A specialized component that computes/fetches data (e.g., Data Ingestion Service) |
| **Signal Filter** | Component that determines if market conditions warrant LLM consultation |
| **TTL** | Time To Live — cache expiration duration |
| **Watchlist** | List of ticker symbols monitored by the scheduler |
| **yfinance** | Python library for fetching Yahoo Finance market data |

---

*Document generated from repository analysis. All information is based on evidence from the codebase. Items marked "To Be Completed" require additional information not available in the repository.*
