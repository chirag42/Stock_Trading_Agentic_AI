from .exceptions import InvalidTickerError

class TickerValidator:

    VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}

    def validate_ticker(self, ticker: str) -> str:
        if not isinstance(ticker, str):
            raise InvalidTickerError(
                f"Ticker must be a string, got {type(ticker)}"
            )
        ticker = ticker.strip().upper()
        if not ticker:
            raise InvalidTickerError("Ticker symbol cannot be empty.")
        if len(ticker) > 10:
            raise InvalidTickerError(
                f"Ticker '{ticker}' is too long — max 10 characters."
            )
        if not ticker.replace(".", "").replace("-", "").isalnum():
            raise InvalidTickerError(
                f"Ticker '{ticker}' contains invalid characters."
            )
        return ticker

    def validate_period(self, period: str) -> None:
        if period not in self.VALID_PERIODS:
            raise ValueError(
                f"Invalid period '{period}'. Choose from: {self.VALID_PERIODS}"
            )