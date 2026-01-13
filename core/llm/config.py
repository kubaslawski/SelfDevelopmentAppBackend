"""
LLM configuration settings.
"""

from decouple import config

# Gemini API Configuration
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-2.5-flash")

# Rate limiting settings (per user)
LLM_RATE_LIMIT_REQUESTS_PER_DAY = config("LLM_RATE_LIMIT_REQUESTS_PER_DAY", default=50, cast=int)
LLM_RATE_LIMIT_REQUESTS_PER_HOUR = config("LLM_RATE_LIMIT_REQUESTS_PER_HOUR", default=10, cast=int)

# Generation settings
LLM_MAX_OUTPUT_TOKENS = config("LLM_MAX_OUTPUT_TOKENS", default=32768, cast=int)
LLM_TEMPERATURE = config("LLM_TEMPERATURE", default=0.7, cast=float)

# Timeout settings (in seconds)
LLM_REQUEST_TIMEOUT = config("LLM_REQUEST_TIMEOUT", default=180, cast=int)
