"""
Domain entities for Notifications.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MotivationalQuote:
    """Motivational quote tailored to user's goals and tasks."""

    text: str
    focus_goal: Optional[str] = None
    focus_task: Optional[str] = None

