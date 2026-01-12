"""
Custom exceptions for LLM module.
"""


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMConfigurationError(LLMError):
    """Raised when LLM is not properly configured (e.g., missing API key)."""

    pass


class RateLimitExceeded(LLMError):
    """Raised when user has exceeded their LLM usage rate limit."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after  # seconds until rate limit resets


class LLMResponseError(LLMError):
    """Raised when LLM returns an invalid or unparseable response."""

    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM provider fails."""

    pass

