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
    LLM_REQUEST_TIMEOUT,
    LLM_TEMPERATURE,
)
from .exceptions import (
    LLMConfigurationError,
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    RateLimitExceeded,
)
from .rate_limiter import check_rate_limit, increment_rate_limit

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Wrapper for Google Gemini API.

    Provides methods for generating text and JSON responses with built-in
    rate limiting and error handling.
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

            # Count input tokens
            try:
                token_count = self._model.count_tokens(full_prompt)
                input_tokens = token_count.total_tokens
            except Exception:
                input_tokens = len(full_prompt) // 4  # Rough estimate

            # Log the prompt being sent
            logger.info("=" * 60)
            logger.info("LLM REQUEST")
            logger.info("=" * 60)
            logger.info(f"📥 INPUT TOKENS: {input_tokens}")
            logger.info(f"⚙️  MAX OUTPUT TOKENS: {LLM_MAX_OUTPUT_TOKENS}")
            if system_prompt:
                logger.info(
                    f"System Prompt:\n{system_prompt[:500]}{'...' if len(system_prompt) > 500 else ''}"
                )
            logger.info(f"User Prompt:\n{prompt[:1000]}{'...' if len(prompt) > 1000 else ''}")
            logger.info("-" * 60)

            # Generate response
            response = self._model.generate_content(
                full_prompt,
                request_options={"timeout": LLM_REQUEST_TIMEOUT},
            )

            # Increment rate limit counter on success
            if user_id:
                increment_rate_limit(user_id)

            # Extract token usage from response
            output_tokens = 0
            total_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0)

            # Extract text from response
            if response.text:
                response_text = response.text.strip()

                # Log the response with token counts
                logger.info("LLM RESPONSE")
                logger.info("=" * 60)
                logger.info(f"📥 INPUT TOKENS: {input_tokens}")
                logger.info(f"📤 OUTPUT TOKENS: {output_tokens}")
                logger.info(f"📊 TOTAL TOKENS: {total_tokens}")
                logger.info(f"📝 RESPONSE LENGTH: {len(response_text)} chars")
                logger.info("-" * 60)
                logger.info(
                    f"Response:\n{response_text[:2000]}{'...' if len(response_text) > 2000 else ''}"
                )
                logger.info("=" * 60)

                return response_text
            else:
                logger.warning("LLM returned empty response")
                raise LLMResponseError("Empty response from LLM")

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"Gemini API rate limit hit: {e}")
            logger.info("=" * 60)
            raise RateLimitExceeded("Gemini API rate limit exceeded. Please try again later.")
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Invalid argument to Gemini API: {e}")
            logger.info("=" * 60)
            raise LLMError(f"Invalid request: {e}")
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error: {e}")
            logger.info("=" * 60)
            raise LLMConnectionError(f"Failed to connect to Gemini API: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during LLM generation: {e}")
            logger.info("=" * 60)
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

        # Try to extract JSON from response (handles markdown code blocks)
        json_str = self._extract_json(response)

        try:
            parsed = json.loads(json_str)
            logger.debug(
                f"Successfully parsed JSON response with keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'array'}"
            )
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            logger.warning("Attempting to repair JSON...")

            # Try to repair truncated JSON
            repaired = self._repair_json(json_str)
            try:
                parsed = json.loads(repaired)
                logger.info("✅ JSON repaired successfully!")
                return parsed
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse LLM response as JSON: {e2}")
                logger.error(f"Raw response length: {len(response)} chars")
                logger.error(f"Last 500 chars of response:\n{response[-500:]}")
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

    def _repair_json(self, json_str: str) -> str:
        """
        Attempt to repair truncated or malformed JSON.

        Common issues:
        - Truncated response (missing closing brackets)
        - Trailing commas before closing brackets
        - Incomplete strings
        """
        repaired = json_str.strip()

        # Remove trailing incomplete elements
        # Find last complete element (ends with }, ], ", number, true, false, null)
        while repaired and repaired[-1] not in '"}]0123456789elnsu':
            repaired = repaired[:-1].strip()

        # Remove trailing commas
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)

        # Count brackets to see what's missing
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")

        # If we have unclosed structures, try to close them
        if open_braces > 0 or open_brackets > 0:
            # Remove any trailing incomplete key-value pair
            # e.g., '"key": ' or '"key": "incomplete
            repaired = re.sub(r',?\s*"[^"]*":\s*"?[^"}\]]*$', "", repaired)
            repaired = re.sub(r',?\s*"[^"]*":\s*$', "", repaired)

            # Remove trailing comma again
            repaired = re.sub(r",(\s*)$", r"\1", repaired)

            # Recount after cleanup
            open_braces = repaired.count("{") - repaired.count("}")
            open_brackets = repaired.count("[") - repaired.count("]")

            # Close arrays first, then objects
            repaired += "]" * open_brackets
            repaired += "}" * open_braces

        logger.debug(f"JSON repair: added {open_brackets} ] and {open_braces} }}")

        return repaired

    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(GEMINI_API_KEY)


# Singleton instance for convenience
gemini_client = GeminiClient()
