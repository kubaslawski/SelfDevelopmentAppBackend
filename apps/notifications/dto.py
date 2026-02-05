"""
DTOs for Notifications app.
"""

from pydantic import BaseModel, Field


class LLMQuoteDTO(BaseModel):
    """Quote item returned by the LLM."""

    text: str
    focus_goal: str | None = None
    focus_task: str | None = None


class LLMQuotesResponseDTO(BaseModel):
    """LLM response wrapper for motivational quotes."""

    quotes: list[LLMQuoteDTO] = Field(default_factory=list)
