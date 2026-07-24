import logging
from services.data_ingestion     import DataIngestionService
from services.sentiment_analysis import SentimentAnalysisService
from services.data_ingestion.fundamentals import (
    FundamentalsFetcher, format_fundamentals_for_prompt
)
from agents.strategy_agent       import StrategyAgent
from agents.signal_filter        import SignalFilter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("Pipeline")


class TradingPipeline:

    def __init__(self, signal_filter: SignalFilter = None, backend: str = "ollama"):
        self.data_svc      = DataIngestionService(cache_ttl=240)
        self.sentiment_svc = SentimentAnalysisService()
        self.fundamentals_fetcher = FundamentalsFetcher()
        self.agent         = StrategyAgent(backend=backend) 
        # Use shared signal filter from scheduler if provided
        # otherwise create a fresh one
        self.signal_filter = signal_filter or SignalFilter()

    def run(self, ticker: str) -> dict:
        ticker = ticker.upper().strip()
        logger.info(f"Pipeline starting for {ticker}")

        # ── Step 1 — Fetch market data ─────────────────────────
        print(f"\n[1/4] Fetching market data for {ticker}...")
        market_data = self.data_svc.get_latest_summary(ticker)
        print(f"      Price : ${market_data['close_price']}")
        print(f"      RSI   : {market_data['rsi']} ({market_data['rsi_signal']})")
        print(f"      MACD  : {market_data['macd']} ({market_data['macd_signal']})")

        # ── Step 2 — Signal filter ─────────────────────────────
        signal = self.signal_filter.check(market_data)

        if not signal["triggered"]:
            print(f"\n      Signal too weak — skipping LLM")
            print(f"      Reason: {signal['reason']}")
            return {
                "ticker":      ticker,
                "decision":    "SKIP",
                "reason":      signal["reason"],
                "market_data": market_data
            }

        print(f"\n      STRONG {signal['signal_type']} SIGNAL DETECTED")
        print(f"      Reason: {signal['reason']}")

        # ── Step 3 — Sentiment analysis ────────────────────────
        print(f"\n[2/4] Fetching sentiment for {ticker}...")
        sentiment_data = self.sentiment_svc.get_aggregated_sentiment(ticker)
        print(f"      Overall    : {sentiment_data['overall'].upper()}")
        print(f"      Positive   : {sentiment_data['positive']}/{sentiment_data['articles_analyzed']}")
        print(f"      Negative   : {sentiment_data['negative']}/{sentiment_data['articles_analyzed']}")
        print(f"      Confidence : {sentiment_data['avg_confidence']}")

        # ── Step 3.5 — Fundamentals (best-effort; never blocks the decision) ──
        print(f"\n[3/4] Fetching fundamentals for {ticker}...")
        try:
            fundamentals = self.fundamentals_fetcher.fetch(ticker)
            fundamentals_block = format_fundamentals_for_prompt(fundamentals)
            print(f"      Fundamentals loaded (sector: {fundamentals.get('sector')}, "
                  f"revenue trend: {fundamentals.get('revenue_trend')})")
        except Exception as exc:
            fundamentals_block = format_fundamentals_for_prompt({})
            print(f"      Fundamentals unavailable ({type(exc).__name__}) — "
                  f"deciding on technicals + sentiment")

        # ── Step 4 — Strategy agent ────────────────────────────
        print(f"\n[4/4] Querying Strategy Agent (LLM)...")
        result = self.agent.decide(market_data, sentiment_data, fundamentals_block)

        print(f"\n{'='*55}")
        print(f"  DECISION for {ticker}: *** {result['decision']} ***")
        print(f"{'='*55}")
        print(f"\n  LLM REASONING:")
        print(f"  {result['llm_reasoning']}")
        print(f"\n{'='*55}\n")

        return result
