"""
Pydantic DTOs for transport/validation between layers.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class GeneratedQuestionDTO(BaseModel):
    id: str
    question: str
    type: str = Field(default="text", pattern="^(text|choice|number)$")
    placeholder: str = ""
    options: List[str] = Field(default_factory=list)


class QuestionAnswerDTO(BaseModel):
    question_id: str
    question: str
    answer: str


class GeneratedTaskDTO(BaseModel):
    title: str
    description: str
    estimated_duration: str
    priority: str = Field(pattern="^(high|medium|low)$")
    is_recurring: bool = False
    recurrence_period: Optional[str] = None
    category: str = Field(
        default="learning", pattern="^(preparation|learning|practice|review|achievement)$"
    )


class GeneratedMilestoneDTO(BaseModel):
    title: str
    description: str
    target_date: date
    tasks: List[GeneratedTaskDTO]
    requirements: str = ""
    success_criteria: str = ""


class GeneratedPlanDTO(BaseModel):
    summary: str
    milestones: List[GeneratedMilestoneDTO]
    tips: List[str] = Field(default_factory=list)
    potential_obstacles: List[str] = Field(default_factory=list)
    motivation: str = ""
    final_achievement: str = ""
    icon: str = ""


class GeneratedQuestionsResponseDTO(BaseModel):
    questions: List[GeneratedQuestionDTO]


# =============================================================================
# Request DTOs (for API endpoints)
# =============================================================================


class TaskInputDTO(BaseModel):
    """Task data from LLM or user override."""

    title: str
    description: str = ""
    estimated_duration: str = "1 hour"
    priority: str = "medium"
    is_recurring: bool = False
    recurrence_period: Optional[str] = None
    category: str = "learning"


class MilestoneInputDTO(BaseModel):
    """Milestone data from LLM or user override."""

    title: str
    description: str = ""
    target_date: Optional[str] = None  # String from JSON, parsed later
    requirements: str = ""
    success_criteria: str = ""
    tasks: List[TaskInputDTO] = Field(default_factory=list)


class ApplyPlanRequestDTO(BaseModel):
    """Request body for apply_plan endpoint."""

    milestones: Optional[List[MilestoneInputDTO]] = None  # Override LLM milestones


class GenerateQuestionsRequestDTO(BaseModel):
    """Request body for generate_questions endpoint."""

    force: bool = False  # Force regeneration even if questions exist


class LLMGeneratedPlanDTO(BaseModel):
    """Structure of llm_generated_plan stored in Goal model."""

    summary: str = ""
    milestones: List[MilestoneInputDTO] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)
    potential_obstacles: List[str] = Field(default_factory=list)
    motivation: str = ""
    final_achievement: str = ""
