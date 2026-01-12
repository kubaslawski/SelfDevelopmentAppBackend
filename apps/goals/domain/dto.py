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


class GeneratedMilestoneDTO(BaseModel):
    title: str
    description: str
    target_date: date
    tasks: List[GeneratedTaskDTO]


class GeneratedPlanDTO(BaseModel):
    summary: str
    milestones: List[GeneratedMilestoneDTO]
    tips: List[str] = Field(default_factory=list)
    potential_obstacles: List[str] = Field(default_factory=list)
    motivation: str = ""


class GeneratedQuestionsResponseDTO(BaseModel):
    questions: List[GeneratedQuestionDTO]
