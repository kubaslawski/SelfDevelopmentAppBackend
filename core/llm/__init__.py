"""
LLM module for AI interactions using Google Gemini.

Usage:
    from core.llm import gemini_client

    # Generate text response
    response = gemini_client.generate("Hello, what's 2+2?")

    # Generate JSON response
    data = gemini_client.generate_json(
        "Return JSON with 3 questions",
        system_prompt="You are a helpful assistant"
    )
"""

from .client import GeminiClient, gemini_client
from .exceptions import (
    LLMConfigurationError,
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    RateLimitExceeded,
)

__all__ = [
    # Client
    "GeminiClient",
    "gemini_client",
    # Exceptions
    "LLMError",
    "LLMConfigurationError",
    "LLMConnectionError",
    "LLMResponseError",
    "RateLimitExceeded",
]
