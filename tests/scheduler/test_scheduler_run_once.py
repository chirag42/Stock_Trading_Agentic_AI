"""FinBERT-safe tests for Scheduler._run_once — pipeline injected, no model load."""
import time
from unittest.mock import MagicMock
from core.scheduler import Scheduler


def _sched(watchlist):
    s = Scheduler.__new__(Scheduler)
    s.watchlist = watchlist
    s.poll_interval = 300
    s.last_decision = {}
    s.pipeline = MagicMock()
    s.signal_filter = MagicMock()
    return s


def test_actionable_decision_starts_cooldown():
    s = _sched(["AAPL"])
    s.pipeline.run.return_value = {"ticker": "AAPL", "decision": "BUY"}
    s._run_once()
    assert "AAPL" in s.last_decision   # cooldown timestamp recorded


def test_hold_does_not_start_cooldown():
    s = _sched(["AAPL"])
    s.pipeline.run.return_value = {"ticker": "AAPL", "decision": "HOLD"}
    s._run_once()
    assert "AAPL" not in s.last_decision


def test_pipeline_error_does_not_crash():
    s = _sched(["AAPL"])
    s.pipeline.run.side_effect = Exception("boom")
    s._run_once()   # must not raise
    assert "AAPL" not in s.last_decision


def test_ticker_on_cooldown_is_skipped():
    s = _sched(["AAPL"])
    s.last_decision["AAPL"] = time.time()   # fresh cooldown
    s._run_once()
    s.pipeline.run.assert_not_called()
