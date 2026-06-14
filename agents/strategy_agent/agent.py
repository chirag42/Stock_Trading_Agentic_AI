import logging
from .prompt_builder import PromptBuilder
from .llm_client     import LLMClient
from .exceptions     import DecisionParsingError

logger = logging.getLogger("StrategyAgent")

VALID_DECISIONS = {"BUY", "SELL", "HOLD"}


class StrategyAgent:

    def __init__(self, model: str = "llama3.2"):
        self.prompt_builder = PromptBuilder()
        self.llm_client     = LLMClient(model=model)

    def _parse_decision(self, llm_response: str) -> str:
        """
        Extracts the Buy/Sell/Hold decision from the first
        word of the LLM response.
        Raises DecisionParsingError if no valid decision found.
        """
        first_word = llm_response.strip().split()[0].upper()
        first_word = first_word.strip(".,!?")

        if first_word in VALID_DECISIONS:
            return first_word

        # Fallback — scan the whole response for a valid decision
        for word in llm_response.upper().split():
            cleaned = word.strip(".,!?")
            if cleaned in VALID_DECISIONS:
                logger.warning(
                    f"Decision not in first word — found '{cleaned}' "
                    f"further in response."
                )
                return cleaned

        raise DecisionParsingError(
            f"Could not parse a valid decision (BUY/SELL/HOLD) "
            f"from LLM response: '{llm_response[:100]}'"
        )

    def decide(self, market_data: dict, sentiment_data: dict) -> dict:
        """
        Main entry point.
        Takes market and sentiment data, returns a structured
        trading decision with full reasoning.
        """
        ticker = market_data.get("ticker", "UNKNOWN")
        logger.info(f"Running Strategy Agent for {ticker}...")

        # Build prompt
        prompt = self.prompt_builder.build(market_data, sentiment_data)

        # Query LLM
        llm_response = self.llm_client.query(prompt)

        # Parse decision
        decision = self._parse_decision(llm_response)

        return {
            "ticker":       ticker,
            "decision":     decision,
            "llm_reasoning": llm_response,
            "market_data":  market_data,
            "sentiment":    {
                "overall":  sentiment_data["overall"],
                "positive": sentiment_data["positive"],
                "negative": sentiment_data["negative"],
                "neutral":  sentiment_data["neutral"],
            }
        }