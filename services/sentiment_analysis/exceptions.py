class SentimentAnalysisError(Exception):
    """Base exception for all sentiment analysis failures."""
    pass

class BraveAPIError(SentimentAnalysisError):
    """Raised when Brave Search API returns an error or unexpected response."""
    pass

class BraveAPIRateLimitError(BraveAPIError):
    """Raised when Brave Search API rate limit is hit."""
    pass

class NoArticlesFoundError(SentimentAnalysisError):
    """Raised when no news articles are found for a ticker."""
    pass

class ClassifierError(SentimentAnalysisError):
    """Raised when FinBERT fails to classify text."""
    pass

class InvalidTickerError(SentimentAnalysisError):
    """Raised when ticker symbol is invalid."""
    pass