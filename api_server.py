"""
Research API — HTTP surface for the Agentic AI Stock Trading decision engine.

This turns the research pipeline into a standalone service. It exposes a small
set of ATOMIC endpoints (indicators, quote, chart, news, sentiment, fundamentals)
plus the trading DECISION. Consumers (the backend middleware) decide which of
these to call and how to combine them — this service stays simple and single-purpose.

Run:
    uvicorn api_server:app --reload --port 8001
"""
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import yfinance as yf

from services.data_ingestion import DataIngestionService
from services.sentiment_analysis import SentimentAnalysisService
from services.sentiment_analysis.fetcher import NewsFetcher
from agents.strategy_agent import StrategyAgent

try:
    from services.data_ingestion.fundamentals import (
        FundamentalsFetcher, format_fundamentals_for_prompt,
    )
    _HAS_FUNDAMENTALS = True
except Exception:  # noqa: BLE001
    _HAS_FUNDAMENTALS = False

import os

LLM_BACKEND = os.getenv("LLM_BACKEND", "claude")

app = FastAPI(title="Agentic AI Stock Trading — Research API", version="1.0.0")

# Heavy singletons built once
_data = DataIngestionService(cache_ttl=240)
_sentiment = SentimentAnalysisService()
_news = NewsFetcher()
_agent = StrategyAgent(backend=LLM_BACKEND)
_fundamentals = FundamentalsFetcher() if _HAS_FUNDAMENTALS else None


def _fund_block(ticker: str) -> Optional[str]:
    if _fundamentals is None:
        return None
    try:
        return format_fundamentals_for_prompt(_fundamentals.fetch(ticker))
    except Exception:  # noqa: BLE001
        return None


# ── Schemas ───────────────────────────────────────────────────────
class Position(BaseModel):
    shares: float
    avg_price: float


class DecisionRequest(BaseModel):
    ticker: str
    position: Optional[Position] = None   # if present → position-aware SELL/HOLD


# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "backend": LLM_BACKEND}


# ── Atomic data endpoints ─────────────────────────────────────────
@app.get("/indicators/{ticker}")
def indicators(ticker: str):
    try:
        return _data.get_latest_summary(ticker.upper())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"No data for {ticker}: {exc}")


@app.get("/quote/{ticker}")
def quote(ticker: str):
    """Current price + day change % from the last two closes."""
    ticker = ticker.upper()
    h = yf.Ticker(ticker).history(period="2d")
    if h is None or h.empty:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")
    closes = [float(x) for x in h["Close"].tolist() if x == x]
    if not closes:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")
    price = round(closes[-1], 2)
    prev = closes[-2] if len(closes) >= 2 else price
    change_pct = round((price - prev) / prev * 100, 2) if prev else 0.0
    return {"ticker": ticker, "price": price, "change_pct": change_pct}


@app.get("/chart/{ticker}")
def chart(ticker: str, period: str = "3mo"):
    df = yf.Ticker(ticker.upper()).history(period=period)
    if df is None or df.empty:
        return {"ticker": ticker.upper(), "points": []}
    points = [{"date": idx.strftime("%Y-%m-%d"), "close": round(float(row), 2)}
              for idx, row in df["Close"].items()]
    return {"ticker": ticker.upper(), "points": points}


@app.get("/news/{ticker}")
def news(ticker: str, count: int = 8):
    try:
        articles = _news.fetch(ticker.upper(), count)
    except Exception:  # noqa: BLE001
        articles = []
    return {"ticker": ticker.upper(),
            "articles": [{"title": a.get("title", ""),
                          "description": a.get("description", ""),
                          "url": a.get("url", "")} for a in articles]}


@app.get("/sentiment/{ticker}")
def sentiment(ticker: str):
    try:
        return _sentiment.get_aggregated_sentiment(ticker.upper())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Sentiment failed for {ticker}: {exc}")


@app.get("/fundamentals/{ticker}")
def fundamentals(ticker: str):
    block = _fund_block(ticker.upper())
    return {"ticker": ticker.upper(), "block": block, "available": block is not None}


# ── The decision (research's core job) ────────────────────────────
def _parse_sell_hold(text: str) -> str:
    first = text.strip().split()[0].upper().strip(".,!?") if text.strip() else ""
    if first in {"SELL", "HOLD"}:
        return first
    for w in text.upper().split():
        if w.strip(".,!?") in {"SELL", "HOLD"}:
            return w.strip(".,!?")
    return "HOLD"


@app.post("/decision")
def decision(req: DecisionRequest):
    ticker = req.ticker.upper()
    try:
        market = _data.get_latest_summary(ticker)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"No data for {ticker}: {exc}")

    sent = _sentiment.get_aggregated_sentiment(ticker)
    fund = _fund_block(ticker)

    # Opportunity decision (no position) → full BUY/SELL/HOLD via the pipeline agent
    if req.position is None:
        result = _agent.decide(market, sent, fund)
        return {"ticker": ticker, "decision": result["decision"],
                "reasoning": result["llm_reasoning"], "backend": LLM_BACKEND}

    # Position-aware decision (SELL or HOLD only)
    price = round(float(market["close_price"]), 2)
    avg = req.position.avg_price
    pnl = ((price - avg) / avg * 100) if avg else 0.0
    prompt = "\n".join([
        "You are a portfolio advisor. The user ALREADY OWNS this position.",
        f"POSITION: {req.position.shares} shares of {ticker}, bought at ${avg}, "
        f"now ${price} ({pnl:+.1f}% profit/loss).",
        "",
        "TECHNICAL INDICATORS",
        f"RSI: {market['rsi']}   MACD: {market['macd']} vs Signal {market['signal']}",
        "",
        "MARKET SENTIMENT",
        f"Overall: {sent['overall'].upper()} "
        f"({sent['positive']}+/{sent['negative']}- of {sent['articles_analyzed']})",
        "",
        (fund or "FUNDAMENTALS\n(unavailable)"),
        "",
        "DECISION RULES",
        "- Recommend SELL to exit if indicators, sentiment, or risk suggest it.",
        "- Recommend HOLD to keep the position otherwise.",
        "- Only SELL or HOLD — the user already owns this; BUY is not an option.",
        "",
        "YOUR TASK",
        "1. First line must be exactly one word: SELL or HOLD",
        "2. Give 2-3 short reasons (mention the profit/loss where relevant)",
        "3. Mention one key risk",
    ])
    resp = _agent.llm_client.query(prompt)
    return {"ticker": ticker, "decision": _parse_sell_hold(resp), "reasoning": resp,
            "pnl_pct": round(pnl, 2), "current_price": price, "backend": LLM_BACKEND}
