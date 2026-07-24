import time
import logging
from datetime import datetime
import pytz

from pipeline import TradingPipeline
from agents.signal_filter import SignalFilter

logger = logging.getLogger("Scheduler")

WATCHLIST             = ["AAPL", "MSFT", "TSLA"]
POLL_INTERVAL_SECONDS = 300
MARKET_OPEN_HOUR      = 9
MARKET_OPEN_MIN       = 30
MARKET_CLOSE_HOUR     = 16
MARKET_CLOSE_MIN      = 0
COOLDOWN_SECONDS      = 14400


class Scheduler:

    def __init__(self, watchlist=None, poll_interval=POLL_INTERVAL_SECONDS, backend="ollama"):
        self.watchlist = watchlist or WATCHLIST
        self.poll_interval = poll_interval
        self.backend = backend
        self.signal_filter = SignalFilter()
        self.pipeline      = TradingPipeline(signal_filter=self.signal_filter, backend=self.backend)
        self.last_decision: dict = {}

    def _initialize(self) -> None:
        """
        Runs historical analysis for all tickers before
        live polling begins. Sets dynamic thresholds.
        """
        self.signal_filter.initialize(self.watchlist)

    def _is_market_open(self) -> bool:
        et_tz = pytz.timezone("America/New_York")
        now   = datetime.now(et_tz)
        if now.weekday() >= 5:
            return False
        market_open  = now.replace(hour=MARKET_OPEN_HOUR,  minute=MARKET_OPEN_MIN,  second=0)
        market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0)
        return market_open <= now <= market_close

    def _is_on_cooldown(self, ticker: str) -> bool:
        if ticker not in self.last_decision:
            return False
        elapsed = time.time() - self.last_decision[ticker]
        return elapsed < COOLDOWN_SECONDS

    def _run_once(self) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] Polling {len(self.watchlist)} tickers...")

        for ticker in self.watchlist:
            if self._is_on_cooldown(ticker):
                elapsed   = time.time() - self.last_decision[ticker]
                remaining = int((COOLDOWN_SECONDS - elapsed) / 60)
                print(f"  [{ticker}] On cooldown — {remaining} min remaining")
                continue

            try:
                result = self.pipeline.run(ticker)
                if result.get("decision") not in ("SKIP", "HOLD"):
                    self.last_decision[ticker] = time.time()
                    logger.info(
                        f"[{ticker}] Decision: {result['decision']} "
                        f"— cooldown started"
                    )
            except Exception as exc:
                logger.error(f"[{ticker}] Pipeline error: {exc}")

    def start(self, respect_market_hours: bool = True) -> None:
        print("\n" + "="*55)
        print("  AGENTIC AI TRADING SYSTEM — LIVE")
        print(f"  Watching: {', '.join(self.watchlist)}")
        print(f"  Poll interval: {self.poll_interval // 60} minutes")
        print(f"  Cooldown: {COOLDOWN_SECONDS // 3600} hours after decision")
        print("="*55)

        # Always run historical analysis before polling starts
        self._initialize()

        while True:
            if respect_market_hours and not self._is_market_open():
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] Market is closed — waiting...")
                time.sleep(60)
                continue

            self._run_once()
            print(f"\nNext poll in {self.poll_interval // 60} minutes...")
            time.sleep(self.poll_interval)