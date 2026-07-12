"""
services/data_ingestion/fundamentals.py

Pulls fundamental context (quarterly results, balance-sheet health, valuation, and
earnings timing) to enrich the LLM's decision input. Everything degrades gracefully:
Yahoo/yfinance data is often missing or partial for a given ticker, so every field is
extracted defensively and absent values are reported as "unavailable" rather than
raising. The goal is to give the LLM richer material to reason over WITHOUT making the
pipeline depend on any single field being present.

Design mirrors MarketDataFetcher (retry/backoff, per-component logger, typed errors).

Public API:
    FundamentalsFetcher().fetch(ticker) -> dict            # structured fundamentals
    format_fundamentals_for_prompt(data) -> str            # prompt-ready text block
"""

import logging
import time
from datetime import datetime, timezone

import yfinance as yf

from .exceptions import DataIngestionError

logger = logging.getLogger("Fundamentals")

UNAVAILABLE = "unavailable"

# yfinance row labels vary; try several known variants for each concept.
REVENUE_KEYS = ["Total Revenue", "TotalRevenue", "Operating Revenue"]
NET_INCOME_KEYS = ["Net Income", "NetIncome", "Net Income Common Stockholders"]
DEBT_KEYS = ["Total Debt", "TotalDebt"]
CASH_KEYS = ["Cash And Cash Equivalents", "CashAndCashEquivalents", "Cash Cash Equivalents And Short Term Investments"]
EQUITY_KEYS = ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"]


def _first_row(df, keys):
    """Return the first matching row (as a list of values, newest first) or None."""
    if df is None or getattr(df, "empty", True):
        return None
    for k in keys:
        if k in df.index:
            try:
                vals = [v for v in df.loc[k].tolist() if v == v]  # drop NaN
                if vals:
                    return vals
            except Exception:  # noqa: BLE001
                continue
    return None


def _trend(values):
    """Describe direction of a newest-first numeric series."""
    if not values or len(values) < 2:
        return UNAVAILABLE
    newest, oldest = values[0], values[-1]
    if oldest == 0:
        return UNAVAILABLE
    change = (newest - oldest) / abs(oldest)
    if change > 0.03:
        return "rising"
    if change < -0.03:
        return "declining"
    return "roughly flat"


def _safe(info, key):
    try:
        v = info.get(key)
        return v if v is not None else None
    except Exception:  # noqa: BLE001
        return None


class FundamentalsFetcher:
    def __init__(self, max_retries: int = 2, backoff_base: float = 2.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def fetch(self, ticker: str) -> dict:
        """Return a structured fundamentals dict. Never raises on missing data;
        only raises DataIngestionError if the ticker object itself can't be built."""
        ticker = (ticker or "").strip().upper()
        if not ticker:
            raise DataIngestionError("Empty ticker for fundamentals fetch.")

        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching fundamentals for {ticker} (attempt {attempt}/{self.max_retries})")
                t = yf.Ticker(ticker)
                return self._assemble(ticker, t)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning(f"Fundamentals attempt {attempt} failed: {type(exc).__name__}: {exc}")
                if attempt < self.max_retries:
                    time.sleep(self.backoff_base ** attempt)

        # If even the Ticker object failed, surface a typed error; caller can proceed
        # on technicals + news alone.
        raise DataIngestionError(f"Could not fetch fundamentals for '{ticker}': {last_exc}")

    def _assemble(self, ticker: str, t) -> dict:
        # --- info (valuation + profile); the flakiest call, guarded hard ---
        try:
            info = t.info or {}
        except Exception:  # noqa: BLE001
            info = {}

        # --- quarterly financials (revenue / net income trend) ---
        try:
            qf = t.quarterly_financials
        except Exception:  # noqa: BLE001
            qf = None
        revenue = _first_row(qf, REVENUE_KEYS)
        net_income = _first_row(qf, NET_INCOME_KEYS)

        # --- balance sheet (debt / cash / equity) ---
        try:
            bs = t.quarterly_balance_sheet
            if bs is None or getattr(bs, "empty", True):
                bs = t.balance_sheet
        except Exception:  # noqa: BLE001
            bs = None
        debt = _first_row(bs, DEBT_KEYS)
        cash = _first_row(bs, CASH_KEYS)
        equity = _first_row(bs, EQUITY_KEYS)

        # --- earnings timing ---
        next_earnings, days_to_earnings = self._earnings_timing(t)

        # --- derive readable signals ---
        latest_rev = revenue[0] if revenue else None
        latest_ni = net_income[0] if net_income else None
        net_margin = (latest_ni / latest_rev) if (latest_rev not in (None, 0) and latest_ni is not None) else None
        d, e = (debt[0] if debt else None), (equity[0] if equity else None)
        debt_to_equity = (d / e) if (d is not None and e not in (None, 0)) else _safe(info, "debtToEquity")

        return {
            "ticker": ticker,
            "sector": _safe(info, "sector") or UNAVAILABLE,
            "revenue_trend": _trend(revenue),
            "net_income_trend": _trend(net_income),
            "net_margin_pct": round(net_margin * 100, 1) if net_margin is not None else UNAVAILABLE,
            "debt_to_equity": round(debt_to_equity, 2) if isinstance(debt_to_equity, (int, float)) else UNAVAILABLE,
            "cash_on_hand": cash[0] if cash else UNAVAILABLE,
            "trailing_pe": _safe(info, "trailingPE") or UNAVAILABLE,
            "price_to_book": _safe(info, "priceToBook") or UNAVAILABLE,
            "market_cap": _safe(info, "marketCap") or UNAVAILABLE,
            "analyst_target_mean": _safe(info, "targetMeanPrice") or UNAVAILABLE,
            "next_earnings_date": next_earnings or UNAVAILABLE,
            "days_to_earnings": days_to_earnings if days_to_earnings is not None else UNAVAILABLE,
        }

    def _earnings_timing(self, t):
        try:
            cal = t.calendar
            dt = None
            if isinstance(cal, dict):
                ed = cal.get("Earnings Date")
                dt = ed[0] if isinstance(ed, (list, tuple)) and ed else ed
            else:  # DataFrame
                if cal is not None and not cal.empty and "Earnings Date" in cal.index:
                    dt = cal.loc["Earnings Date"].iloc[0]
            if dt is None:
                return None, None
            if hasattr(dt, "to_pydatetime"):
                dt = dt.to_pydatetime()
            if isinstance(dt, datetime):
                today = datetime.now(timezone.utc).date()
                d = dt.date() if hasattr(dt, "date") else dt
                return d.isoformat(), (d - today).days
            return str(dt), None
        except Exception:  # noqa: BLE001
            return None, None


def _fmt_money(v):
    if not isinstance(v, (int, float)):
        return str(v)
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if abs(v) >= size:
            return f"${v / size:.1f}{unit}"
    return f"${v:,.0f}"


def format_fundamentals_for_prompt(data: dict) -> str:
    """Render a compact, LLM-friendly fundamentals block. Absent fields are shown as
    'unavailable' so the model knows to reason without them rather than assume."""
    if not data:
        return "FUNDAMENTALS\n(unavailable — deciding on technicals and news alone)"

    de = data.get("days_to_earnings")
    earnings_note = ""
    if isinstance(de, int):
        if 0 <= de <= 5:
            earnings_note = f"  [!] earnings in {de} days — elevated event risk"
        elif de < 0:
            earnings_note = "  (earnings recently reported)"

    lines = [
        "FUNDAMENTALS",
        f"Sector: {data.get('sector')}",
        f"Revenue trend (recent quarters): {data.get('revenue_trend')}",
        f"Net income trend: {data.get('net_income_trend')}",
        f"Net margin: {data.get('net_margin_pct')}%"
        if data.get("net_margin_pct") != UNAVAILABLE else "Net margin: unavailable",
        f"Debt-to-equity: {data.get('debt_to_equity')}",
        f"Cash on hand: {_fmt_money(data.get('cash_on_hand'))}",
        f"Valuation: P/E {data.get('trailing_pe')}, P/B {data.get('price_to_book')}, "
        f"market cap {_fmt_money(data.get('market_cap'))}",
        f"Analyst mean target: {data.get('analyst_target_mean')}",
        f"Next earnings: {data.get('next_earnings_date')}{earnings_note}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    sym = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    fetcher = FundamentalsFetcher()
    try:
        d = fetcher.fetch(sym)
        print("\n--- structured ---")
        for k, v in d.items():
            print(f"  {k}: {v}")
        print("\n--- prompt block ---")
        print(format_fundamentals_for_prompt(d))
    except DataIngestionError as exc:
        print(f"[fundamentals unavailable] {exc}")
