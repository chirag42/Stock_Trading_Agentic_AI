from .exceptions import InvalidMarketDataError, InvalidSentimentDataError

REQUIRED_MARKET_FIELDS   = {"ticker", "close_price", "rsi", "macd", "signal"}
REQUIRED_SENTIMENT_FIELDS = {"overall", "positive", "negative", "neutral", "articles_analyzed"}


class PromptBuilder:

    def validate_market_data(self, market_data: dict) -> None:
        missing = REQUIRED_MARKET_FIELDS - set(market_data.keys())
        if missing:
            raise InvalidMarketDataError(
                f"Market data missing required fields: {missing}"
            )
        if not isinstance(market_data["rsi"], (int, float)):
            raise InvalidMarketDataError("RSI must be a number.")
        if not (0 <= market_data["rsi"] <= 100):
            raise InvalidMarketDataError(
                f"RSI value {market_data['rsi']} is out of range (0-100)."
            )

    def validate_sentiment_data(self, sentiment_data: dict) -> None:
        missing = REQUIRED_SENTIMENT_FIELDS - set(sentiment_data.keys())
        if missing:
            raise InvalidSentimentDataError(
                f"Sentiment data missing required fields: {missing}"
            )
        valid_labels = {"positive", "negative", "neutral"}
        if sentiment_data["overall"] not in valid_labels:
            raise InvalidSentimentDataError(
                f"Invalid sentiment label '{sentiment_data['overall']}'. "
                f"Must be one of {valid_labels}."
            )

    def build(self, market_data: dict, sentiment_data: dict,
              fundamentals_block: str = None) -> str:
        """
        Validates inputs and builds a structured prompt for the LLM strategy decision.

        fundamentals_block is OPTIONAL. When omitted (e.g. in benchmarks), the prompt is
        identical to the technicals+sentiment version, so benchmark results stay
        comparable. When provided (live pipeline), a FUNDAMENTALS section and two extra
        handling rules are added — fundamentals inform reasoning and risk, not the
        decision rules themselves.
        """
        self.validate_market_data(market_data)
        self.validate_sentiment_data(sentiment_data)

        ticker  = market_data["ticker"]
        price   = market_data["close_price"]
        rsi     = market_data["rsi"]
        macd    = market_data["macd"]
        signal  = market_data["signal"]

        overall   = sentiment_data["overall"].upper()
        positive  = sentiment_data["positive"]
        negative  = sentiment_data["negative"]
        neutral   = sentiment_data["neutral"]
        total     = sentiment_data["articles_analyzed"]

        if rsi > 70:
            rsi_hint = "overbought — potential sell signal"
        elif rsi < 30:
            rsi_hint = "oversold — potential buy signal"
        else:
            rsi_hint = "neutral range"

        macd_hint = "bullish crossover" if macd > signal else "bearish crossover"

        lines = [
            f"You are a financial analysis AI assistant.",
            f"Analyze the following data for {ticker} and make a trading decision.",
            "",
            "TECHNICAL INDICATORS",
            f"Current Price: ${price}",
            f"RSI: {rsi} ({rsi_hint})",
            f"MACD: {macd} ({macd_hint})",
            f"Signal Line: {signal}",
            "",
            "MARKET SENTIMENT",
            f"Overall Sentiment: {overall}",
            f"Positive Articles: {positive}/{total}",
            f"Negative Articles: {negative}/{total}",
            f"Neutral Articles:  {neutral}/{total}",
        ]

        # Optional fundamentals section — only added when provided.
        if fundamentals_block:
            lines += ["", fundamentals_block]

        lines += [
            "",
            "DECISION RULES — FOLLOW STRICTLY",
            "- Recommend BUY  only when: RSI is oversold (< 35) AND MACD is bullish crossover",
            "- Recommend SELL only when: RSI is overbought (> 65) AND MACD is bearish crossover",
            "- Recommend HOLD when: signals are mixed, unclear, or do not meet above criteria",
            "- When in doubt, always default to HOLD — never force a BUY or SELL",
        ]

        # Extra handling rules only when fundamentals are present, so the base prompt
        # (and therefore benchmark behavior) is unchanged when they are not.
        if fundamentals_block:
            lines += [
                "- Use FUNDAMENTALS and earnings timing to inform your REASONING and the "
                "RISK you flag — not to override the decision rules above.",
                "- If a fundamentals field is 'unavailable', do NOT assume a value; reason "
                "only from the data that is present.",
            ]

        lines += [
            "",
            "YOUR TASK",
            "1. First line must be exactly one word: BUY, SELL, or HOLD",
            "2. Give 2-3 short reasons for your decision",
            "3. Mention one key risk",
            "4. If recommending HOLD, explain what conditions would change your decision",
            "Keep your response concise and structured.",
        ]
        return "\n".join(lines)
