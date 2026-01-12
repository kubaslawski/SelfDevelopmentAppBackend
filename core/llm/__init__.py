"""
LLM infrastructure module.

Provides a unified interface for interacting with LLM providers (currently Gemini).

Usage:
    from core.llm import gemini_client

    response = gemini_client.generate("Your prompt here")
    json_response = gemini_client.generate_json("Generate a plan", user_id=user.id)
"""

from .client import GeminiClient, gemini_client
from .exceptions import LLMError, RateLimitExceeded, LLMConfigurationError

__all__ = [
    "GeminiClient",
    "gemini_client",
    "LLMError",
    "RateLimitExceeded",
    "LLMConfigurationError",
]

