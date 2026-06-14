class StrategyAgentError(Exception):
    """Base exception for all strategy agent failures."""
    pass

class LLMConnectionError(StrategyAgentError):
    """Raised when Ollama is not running or unreachable."""
    pass

class LLMResponseError(StrategyAgentError):
    """Raised when LLM returns an empty or unparseable response."""
    pass

class InvalidMarketDataError(StrategyAgentError):
    """Raised when market data input is missing required fields."""
    pass

class InvalidSentimentDataError(StrategyAgentError):
    """Raised when sentiment data input is missing required fields."""
    pass

class DecisionParsingError(StrategyAgentError):
    """Raised when LLM response cannot be parsed into Buy/Sell/Hold."""
    pass