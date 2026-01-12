"""
Domain services for Goals.

Responsible for orchestrating LLM calls and mapping to/from entities/DTOs.
"""

import logging
from typing import List

from django.utils import timezone

from core.llm import gemini_client, LLMError, RateLimitExceeded
from core.llm.prompts import (
    format_generate_questions_prompt,
    format_goal_plan_prompt,
    GOAL_PLANNER_SYSTEM,
    QUESTION_GENERATOR_SYSTEM,
    FALLBACK_QUESTIONS,
)

from .domain.entities import (
    GeneratedQuestion,
    QuestionAnswer,
    GeneratedPlan,
    GeneratedMilestone,
    GeneratedTask,
)
from .domain.dto import (
    GeneratedPlanDTO,
    GeneratedQuestionsResponseDTO,
)
from .models import Goal

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Question Generation
# -----------------------------------------------------------------------------

def generate_questions(goal: Goal, user_id: int) -> List[GeneratedQuestion]:
    """
    Generate contextual questions for a goal using the LLM.
    Returns a list of GeneratedQuestion entities.
    Falls back to static questions on error/rate-limit.
    """
    prompt = format_generate_questions_prompt(
        goal_description=f"{goal.title}. {goal.description}" if goal.description else goal.title
    )

    try:
        result = gemini_client.generate_json(
            prompt=prompt,
            system_prompt=QUESTION_GENERATOR_SYSTEM,
            user_id=user_id,
        )
        dto = GeneratedQuestionsResponseDTO.model_validate(result)
        return [
            GeneratedQuestion(
                id=q.id,
                question=q.question,
                type=q.type,
                placeholder=q.placeholder or "",
                options=q.options or [],
            )
            for q in dto.questions
        ]
    except RateLimitExceeded as e:
        logger.warning("Rate limit for user %s, using fallback questions", user_id)
        return _fallback_questions()
    except LLMError as e:
        logger.error("LLM error generating questions for goal %s: %s", goal.id, e)
        return _fallback_questions()
    except Exception as e:
        logger.exception("Unexpected error generating questions: %s", e)
        return _fallback_questions()


def _fallback_questions() -> List[GeneratedQuestion]:
    """Convert fallback dicts to entities."""
    return [
        GeneratedQuestion(
            id=q.get("id", f"q{idx+1}"),
            question=q.get("question", ""),
            type=q.get("type", "text"),
            placeholder=q.get("placeholder", ""),
            options=q.get("options", []) if q.get("type") == "choice" else [],
        )
        for idx, q in enumerate(FALLBACK_QUESTIONS)
    ]


# -----------------------------------------------------------------------------
# Plan Generation
# -----------------------------------------------------------------------------

def generate_plan(goal: Goal, answers: List[QuestionAnswer], user_id: int) -> GeneratedPlan:
    """
    Generate a plan (milestones + tasks) using LLM based on answers.
    Returns a GeneratedPlan entity.
    """
    prompt = format_goal_plan_prompt(
        goal_title=goal.title,
        goal_description=goal.description,
        answers=[{"question": a.question, "answer": a.answer} for a in answers],
        target_date=goal.target_date.isoformat(),
    )

    result = gemini_client.generate_json(
        prompt=prompt,
        system_prompt=GOAL_PLANNER_SYSTEM,
        user_id=user_id,
    )

    dto = GeneratedPlanDTO.model_validate(result)

    milestones = []
    for ms in dto.milestones:
        milestones.append(
            GeneratedMilestone(
                title=ms.title,
                description=ms.description,
                target_date=ms.target_date,
                tasks=[
                    GeneratedTask(
                        title=t.title,
                        description=t.description,
                        estimated_duration=t.estimated_duration,
                        priority=t.priority,
                        is_recurring=t.is_recurring,
                        recurrence_period=t.recurrence_period,
                    )
                    for t in ms.tasks
                ],
            )
        )

    return GeneratedPlan(
        summary=dto.summary,
        milestones=milestones,
        tips=dto.tips,
        potential_obstacles=dto.potential_obstacles,
        motivation=dto.motivation,
    )


# -----------------------------------------------------------------------------
# Persistence helpers
# -----------------------------------------------------------------------------

def save_questions(goal: Goal, questions: List[GeneratedQuestion]) -> None:
    """Persist generated questions onto the Goal."""
    goal.planning_questions = [
        {
            "id": q.id,
            "question": q.question,
            "type": q.type,
            "placeholder": q.placeholder,
            "options": q.options,
        }
        for q in questions
    ]
    goal.save(update_fields=["planning_questions", "updated_at"])


def save_plan(goal: Goal, plan: GeneratedPlan) -> None:
    """Persist generated plan onto the Goal."""
    goal.llm_generated_plan = {
        "summary": plan.summary,
        "milestones": [
            {
                "title": m.title,
                "description": m.description,
                "target_date": m.target_date.isoformat(),
                "tasks": [
                    {
                        "title": t.title,
                        "description": t.description,
                        "estimated_duration": t.estimated_duration,
                        "priority": t.priority,
                        "is_recurring": t.is_recurring,
                        "recurrence_period": t.recurrence_period,
                    }
                    for t in m.tasks
                ],
            }
            for m in plan.milestones
        ],
        "tips": plan.tips,
        "potential_obstacles": plan.potential_obstacles,
        "motivation": plan.motivation,
    }
    goal.plan_generated_at = timezone.now()
    goal.motivation = plan.motivation
    goal.potential_obstacles = plan.potential_obstacles
    goal.tips = plan.tips
    goal.status = Goal.Status.DRAFT
    goal.save()

