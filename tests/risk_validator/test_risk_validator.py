"""Tests for RiskValidator — covers every decision branch and the halt lifecycle."""
import pytest
from agents.risk_validator import RiskValidator


@pytest.fixture
def validator():
    return RiskValidator(max_loss_pct=0.05, max_portfolio_pct=0.20)


class TestInitialization:
    def test_defaults(self):
        v = RiskValidator()
        assert v.max_loss_pct == 0.05
        assert v.max_portfolio_pct == 0.20
        assert v.is_halted is False

    def test_custom_thresholds(self):
        v = RiskValidator(max_loss_pct=0.10, max_portfolio_pct=0.30)
        assert v.max_loss_pct == 0.10
        assert v.max_portfolio_pct == 0.30


class TestHoldAndHalt:
    def test_hold_needs_no_validation(self, validator):
        r = validator.validate_trade("HOLD", "NVDA", 850.0, 10000, 55.0)
        assert r["approved"] is True
        assert r["status"] == "APPROVED"

    def test_hold_is_case_insensitive(self, validator):
        r = validator.validate_trade("hold", "NVDA", 850.0, 10000, 55.0)
        assert r["approved"] is True

    def test_emergency_halt_blocks_all_trades(self, validator):
        validator.trigger_emergency_halt()
        assert validator.is_halted is True
        r = validator.validate_trade("BUY", "MSFT", 100.0, 100000, 50.0)
        assert r["approved"] is False
        assert r["status"] == "REJECTED"
        assert "halt" in r["reason"].lower()

    def test_lift_halt_resumes_trading(self, validator):
        validator.trigger_emergency_halt()
        validator.lift_emergency_halt()
        assert validator.is_halted is False
        r = validator.validate_trade("BUY", "MSFT", 100.0, 100000, 50.0)
        assert r["approved"] is True


class TestExtremeRSI:
    def test_buy_blocked_when_overbought(self, validator):
        r = validator.validate_trade("BUY", "AAPL", 210.0, 10000, 82.0)
        assert r["approved"] is False
        assert "overbought" in r["reason"].lower()

    def test_sell_blocked_when_oversold(self, validator):
        r = validator.validate_trade("SELL", "TSLA", 180.0, 10000, 18.0)
        assert r["approved"] is False
        assert "oversold" in r["reason"].lower()

    def test_buy_allowed_at_rsi_boundary_80(self, validator):
        # rsi > 80 triggers; exactly 80 should pass the RSI rule
        r = validator.validate_trade("BUY", "MSFT", 100.0, 100000, 80.0)
        assert r["approved"] is True

    def test_sell_allowed_at_rsi_boundary_20(self, validator):
        r = validator.validate_trade("SELL", "MSFT", 100.0, 100000, 20.0)
        assert r["approved"] is True


class TestPositionSize:
    def test_reject_when_share_price_exceeds_max_position(self, validator):
        # max_allowed = 10000 * 0.20 = 2000; price 2500 > 2000 → reject
        r = validator.validate_trade("BUY", "BRK", 2500.0, 10000, 50.0)
        assert r["approved"] is False
        assert "exceeds max position" in r["reason"].lower()


class TestStopLoss:
    def test_warning_when_stop_loss_large_relative_to_portfolio(self, validator):
        # price 100, max_loss 5% → potential loss 5; portfolio 200 → 2% = 4; 5 > 4 → WARNING
        r = validator.validate_trade("BUY", "MSFT", 100.0, 200, 50.0)
        # position-size rule first: max_allowed = 200*0.2 = 40; price 100 > 40 → rejected before stop-loss
        assert r["status"] in {"REJECTED", "WARNING"}

    def test_pure_warning_path(self, validator):
        # Choose numbers so position-size passes but stop-loss warns:
        # portfolio 1000 → max_allowed 200 (price must be < 200)
        # potential_loss = price*0.05; portfolio*0.02 = 20 → need price*0.05 > 20 → price > 400
        # can't have price < 200 and > 400, so use custom validator with higher max_portfolio_pct
        v = RiskValidator(max_loss_pct=0.05, max_portfolio_pct=0.80)
        # portfolio 1000 → max_allowed 800; price 500 < 800 ok; loss=25 > 20 → WARNING
        r = v.validate_trade("BUY", "MSFT", 500.0, 1000, 50.0)
        assert r["status"] == "WARNING"
        assert r["approved"] is True

    def test_clean_approve_path(self, validator):
        # price 100, portfolio 100000: max_allowed 20000 ok; loss=5 < 2000 → clean APPROVED
        r = validator.validate_trade("BUY", "MSFT", 100.0, 100000, 50.0)
        assert r["status"] == "APPROVED"
        assert "passes all risk checks" in r["reason"].lower()
