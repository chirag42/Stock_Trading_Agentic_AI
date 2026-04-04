class DataIngestionError(Exception):
    pass

class InvalidTickerError(DataIngestionError):
    pass

class InsufficientDataError(DataIngestionError):
    pass

class APIRateLimitError(DataIngestionError):
    pass

class StaleDataError(DataIngestionError):
    pass