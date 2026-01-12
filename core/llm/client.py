"""
Gemini LLM client wrapper.

Provides a simple interface for interacting with Google's Gemini API.
"""

import json
import logging
import re
from typing import Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_TEMPERATURE,
    LLM_REQUEST_TIMEOUT,
)
from .exceptions import (
    LLMError,
    LLMConfigurationError,
    LLMResponseError,
    LLMConnectionError,
    RateLimitExceeded,
)
from .rate_limiter import check_rate_limit, increment_rate_limit

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Wrapper for Google Gemini API.

    Provides methods for generating text and JSON responses with built-in
    rate limiting and error handling.

    Usage:
        from core.llm import gemini_client

        # Simple generation
        response = gemini_client.generate("Tell me a joke")

        # JSON generation with rate limiting
        plan = gemini_client.generate_json(
            prompt="Create a workout plan",
            user_id=user.id
        )
    """

    def __init__(self):
        self._model = None
        self._configured = False

    def _ensure_configured(self) -> None:
        """Ensure the client is configured with API key."""
        if self._configured:
            return

        if not GEMINI_API_KEY:
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not set. Please add it to your .env file."
            )

        genai.configure(api_key=GEMINI_API_KEY)
        self._model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                max_output_tokens=LLM_MAX_OUTPUT_TOKENS,
                temperature=LLM_TEMPERATURE,
            ),
        )
        self._configured = True
        logger.info(f"Gemini client configured with model: {GEMINI_MODEL}")

    def generate(
        self,
        prompt: str,
        user_id: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a text response from the LLM.

        Args:
            prompt: The user prompt to send to the LLM.
            user_id: Optional user ID for rate limiting.
            system_prompt: Optional system prompt to prepend.

        Returns:
            Generated text response.

        Raises:
            LLMConfigurationError: If API key is not configured.
            RateLimitExceeded: If user has exceeded their rate limit.
            LLMConnectionError: If connection to Gemini fails.
            LLMError: For other LLM-related errors.
        """
        self._ensure_configured()

        # Check rate limit if user_id provided
        if user_id:
            check_rate_limit(user_id)

        try:
            # Prepare the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

            # Generate response
            response = self._model.generate_content(
                full_prompt,
                request_options={"timeout": LLM_REQUEST_TIMEOUT},
            )

            # Increment rate limit counter on success
            if user_id:
                increment_rate_limit(user_id)

            # Extract text from response
            if response.text:
                return response.text.strip()
            else:
                raise LLMResponseError("Empty response from LLM")

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"Gemini API rate limit hit: {e}")
            raise RateLimitExceeded("Gemini API rate limit exceeded. Please try again later.")
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Invalid argument to Gemini API: {e}")
            raise LLMError(f"Invalid request: {e}")
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error: {e}")
            raise LLMConnectionError(f"Failed to connect to Gemini API: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during LLM generation: {e}")
            raise LLMError(f"Unexpected error: {e}")

    def generate_json(
        self,
        prompt: str,
        user_id: int | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a JSON response from the LLM.

        The prompt should instruct the LLM to respond with valid JSON.

        Args:
            prompt: The user prompt (should request JSON output).
            user_id: Optional user ID for rate limiting.
            system_prompt: Optional system prompt to prepend.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            LLMResponseError: If response is not valid JSON.
            (Plus all exceptions from generate())
        """
        response = self.generate(prompt, user_id, system_prompt)

        try:
            # Try to extract JSON from response (handles markdown code blocks)
            json_str = self._extract_json(response)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
            raise LLMResponseError(f"LLM response is not valid JSON: {e}")

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks.

        Args:
            text: Raw text that may contain JSON.

        Returns:
            Extracted JSON string.
        """
        # Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if json_match:
            return json_match.group(1).strip()

        # Try to find raw JSON object or array
        json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if json_match:
            return json_match.group(1).strip()

        # Return as-is and let JSON parser handle it
        return text.strip()

    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(GEMINI_API_KEY)


# Singleton instance for convenience
gemini_client = GeminiClient()

