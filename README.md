# Agentic AI Stock Trading System

A research-based multi-agent AI system that simulates autonomous stock trading. 
Specialized AI agents collaborate to analyze market data, process financial news, 
generate trading strategies, and validate risk — entirely in simulation with no real money involved.

## Overview

Instead of a single model making all decisions, this system uses a **team of specialized agents**, 
each responsible for one part of the trading pipeline. This mirrors how a real trading desk works — 
a data analyst, a news analyst, a strategist, and a risk manager all working together.

## System Architecture
```
User Input (Stock Ticker)
        ↓
Data Ingestion Agent      → Fetches real-time OHLCV prices + calculates RSI/MACD
        ↓
Sentiment Analysis Agent  → Fetches news via Brave Search API + classifies with FinBERT
        ↓
Strategy Agent (LLM)      → Combines signals → generates Buy / Sell / Hold decision
        ↓
Risk Validator            → Checks decision against portfolio risk limits
        ↓
Execution Simulator       → Records simulated trade + calculates P&L
```

## Services

### Data Ingestion Service (`services/data_ingestion.py`)
- Connects to **yfinance** to fetch real-time and historical OHLCV data
- Calculates **RSI** (Relative Strength Index) to detect overbought/oversold conditions
- Calculates **MACD** (Moving Average Convergence Divergence) to detect trend momentum
- Implements exponential backoff for API rate limit handling

### Sentiment Analysis Service (`services/sentiment_analysis.py`)
- Calls **Brave Search API** to fetch recent financial news for a given ticker
- Runs each headline through **FinBERT** (a finance-specific NLP model) 
- Classifies news as `positive`, `negative`, or `neutral`
- Returns an aggregated sentiment score via majority vote

### Strategy Agent (`agents/strategy_agent.py`) — In Progress
- Combines technical indicators from Data Ingestion with sentiment scores
- Uses a **locally running LLM via Ollama** (llama3.2) for reasoning
- Outputs a trading decision: `BUY`, `SELL`, or `HOLD` with justification

### Risk Validator (`agents/risk_validator.py`) — Planned
- Validates every proposed trade against predefined risk policies
- Applies maximum loss thresholds to prevent excessive drawdown
- Can trigger an emergency halt during critical failures

### Execution Simulator (`services/execution_simulator.py`) — Planned
- Records simulated trade entry and exit prices
- Calculates profit/loss (P&L) for each session
- Feeds results back to Strategy Agent for self-correction

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Market Data | yfinance |
| News API | Brave Search API |
| Sentiment NLP | FinBERT (ProsusAI/finbert) |
| Local LLM | Ollama + llama3.2 |
| Agent Orchestration | LangChain / CrewAI |
| Vector Memory | ChromaDB |
| Structured Storage | PostgreSQL |
| API Layer | FastAPI |

## Project Structure
```
stock-trading-ai/
├── agents/
│   ├── __init__.py
│   ├── strategy_agent.py      # LLM-powered decision making
│   └── risk_validator.py      # Trade validation
├── services/
│   ├── __init__.py
│   ├── data_ingestion.py      # Market data + indicators
│   ├── sentiment_analysis.py  # News + FinBERT
│   └── execution_simulator.py # Simulated trade execution
├── utils/
│   └── __init__.py
├── data/
├── .env                       # API keys (never committed)
├── .gitignore
└── README.md
```

## Setup

### Prerequisites
- Python 3.11+
- Ollama (for local LLM)

### Installation
```bash
# Clone the repo
git clone https://github.com/chirag42/Stock_Trading_Agentic_AI.git
cd Stock_Trading_Agentic_AI

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install yfinance pandas numpy requests transformers torch
pip install langchain langgraph chromadb psycopg2-binary python-dotenv fastapi uvicorn

# Install Ollama and pull the model
# Download Ollama from ollama.com, then:
ollama pull llama3.2
```

### Environment Variables

Create a `.env` file in the project root:
```
BRAVE_API_KEY=your_brave_api_key_here
```

### Running Individual Services
```bash
# Test Data Ingestion
python services/data_ingestion.py

# Test Sentiment Analysis
python services/sentiment_analysis.py
```

## Current Status

| Component | Status |
|-----------|--------|
| Software Requirements Specification (SRS) | ✅ Complete |
| High-Level Design (HLD) | ✅ Complete |
| Low-Level Design (LLD) | ✅ Complete |
| Data Ingestion Service | ✅ Complete |
| Sentiment Analysis Service | ✅ Complete |
| Strategy Agent (Local LLM) | 🔄 In Progress |
| Risk Validator | 📋 Planned |
| Execution Simulator | 📋 Planned |
| Dashboard UI | 📋 Planned |


**Disclaimer:** This system is a research simulation only. It does not provide 
financial advice and does not involve real money or real brokerage integration.
