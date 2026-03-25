class RiskValidator:

    def __init__(self, max_loss_pct: float = 0.05, max_portfolio_pct: float = 0.20):
        """
        max_loss_pct      — max loss allowed on a single trade (default 5%)
        max_portfolio_pct — max % of portfolio allowed in one stock (default 20%)
        """
        self.max_loss_pct = max_loss_pct
        self.max_portfolio_pct = max_portfolio_pct
        self.is_halted = False

    def validate_trade(self, decision: str, ticker: str, current_price: float,
                       portfolio_value: float, rsi: float) -> dict:
        """
        Main method — validates a proposed trade decision.
        Returns approval status + reason.
        """
        print(f"\nRisk Validator checking trade: {decision} {ticker} @ ${current_price}")

        # Emergency halt check — overrides everything
        if self.is_halted:
            return self._reject("System is under emergency halt. No trades allowed.")

        # Only validate BUY or SELL — HOLD needs no validation
        if decision.upper() == "HOLD":
            return self._approve("HOLD decision requires no risk validation.")

        # Rule 1 — Extreme RSI check
        # If RSI > 80 and we're trying to BUY, that's dangerously overbought
        # If RSI < 20 and we're trying to SELL, that's dangerously oversold
        if decision.upper() == "BUY" and rsi > 80:
            return self._reject(
                f"RSI is {rsi} — extremely overbought. Buying here is too risky."
            )
        if decision.upper() == "SELL" and rsi < 20:
            return self._reject(
                f"RSI is {rsi} — extremely oversold. Selling here locks in excessive loss."
            )

        # Rule 2 — Position size check
        # Max amount allowed in one stock = portfolio_value * max_portfolio_pct
        max_allowed = portfolio_value * self.max_portfolio_pct
        print(f"  Max allowed position size: ${max_allowed:,.2f}")

        if current_price > max_allowed:
            return self._reject(
                f"Single share price (${current_price}) exceeds max position "
                f"limit (${max_allowed:,.2f}). Reduce portfolio concentration."
            )

        # Rule 3 — Stop loss check
        # Calculate what a 5% drop from current price would mean in dollars
        potential_loss = current_price * self.max_loss_pct
        print(f"  Potential loss at {self.max_loss_pct*100}% stop: ${potential_loss:,.2f}")

        # If even one share's loss exceeds 2% of portfolio, flag it
        if potential_loss > (portfolio_value * 0.02):
            return self._warn(
                f"Trade approved but note: a {self.max_loss_pct*100}% stop loss "
                f"on this position = ${potential_loss:,.2f}. "
                f"Consider smaller position size."
            )

        return self._approve(
            f"Trade passes all risk checks. "
            f"Max loss capped at ${potential_loss:,.2f} with stop loss."
        )

    def trigger_emergency_halt(self):
        """Freezes all trading activity immediately."""
        self.is_halted = True
        print("EMERGENCY HALT TRIGGERED — all trading frozen.")

    def lift_emergency_halt(self):
        """Lifts the emergency halt."""
        self.is_halted = False
        print("Emergency halt lifted. Trading resumed.")

    def _approve(self, reason: str) -> dict:
        print(f"  APPROVED: {reason}")
        return {"approved": True, "status": "APPROVED", "reason": reason}

    def _warn(self, reason: str) -> dict:
        print(f"  APPROVED WITH WARNING: {reason}")
        return {"approved": True, "status": "WARNING", "reason": reason}

    def _reject(self, reason: str) -> dict:
        print(f"  REJECTED: {reason}")
        return {"approved": False, "status": "REJECTED", "reason": reason}


# --- Quick test ---
if __name__ == "__main__":
    validator = RiskValidator(max_loss_pct=0.05, max_portfolio_pct=0.20)

    # Simulating output from Strategy Agent
    test_cases = [
        {"decision": "BUY",  "ticker": "MSFT", "price": 372.74, "portfolio": 10000, "rsi": 20.69},
        {"decision": "BUY",  "ticker": "AAPL", "price": 210.00, "portfolio": 10000, "rsi": 82.0},
        {"decision": "SELL", "ticker": "TSLA", "price": 180.00, "portfolio": 10000, "rsi": 18.0},
        {"decision": "HOLD", "ticker": "NVDA", "price": 850.00, "portfolio": 10000, "rsi": 55.0},
    ]

    print("\n" + "="*55)
    print("RISK VALIDATOR TEST RESULTS")
    print("="*55)

    for t in test_cases:
        result = validator.validate_trade(
            decision=t["decision"],
            ticker=t["ticker"],
            current_price=t["price"],
            portfolio_value=t["portfolio"],
            rsi=t["rsi"]
        )
        print(f"  → Status: {result['status']}")
        print()