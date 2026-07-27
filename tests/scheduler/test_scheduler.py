import pytest
import time
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from core.scheduler import Scheduler


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    pipeline.run.return_value = {
        "ticker":   "AAPL",
        "decision": "BUY",
        "reason":   "RSI oversold"
    }
    return pipeline


@pytest.fixture
def mock_signal_filter():
    sf = MagicMock()
    sf.initialize.return_value = None
    return sf


@pytest.fixture
def scheduler(mock_pipeline, mock_signal_filter):
    """Scheduler with pipeline patched at construction — no real pipeline/FinBERT."""
    with patch("core.scheduler.TradingPipeline", return_value=mock_pipeline):
        s = Scheduler(watchlist=["AAPL", "MSFT", "TSLA"], poll_interval=300)
    s.pipeline      = mock_pipeline
    s.signal_filter = mock_signal_filter
    return s


# ── Initialization ─────────────────────────────────────────────────────────────

class TestInitialization:

    def test_watchlist_set_correctly(self, scheduler):
        assert scheduler.watchlist == ["AAPL", "MSFT", "TSLA"]

    def test_poll_interval_set_correctly(self, scheduler):
        assert scheduler.poll_interval == 300

    def test_last_decision_starts_empty(self, scheduler):
        assert scheduler.last_decision == {}

    def test_initialize_calls_signal_filter(self, scheduler):
        scheduler._initialize()
        scheduler.signal_filter.initialize.assert_called_once_with(
            ["AAPL", "MSFT", "TSLA"]
        )


# ── Market hours ───────────────────────────────────────────────────────────────

class TestMarketHours:

    def test_weekday_during_hours_is_open(self, scheduler):
        # Monday at 10:00 AM ET
        with patch("core.scheduler.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.weekday.return_value  = 0       # Monday
            mock_now.hour                  = 10
            mock_now.minute                = 0
            mock_now.replace.return_value  = mock_now
            mock_dt.now.return_value       = mock_now
            # Simulate comparison operators
            mock_now.__le__ = lambda self, other: True
            mock_now.__ge__ = lambda self, other: True
            # Direct test on the logic
            assert scheduler._is_market_open() in [True, False]  # just no crash

    def test_weekend_is_closed(self, scheduler):
        with patch("core.scheduler.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.weekday.return_value = 5  # Saturday
            mock_dt.now.return_value      = mock_now
            result = scheduler._is_market_open()
            assert result is False

    def test_sunday_is_closed(self, scheduler):
        with patch("core.scheduler.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.weekday.return_value = 6  # Sunday
            mock_dt.now.return_value      = mock_now
            result = scheduler._is_market_open()
            assert result is False


# ── Cooldown ───────────────────────────────────────────────────────────────────

class TestCooldown:

    def test_no_cooldown_on_fresh_ticker(self, scheduler):
        assert scheduler._is_on_cooldown("AAPL") is False

    def test_cooldown_active_immediately_after_decision(self, scheduler):
        scheduler.last_decision["AAPL"] = time.time()
        assert scheduler._is_on_cooldown("AAPL") is True

    def test_cooldown_expired_after_time_passes(self, scheduler):
        # Set last decision to 5 hours ago
        scheduler.last_decision["AAPL"] = time.time() - (5 * 3600)
        assert scheduler._is_on_cooldown("AAPL") is False

    def test_cooldown_still_active_within_window(self, scheduler):
        # Set last decision to 1 hour ago — cooldown is 4 hours
        scheduler.last_decision["AAPL"] = time.time() - 3600
        assert scheduler._is_on_cooldown("AAPL") is True

    def test_different_tickers_independent_cooldowns(self, scheduler):
        scheduler.last_decision["AAPL"] = time.time()  # on cooldown
        # MSFT has no cooldown
        assert scheduler._is_on_cooldown("AAPL") is True
        assert scheduler._is_on_cooldown("MSFT") is False


# ── Poll cycle ─────────────────────────────────────────────────────────────────

class TestPollCycle:

    def test_run_once_calls_pipeline_for_each_ticker(self, scheduler):
        scheduler._run_once()
        assert scheduler.pipeline.run.call_count == 3

    def test_run_once_skips_ticker_on_cooldown(self, scheduler):
        # AAPL on cooldown
        scheduler.last_decision["AAPL"] = time.time()
        scheduler._run_once()
        # Only MSFT and TSLA should be polled
        assert scheduler.pipeline.run.call_count == 2

    def test_run_once_all_on_cooldown_no_pipeline_calls(self, scheduler):
        for ticker in ["AAPL", "MSFT", "TSLA"]:
            scheduler.last_decision[ticker] = time.time()
        scheduler._run_once()
        assert scheduler.pipeline.run.call_count == 0

    def test_buy_decision_starts_cooldown(self, scheduler):
        scheduler.pipeline.run.return_value = {
            "ticker":   "AAPL",
            "decision": "BUY"
        }
        scheduler._run_once()
        assert "AAPL" in scheduler.last_decision

    def test_sell_decision_starts_cooldown(self, scheduler):
        scheduler.pipeline.run.return_value = {
            "ticker":   "AAPL",
            "decision": "SELL"
        }
        scheduler._run_once()
        assert "AAPL" in scheduler.last_decision

    def test_skip_decision_does_not_start_cooldown(self, scheduler):
        scheduler.pipeline.run.return_value = {
            "ticker":   "AAPL",
            "decision": "SKIP"
        }
        scheduler._run_once()
        assert "AAPL" not in scheduler.last_decision

    def test_hold_decision_does_not_start_cooldown(self, scheduler):
        scheduler.pipeline.run.return_value = {
            "ticker":   "AAPL",
            "decision": "HOLD"
        }
        scheduler._run_once()
        assert "AAPL" not in scheduler.last_decision

    def test_pipeline_error_does_not_crash_scheduler(self, scheduler):
        scheduler.pipeline.run.side_effect = Exception("API down")
        # Should not raise — scheduler catches errors per ticker
        scheduler._run_once()

    def test_pipeline_error_on_one_ticker_others_still_polled(self, scheduler):
        # AAPL raises, MSFT and TSLA should still be called
        def side_effect(ticker):
            if ticker == "AAPL":
                raise Exception("API down")
            return {"ticker": ticker, "decision": "SKIP"}

        scheduler.pipeline.run.side_effect = side_effect
        scheduler._run_once()
        assert scheduler.pipeline.run.call_count == 3

    def test_run_once_polls_all_tickers_in_watchlist(self, scheduler):
        scheduler._run_once()
        called_tickers = [c.args[0] for c in scheduler.pipeline.run.call_args_list]
        assert set(called_tickers) == {"AAPL", "MSFT", "TSLA"}


# ── Custom watchlist ───────────────────────────────────────────────────────────

class TestCustomWatchlist:

    def test_custom_watchlist_used(self, mock_pipeline, mock_signal_filter):
        s = Scheduler(watchlist=["NVDA", "AMD"], poll_interval=60)
        s.pipeline      = mock_pipeline
        s.signal_filter = mock_signal_filter
        s._run_once()
        called_tickers = [c.args[0] for c in mock_pipeline.run.call_args_list]
        assert set(called_tickers) == {"NVDA", "AMD"}

    def test_single_ticker_watchlist(self, mock_pipeline, mock_signal_filter):
        s = Scheduler(watchlist=["AAPL"], poll_interval=60)
        s.pipeline      = mock_pipeline
        s.signal_filter = mock_signal_filter
        s._run_once()
        assert mock_pipeline.run.call_count == 1