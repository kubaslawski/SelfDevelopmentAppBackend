"""
Rate limiting for LLM API calls.

Uses Django's cache backend to track request counts per user.
"""

from datetime import datetime, timedelta
from django.core.cache import cache

from .config import LLM_RATE_LIMIT_REQUESTS_PER_DAY, LLM_RATE_LIMIT_REQUESTS_PER_HOUR
from .exceptions import RateLimitExceeded


def _get_cache_key(user_id: int, period: str) -> str:
    """Generate cache key for rate limiting."""
    return f"llm_rate_limit:{user_id}:{period}"


def _get_hourly_key(user_id: int) -> str:
    """Get cache key for hourly rate limit."""
    hour = datetime.now().strftime("%Y%m%d%H")
    return _get_cache_key(user_id, f"hour:{hour}")


def _get_daily_key(user_id: int) -> str:
    """Get cache key for daily rate limit."""
    day = datetime.now().strftime("%Y%m%d")
    return _get_cache_key(user_id, f"day:{day}")


def check_rate_limit(user_id: int) -> None:
    """
    Check if user has exceeded rate limits.

    Args:
        user_id: The ID of the user making the request.

    Raises:
        RateLimitExceeded: If user has exceeded their rate limit.
    """
    # Check hourly limit
    hourly_key = _get_hourly_key(user_id)
    hourly_count = cache.get(hourly_key, 0)

    if hourly_count >= LLM_RATE_LIMIT_REQUESTS_PER_HOUR:
        # Calculate seconds until next hour
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        retry_after = int((next_hour - now).total_seconds())
        raise RateLimitExceeded(
            f"Hourly rate limit exceeded ({LLM_RATE_LIMIT_REQUESTS_PER_HOUR} requests/hour)",
            retry_after=retry_after,
        )

    # Check daily limit
    daily_key = _get_daily_key(user_id)
    daily_count = cache.get(daily_key, 0)

    if daily_count >= LLM_RATE_LIMIT_REQUESTS_PER_DAY:
        # Calculate seconds until midnight
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        retry_after = int((midnight - now).total_seconds())
        raise RateLimitExceeded(
            f"Daily rate limit exceeded ({LLM_RATE_LIMIT_REQUESTS_PER_DAY} requests/day)",
            retry_after=retry_after,
        )


def increment_rate_limit(user_id: int) -> None:
    """
    Increment the rate limit counters for a user.

    Should be called after a successful LLM request.

    Args:
        user_id: The ID of the user who made the request.
    """
    # Increment hourly counter (expires in 1 hour)
    hourly_key = _get_hourly_key(user_id)
    try:
        cache.incr(hourly_key)
    except ValueError:
        # Key doesn't exist, create it
        cache.set(hourly_key, 1, timeout=3600)  # 1 hour

    # Increment daily counter (expires in 24 hours)
    daily_key = _get_daily_key(user_id)
    try:
        cache.incr(daily_key)
    except ValueError:
        # Key doesn't exist, create it
        cache.set(daily_key, 1, timeout=86400)  # 24 hours


def get_remaining_requests(user_id: int) -> dict:
    """
    Get the remaining requests for a user.

    Args:
        user_id: The ID of the user.

    Returns:
        Dictionary with remaining hourly and daily requests.
    """
    hourly_key = _get_hourly_key(user_id)
    daily_key = _get_daily_key(user_id)

    hourly_used = cache.get(hourly_key, 0)
    daily_used = cache.get(daily_key, 0)

    return {
        "hourly": {
            "used": hourly_used,
            "limit": LLM_RATE_LIMIT_REQUESTS_PER_HOUR,
            "remaining": max(0, LLM_RATE_LIMIT_REQUESTS_PER_HOUR - hourly_used),
        },
        "daily": {
            "used": daily_used,
            "limit": LLM_RATE_LIMIT_REQUESTS_PER_DAY,
            "remaining": max(0, LLM_RATE_LIMIT_REQUESTS_PER_DAY - daily_used),
        },
    }

