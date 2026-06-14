import pytest
from agents.signal_filter import SignalFilter
from tests.signal_filter.conftest import make_market_data, make_baseline


class TestInitialization:

    def test_initialize_calls_analyzer_per_ticker(self, signal_filter, mock_analyzer):
        signal_filter.initialize(["AAPL", "MSFT", "TSLA"])
        assert mock_analyzer.analyze.call_count == 3

    def test_initialize_stores_baselines(self, signal_filter, mock_analyzer):
        signal_filter.initialize(["AAPL", "MSFT"])
        assert "AAPL" in signal_filter._baselines
        assert "MSFT" in signal_filter._baselines

    def test_initialize_uses_fallback_on_error(self, signal_filter, mock_analyzer):
        mock_analyzer.analyze.side_effect = Exception("API down")
        signal_filter.initialize(["AAPL"])
        # Should not raise — uses fallback thresholds
        assert signal_filter._baselines["AAPL"]["dynamic_oversold"] == 35.0
        assert signal_filter._baselines["AAPL"]["dynamic_overbought"] == 65.0


class TestFirstPoll:

    def test_first_poll_stores_state(self, signal_filter):
        data = make_market_data(rsi=50.0)
        signal_filter.check(data)
        assert "AAPL" in signal_filter._previous_state

    def test_first_poll_neutral_rsi_no_trigger(self, signal_filter):
        data = make_market_data(rsi=50.0)
        result = signal_filter.check(data)
        assert result["triggered"] is False
        assert result["signal_type"] == "NONE"

    def test_first_poll_deeply_oversold_triggers_buy(self, signal_filter):
        # dynamic_oversold is 35.0, tight = 35 * 0.9 = 31.5
        data = make_market_data(rsi=28.0, macd=1.0, signal=0.5)
        result = signal_filter.check(data)
        assert result["triggered"] is True
        assert result["signal_type"] == "BUY"

    def test_first_poll_deeply_overbought_triggers_sell(self, signal_filter):
        # dynamic_overbought is 65.0, tight = 65 * 1.1 = 71.5
        data = make_market_data(rsi=75.0, macd=0.3, signal=0.8)
        result = signal_filter.check(data)
        assert result["triggered"] is True
        assert result["signal_type"] == "SELL"

    def test_first_poll_oversold_but_bearish_macd_no_trigger(self, signal_filter):
        # RSI oversold but MACD not confirming
        data = make_market_data(rsi=28.0, macd=0.3, signal=0.8)
        result = signal_filter.check(data)
        assert result["triggered"] is False

    def test_first_poll_overbought_but_bullish_macd_no_trigger(self, signal_filter):
        data = make_market_data(rsi=75.0, macd=1.0, signal=0.5)
        result = signal_filter.check(data)
        assert result["triggered"] is False

    def test_first_poll_result_has_required_keys(self, signal_filter):
        data = make_market_data()
        result = signal_filter.check(data)
        assert "triggered"   in result
        assert "signal_type" in result
        assert "reason"      in result


class TestTransitionDetection:

    def _set_previous_state(self, signal_filter, data):
        """Helper — manually sets previous state to simulate second poll."""
        signal_filter._previous_state["AAPL"] = data

    def test_rsi_crosses_into_oversold_triggers_buy(self, signal_filter):
        # Previous: RSI above oversold threshold
        prev = make_market_data(rsi=38.0, macd=0.5, signal=0.3)
        self._set_previous_state(signal_filter, prev)
        # Current: RSI crossed below oversold threshold with bullish MACD
        curr = make_market_data(rsi=32.0, macd=0.6, signal=0.3)
        result = signal_filter.check(curr)
        assert result["triggered"] is True
        assert result["signal_type"] == "BUY"

    def test_rsi_crosses_into_overbought_triggers_sell(self, signal_filter):
        prev = make_market_data(rsi=62.0, macd=0.3, signal=0.5)
        self._set_previous_state(signal_filter, prev)
        curr = make_market_data(rsi=68.0, macd=0.2, signal=0.5)
        result = signal_filter.check(curr)
        assert result["triggered"] is True
        assert result["signal_type"] == "SELL"

    def test_macd_bullish_crossover_in_oversold_triggers_buy(self, signal_filter):
        # Previous: MACD below signal (bearish)
        prev = make_market_data(rsi=30.0, macd=0.2, signal=0.5)
        self._set_previous_state(signal_filter, prev)
        # Current: MACD crossed above signal (bullish crossover)
        curr = make_market_data(rsi=30.0, macd=0.6, signal=0.5)
        result = signal_filter.check(curr)
        assert result["triggered"] is True
        assert result["signal_type"] == "BUY"

    def test_macd_bearish_crossover_in_overbought_triggers_sell(self, signal_filter):
        prev = make_market_data(rsi=70.0, macd=0.8, signal=0.5)
        self._set_previous_state(signal_filter, prev)
        curr = make_market_data(rsi=70.0, macd=0.3, signal=0.5)
        result = signal_filter.check(curr)
        assert result["triggered"] is True
        assert result["signal_type"] == "SELL"

    def test_neutral_rsi_no_trigger(self, signal_filter):
        prev = make_market_data(rsi=50.0, macd=0.5, signal=0.3)
        self._set_previous_state(signal_filter, prev)
        curr = make_market_data(rsi=52.0, macd=0.6, signal=0.3)
        result = signal_filter.check(curr)
        assert result["triggered"] is False
        assert result["signal_type"] == "NONE"

    def test_oversold_rsi_but_bearish_macd_no_trigger(self, signal_filter):
        prev = make_market_data(rsi=32.0, macd=0.3, signal=0.5)
        self._set_previous_state(signal_filter, prev)
        curr = make_market_data(rsi=30.0, macd=0.2, signal=0.5)
        result = signal_filter.check(curr)
        assert result["triggered"] is False

    def test_previous_state_updated_after_each_poll(self, signal_filter):
        prev = make_market_data(rsi=50.0)
        self._set_previous_state(signal_filter, prev)
        curr = make_market_data(rsi=55.0)
        signal_filter.check(curr)
        assert signal_filter._previous_state["AAPL"]["rsi"] == 55.0


class TestDynamicThresholds:

    def test_uses_dynamic_oversold_from_baseline(self, signal_filter):
        # Set a custom baseline with tight oversold threshold
        signal_filter._baselines["AAPL"]["dynamic_oversold"] = 40.0
        prev = make_market_data(rsi=42.0, macd=0.3, signal=0.5)
        signal_filter._previous_state["AAPL"] = prev
        # RSI crossed below 40 with bullish MACD → should trigger
        curr = make_market_data(rsi=38.0, macd=0.6, signal=0.5)
        result = signal_filter.check(curr)
        assert result["triggered"] is True

    def test_uses_dynamic_overbought_from_baseline(self, signal_filter):
        signal_filter._baselines["AAPL"]["dynamic_overbought"] = 60.0
        prev = make_market_data(rsi=58.0, macd=0.3, signal=0.5)
        signal_filter._previous_state["AAPL"] = prev
        curr = make_market_data(rsi=62.0, macd=0.2, signal=0.5)
        result = signal_filter.check(curr)
        assert result["triggered"] is True

    def test_missing_baseline_uses_fallback(self, signal_filter):
        # MSFT has no baseline loaded
        data = make_market_data(ticker="MSFT", rsi=50.0)
        # Should not raise — uses fallback 35/65
        result = signal_filter.check(data)
        assert "triggered" in result


class TestReset:

    def test_reset_single_ticker_clears_state(self, signal_filter):
        signal_filter._previous_state["AAPL"] = make_market_data()
        signal_filter.reset("AAPL")
        assert "AAPL" not in signal_filter._previous_state

    def test_reset_single_ticker_clears_baseline(self, signal_filter):
        signal_filter.reset("AAPL")
        assert "AAPL" not in signal_filter._baselines

    def test_reset_all_clears_everything(self, signal_filter):
        signal_filter._previous_state["AAPL"] = make_market_data()
        signal_filter._previous_state["MSFT"] = make_market_data(ticker="MSFT")
        signal_filter.reset()
        assert len(signal_filter._previous_state) == 0
        assert len(signal_filter._baselines) == 0